"""
bot_worker.py — BotWorker: chạy các nhiệm vụ của một thiết bị trên QThread riêng, tới khi Stop.

Danh sách nhiệm vụ: lúc Start lấy mọi nhiệm vụ đã tích (tasks.build_tasks), xếp theo độ ưu tiên (priority.py). Mỗi vòng lặp:
1. đọc DB, bỏ qua nhiệm vụ đã xong hôm nay (xong = dấu lưu sau mốc reset server gần nhất);
2. việc theo giờ (đập trứng, Alliance Donation / Help): làm xong thì lưu giờ vào DB; mỗi vòng chỉ so giờ đó, tới giờ thì làm ngay;
3. không có việc theo giờ nào tới giờ thì lấy nhiệm vụ đầu danh sách làm; chưa xong thì chuyển xuống cuối, rồi làm việc khác.
Sang ngày mới (qua mốc reset server) thì tắt game bật lại (giữa hai nhiệm vụ), dấu "xong" của hôm qua hết hiệu lực nên nhiệm vụ
tự quay lại (trừ nhiệm vụ `once` đã xong).

Thứ tự ưu tiên: Bubble > Auto Times Out > Join Boss > nhiệm vụ.
- Bubble: lo trước mọi lần chạy (guards.py); tới hạn thì ngắt mọi thứ đang chạy (BubbleDue).
- Auto Times Out (số phút chọn ở màn Home, chung mọi thiết bị): lo ngay sau bubble; chạy đủ số phút kể từ
  lần đóng game trước thì ngắt mọi thứ đang chạy (RestartDue) và đóng game; nhiệm vụ đang dở làm lại.
- Có chọn Join Boss: mỗi vòng chạy Join Boss (rảnh thì nhường), rồi 1 nhiệm vụ tối đa OTHERS_WINDOW
  giây; xong nhiệm vụ là quay lại Join Boss ngay. Hết giờ / có boss mới -> nhiệm vụ đang dở giữ nguyên vị trí, sau Join Boss làm tiếp.
  Join Boss dừng hẳn (không phải rảnh) -> vẫn chạy tiếp các nhiệm vụ.
- Nhiệm vụ must_finish (priority.py): đã bắt đầu thì chạy tới xong; Bubble / Auto Times Out / boss mới /
  120 giây không ngắt (chỉ Stop). Xong rồi mới tới Bubble, Auto Times Out và Join Boss.
- Nhiệm vụ idle_only (priority.py, VD Find Boss): chỉ chạy khi RẢNH, tức không còn nhiệm vụ nào khác tới lượt (kể cả việc theo giờ chưa
  tới giờ); việc theo giờ (due) thì tới giờ mới làm, không có due thì làm liên tục; không bị giới hạn 120 giây và boss mới không ngắt nó: sau mỗi cú kéo kiểm tra số boss (arc_sweep.WATCH_EVERY), tăng thì vào Join Boss tới khi rảnh rồi kéo tiếp; bị ngắt bởi Bubble / Auto Times Out / reset server và khi có nhiệm vụ khác tới lượt (việc theo giờ tới giờ, City VIP
  lúc 0h...: YieldToTask, xét mỗi 5 giây), xong việc đó rảnh lại thì quét lại.
- Không chọn Join Boss: không có giới hạn 120 giây, các nhiệm vụ chạy lần lượt tới khi xong.
- Activity chạy một mình (activities.EXCLUSIVE_ACTIVITIES, VD Recruit General): chỉ chạy hàm của nó, KHÔNG liên quan Bubble
  (kể cả đã tích), Auto Times Out, reset server, Join Boss hay nhiệm vụ nào khác (_run_exclusive).
- Không tích Bubble: không có luật Bubble (không lo bubble, không bị ngắt vì bubble).
- Một nhiệm vụ chạy hết một lượt mà vẫn chưa xong tối đa MAX_ATTEMPTS (6) lần mỗi ngày; quá thì bỏ qua tới ngày mới
  (bị ngắt giữa chừng không tính là một lần thử).
- Danh sách rỗng hoặc cả danh sách đều chưa xong: nghỉ ngắn (IDLE_WAIT) rồi xét lại (thread vẫn sống).
- Chỉ chọn mỗi Join Boss: chạy Join Boss liên tục như trước.
- Hết nhiệm vụ (kể cả việc theo giờ chưa tới giờ) và Join Boss rảnh, máy chưa có bản đồ thành: quét 13 ô route công trình (city_map.scan_city),
  lưu DB; mỗi lượt Start thử một lần, boss mới ngắt giữa chừng thì lần rảnh sau quét lại.
"""
import json
import os
import sys
import threading
import time
import traceback
from datetime import datetime
from types import SimpleNamespace

from PyQt5.QtCore import QThread, pyqtSignal

from ..activities import ACTIVITIES, EXCLUSIVE_ACTIVITIES
from ..city.city_map import scan_city
from ..activities.join_monster_war import IDLE as BOSS_IDLE
from ..activities.join_monster_war import stamina_wait
from ..activities.join_monster_war.constants import LISTBOSS
from ..ocr.read_boss_count import crop as boss_count_crop, run as read_boss_count
from ..common import get_server, no_alliance
from ..daily_reset import done_today, last_reset
from ..context import BotContext, BotInterrupted, TimedOut
from ..context.errors import BossAvailable, StopRequested, YieldToBoss, YieldToTask
from .guards import Guards
from .server_clock import ServerClock
from .tasks import build_tasks, sink
from .status import STATUS_ERROR, STATUS_RUNNING, STATUS_STOPPED

JOIN_BOSS = "Join Monster War"
OTHERS_WINDOW = 120   # giây tối đa cho 1 nhiệm vụ khi có Join Boss (không có Join Boss: không giới hạn)
# Icon listboss: ảnh mẫu cắt phần giữa avatar, bỏ viền vàng (viền vàng sáng lên khi có boss mới nên ảnh mẫu có viền sẽ khớp kém).
BOSS_ICON_REGION = (80, 20, 100, 90)   # % màn hình: cột icon bên phải
MAX_ATTEMPTS = 6       # số lần tối đa mỗi ngày một nhiệm vụ chạy hết một lượt mà vẫn chưa xong (quá thì bỏ qua tới ngày mới)
IDLE_RECHECK = 5       # giây: việc idle_only đang chạy xét lại xem có nhiệm vụ khác tới lượt chưa
IDLE_WAIT = 5         # giây nghỉ khi không còn nhiệm vụ nào tới lượt


def _print_safe(message: str):
    """Ghi console mà không bao giờ làm worker chết vì code page Windows.

    Khi chạy từ PowerShell/cmd cũ, stdout thường là CP1252 và không mã hóa được tiếng Việt.
    UI/History vẫn nhận nguyên văn Unicode; chỉ bản console mới thay ký tự không hỗ trợ.
    """
    stream = sys.stdout
    if stream is None:       # pythonw.exe không có console
        return
    encoding = getattr(stream, "encoding", None) or "utf-8"
    safe = message.encode(encoding, errors="replace").decode(encoding, errors="replace")
    try:
        print(safe, file=stream)
    except (OSError, ValueError):
        # Console đã đóng / stream không còn hợp lệ: log UI vẫn tiếp tục hoạt động.
        pass


def _describe_error(e: Exception, activity: str | None) -> str:
    """Dòng lịch sử cho lỗi làm bot dừng: activity đang chạy, loại lỗi, nội dung, file:dòng nơi lỗi."""
    frames = traceback.extract_tb(e.__traceback__)
    where = f" (tại {os.path.basename(frames[-1].filename)}:{frames[-1].lineno})" if frames else ""
    during = f" khi chạy {activity}" if activity else ""
    return f"Lỗi{during}: {type(e).__name__}: {e}{where} -> bot dừng"


# Điều phối activity của một thiết bị trên QThread riêng.
class BotWorker(QThread):
    # Gửi serial kèm dữ liệu để UI cập nhật đúng thiết bị.
    activity_changed = pyqtSignal(str, str)   # (serial, activity)
    status_changed = pyqtSignal(str, str)     # (serial, status)
    server_found = pyqtSignal(str, str)       # (serial, server)

    daily_task_done = pyqtSignal(str, str)    # (serial, task Daily Activities vừa xong)
    daily_task_cleared = pyqtSignal(str, str) # (serial, khoá daily_done cần xoá khỏi DB)
    bubble_found = pyqtSignal(str, int)       # (serial, giây bubble còn lại; 0 = không có)
    civilization_found = pyqtSignal(str, int) # (serial, nền văn minh bot tự xếp từ ảnh công trình)
    city_map_found = pyqtSignal(str, str)     # (serial, bản đồ thành JSON bot quét được)
    bubble_disabled = pyqtSignal(str)         # (serial) không đủ kim cương -> bỏ tích Bubble
    log_message = pyqtSignal(str, str)        # (serial, dòng log) -> tab Logs > Info
    history = pyqtSignal(str, str)            # (serial, sự kiện) -> lưu DB + tab Logs > History

    def __init__(self, serial: str, activities: list[str], settings: dict, parent=None, *,
                 boss_board=None, daily_done: dict | None = None, server_clock: ServerClock | None = None,
                 auto_timeout=None):
        super().__init__(parent)
        # Lưu thiết bị và sao chép danh sách activity cho lượt chạy.
        self.serial = serial
        self.boss_board = boss_board
        self.activities = list(activities)
        # Nhận cấu hình từ UI; ở đây giữ tham chiếu, không sao chép settings.
        self.settings = settings            # DeviceView.get_settings() snapshot
        # Dùng server đã cấu hình; nếu thiếu sẽ thử đọc trong game.
        self.server = settings.get("Initialization", {}).get("server") or ""
        # Cờ Stop dùng chung giữa UI và BotContext.
        self._stop = threading.Event()
        self._current = None   # activity đang chạy, để ghi vào lịch sử khi có lỗi
        # Giờ reset server chọn ở màn Home, dùng chung mọi thiết bị (BotManager giữ; thiếu thì dùng riêng).
        self.server_clock = server_clock if server_clock is not None else ServerClock()
        # {task: done_at} lấy từ DB; task chỉ tính là xong nếu done_at sau mốc reset gần nhất.
        self.daily_done = dict(daily_done or {})
        self._boss_count = None   # số boss lần đọc trước khi tìm route (OCR huy hiệu listboss); None = chưa đọc
        # Bubble + Auto Times Out (guards.py): ưu tiên hơn mọi nhiệm vụ. Auto Times Out: hàm trả số phút chọn ở màn Home
        # (đọc lại mỗi lần, đổi là dùng ngay; 0 = tắt).
        self.guards = Guards(
            lambda: self.ctx, settings.get("Initialization", {}), auto_timeout or (lambda: 0),
            SimpleNamespace(
                found=lambda seconds: self.bubble_found.emit(self.serial, seconds),
                disabled=self._on_bubble_disabled,
                activity=lambda label: self.activity_changed.emit(self.serial, label),
                log=self.log, record=self.record),
            server_time=lambda: self.server_time)

    def stop(self):
        # Chỉ yêu cầu dừng; activity phải kiểm tra cờ, không cưỡng chế tắt thread.
        self._stop.set()

    def run(self):
        # Điểm vào khi worker.start(): báo UI đang chạy.
        self.status_changed.emit(self.serial, STATUS_RUNNING)
        self.record(f"Bắt đầu chạy bot: {', '.join(self.activities)}")
        # Hoàn thành bình thường hoặc Stop đều có trạng thái cuối là Stopped.
        status = STATUS_STOPPED
        try:
            import adbutils

            # Lấy thiết bị ADB theo serial và tạo context thao tác với game.
            device = adbutils.adb.device(serial=self.serial)
            # Truyền cờ Stop, deadline None (không giới hạn) và hàm log.
            self.ctx = BotContext(device, self._stop, None, self.log)
            self.ctx.settings = self.settings
            self.ctx.report_boss = self._report_boss
            self.ctx.is_daily_done = self._is_daily_done
            self.ctx.mark_daily_done = self._mark_daily_done
            self.ctx.done_at = self.daily_done.get
            self.ctx.forget_daily = self._forget_daily
            self.ctx.daily_keys = lambda: list(self.daily_done)
            self.ctx.server_time = lambda: self.server_time
            self.ctx.server = self.server
            self.ctx.record = self.record
            # Nền văn minh đã lưu DB (None = chưa biết); bot tự xếp thì lưu lại qua signal.
            self.ctx.civilization = self.settings.get("Initialization", {}).get("civilization") or None
            self.ctx.set_civilization = self._set_civilization
            # Bản đồ thành đã lưu DB ({công trình: [x, y]}, {} = chưa quét); bot quét xong thì lưu lại qua signal.
            self.ctx.city_map = dict(self.settings.get("Initialization", {}).get("city_map") or {})
            self.ctx.set_city_map = self._set_city_map
            self._register_boss_listener()
            if EXCLUSIVE_ACTIVITIES.intersection(self.activities):
                self._run_exclusive()
            else:
                self._run_tasks()
        # Ngắt có chủ đích (Stop/timeout truyền tới đây) không xem là lỗi.
        except BotInterrupted:
            pass
        # Lỗi ngoài dự kiến: dừng lượt chạy và báo nội dung lỗi.
        except Exception as e:
            status = f"{STATUS_ERROR}: {e}"
            self.log(traceback.format_exc().rstrip())
            self.record(_describe_error(e, self._current))
        # Luôn xóa activity đang hiển thị và báo trạng thái cuối, kể cả khi lỗi.
        finally:
            if self.boss_board is not None:
                self.boss_board.unregister(self.serial)
            if status == STATUS_STOPPED:
                self.record("Bot đã dừng")
            self.activity_changed.emit(self.serial, "None")
            self.status_changed.emit(self.serial, status)

    def _run_once(self, activities: list[str]):
        """Chạy tuần tự mỗi activity 1 lần (chỉ còn dùng cho trường hợp chỉ chọn mỗi Join Boss)."""
        for activity in activities:
            if self._stop.is_set():
                break
            # Server chỉ cần cho cơ chế chia sẻ boss. Daily và activity khác
            # không được mở Settings chỉ để dò server trước khi bắt đầu.
            if activity == JOIN_BOSS:
                self._ensure_server()
            self.activity_changed.emit(self.serial, activity)
            self._run_activity(activity, self.settings.get(activity, {}))

    def _run_exclusive(self):
        """Activity chạy một mình: gọi thẳng hàm run, không qua guards (Bubble, Auto Times Out, reset server) và không
        có Join Boss / nhiệm vụ khác. Chạy một lượt rồi dừng; hàm run tự lặp nếu cần."""
        for activity in self.activities:
            if self._stop.is_set():
                break
            if activity not in EXCLUSIVE_ACTIVITIES:
                continue
            run = ACTIVITIES.get(activity)
            if run is None:
                self.log(f"Unknown activity: {activity}")
                continue
            self._current = activity
            self.activity_changed.emit(self.serial, activity)
            run(self.ctx, self.settings.get(activity, {}))

    def _run_tasks(self):
        """Vòng lặp chính (xem docstring đầu file) cho tới khi Stop."""
        boss = JOIN_BOSS in self.activities
        tasks = build_tasks(self.activities, {JOIN_BOSS}, self.settings)   # đã xếp theo độ ưu tiên
        if boss and not tasks:
            self._run_once([JOIN_BOSS])   # chỉ Join Boss: chạy liên tục như trước
            return
        idle = [task for task in tasks if task.idle_only]          # chỉ làm khi rảnh (hết mọi nhiệm vụ khác), vd Find Boss
        tasks = [task for task in tasks if not task.idle_only]
        timed = [task for task in tasks if task.due is not None]   # việc theo giờ: giờ lần làm trước lưu trong DB
        order = [task for task in tasks if task.due is None]       # thứ tự làm: chưa xong thì chuyển xuống cuối
        reset = last_reset(self.server_time)
        self.guards.reset_handled = reset   # vừa Start thì không đóng game; chỉ đóng khi qua một mốc reset mới
        ran = set()        # nhiệm vụ không có dấu xong trong DB: đã chạy hết một lượt kể từ lần reset gần nhất
        ran_once = set()   # nhiệm vụ `once` đã chạy xong: không làm lại khi sang ngày mới (chỉ khi Start lại)
        attempts = {}      # key -> số lần chạy hết một lượt mà vẫn chưa xong hôm nay (tối đa MAX_ATTEMPTS)
        stalled = 0        # số nhiệm vụ liên tiếp chạy xong một lượt mà vẫn chưa xong
        scan_tried = False  # đã thử quét bản đồ thành trong lượt Start này (rảnh mới quét, xem nhánh `not pending` bên dưới)
        while not self._stop.is_set():
            # Hết thể lực: Join Boss lưu mốc "+20 phút" vào DB; chưa tới mốc thì làm nhiệm vụ (không gọi Join Boss, boss mới cũng
            # không ngắt), qua mốc thì Join Boss lại.
            stamina_wait_on = boss and stamina_wait.waiting(self.ctx.daily_keys())
            if boss and not stamina_wait_on:
                self._ensure_server()
                boss = self._check_boss()
            now_reset = last_reset(self.server_time)
            if now_reset > reset:   # sang ngày mới: các dấu "đã chạy" và số lần thử của hôm qua hết hiệu lực
                reset = now_reset
                ran.clear()
                attempts.clear()
                # Tới mốc reset server: tắt game bật lại. Thường đã làm đúng giờ bởi ResetDue (guards.py, kể cả khi đang chạy
                # nhiệm vụ); ở đây chỉ làm nếu chưa (restart_for_reset bỏ qua mốc đã xử lý). Game tự mở lại ở nhiệm vụ kế tiếp
                # (go_home).
                self.guards.restart_for_reset(now_reset)
            # Mỗi vòng đọc lại trạng thái từ DB và bỏ qua nhiệm vụ đã xong hôm nay (đổi mục tiêu ở tab, sang ngày mới... thì
            # nhiệm vụ tự quay lại, không cần dựng lại danh sách).
            # Nhiệm vụ cần route (needs_city_map) chờ tới khi máy có bản đồ thành (quét lúc rảnh, bên dưới); đã thử quét mà
            # không được thì thôi chờ, nhiệm vụ tự xoay xở.
            waiting = lambda t: t.needs_city_map and not self.ctx.city_map and not scan_tried
            skip = lambda t: ((t.once and t.key in ran_once) or attempts.get(t.key, 0) >= MAX_ATTEMPTS
                              or (t.needs_alliance and no_alliance.known(self.ctx))
                              or waiting(t) or self._is_done(t, ran))
            # Việc theo giờ: chỉ cần so giờ đã lưu trong DB; tới giờ thì làm ngay, trước các việc trong danh sách.
            task = next((t for t in timed if not skip(t) and self._is_due(t)), None)
            pending = [t for t in order if not skip(t)]
            if task is None:
                if not pending:
                    # Không còn nhiệm vụ nào (kể cả việc theo giờ chưa tới giờ) và Join Boss vừa báo rảnh: chưa có bản đồ thành
                    # thì tìm route các công trình (city_map.scan_city: tìm Thành chính trước rồi quét từng ô, lưu DB); cứ 3 cú
                    # vuốt kiểm tra số boss, tăng thì vào Join Boss tới khi rảnh rồi vuốt tiếp. Mỗi lượt Start thử một lần.
                    need_map = any(waiting(t) for t in order)
                    if (boss or need_map) and not self.ctx.city_map and not scan_tried:
                        scan_tried = True
                        self.record("Rảnh (hết nhiệm vụ, Join Boss rảnh): tìm route các công trình")
                        self.activity_changed.emit(self.serial, JOIN_BOSS)
                        self._boss_count = None
                        self.guards.call(None, scan_city, self.ctx, "City scan",
                                         self._watch_boss_count if boss and not stamina_wait_on else None)
                        continue
                    # Rảnh hẳn: làm việc `idle_only` đã tới giờ (không bao giờ chen vào lúc còn nhiệm vụ khác).
                    idle_task = next((t for t in idle if t.key not in ran_once and not skip(t) and (t.due is None or self._is_due(t))), None)
                    if idle_task is not None:
                        last_look = [0.0]

                        def others_waiting():   # nhiệm vụ khác (việc theo giờ tới giờ, City VIP 0h, ...) tới lượt: nhường; xét tối đa 5 giây một lần
                            if time.monotonic() - last_look[0] < IDLE_RECHECK:
                                return False
                            last_look[0] = time.monotonic()
                            return any(not skip(t) for t in order) or any(not skip(t) and self._is_due(t) for t in timed)

                        self._run_task(idle_task, boss and not stamina_wait_on, others_waiting)
                        continue
                    self.guards.call(None, self.ctx.sleep, IDLE_WAIT)
                    continue
                task = pending[0]
            completed = self._run_task(task, boss and not stamina_wait_on)   # False: bị ngắt giữa chừng (không tính là một lần thử)
            if completed and task.done is None:
                ran.add(task.key)
                if task.once:
                    ran_once.add(task.key)
            if self._is_done(task, ran):
                stalled = 0
                continue
            if completed and task.due is None:   # việc theo giờ đã bị giãn bởi số giờ trên tab: không giới hạn số lần thử
                attempts[task.key] = attempts.get(task.key, 0) + 1
                if attempts[task.key] >= MAX_ATTEMPTS:
                    self.record(f"{task.key}: chưa xong sau {MAX_ATTEMPTS} lần thử, bỏ qua tới ngày mới")
                    continue
            if not completed:
                continue   # bị ngắt (boss / hết 120 giây): sau Join Boss làm tiếp chính nhiệm vụ này, không đổi sang việc khác
            if task.due is None:
                sink(order, task)   # chưa xong: xuống cuối chuỗi cùng nhóm, trên nhiệm vụ nhận thưởng (việc theo giờ thì chờ tới giờ kế tiếp)
                stalled += 1
                if stalled >= len(pending):   # cả danh sách đều chưa xong: nghỉ chút rồi mới vòng lại
                    stalled = 0
                    self.guards.call(None, self.ctx.sleep, IDLE_WAIT)

    def _read_boss_count(self) -> int | None:
        """Số boss đang chờ trên màn thành: 0 nếu không thấy icon listboss, None nếu thấy mà không đọc được số."""
        screen = self.ctx.screenshot()
        icon = self.ctx.find(LISTBOSS, screen=screen, center=False, region=BOSS_ICON_REGION)
        if icon is None:
            return 0
        return read_boss_count(boss_count_crop(screen, icon))

    def _watch_boss_count(self, bot) -> bool:
        """Gọi lúc scan_city bắt đầu và cứ 3 cú vuốt: so số boss (OCR huy hiệu icon listboss) với lần đọc trước. Bằng thì vuốt
        tiếp; giảm thì ghi đè số cũ; tăng thì có boss mới: vào Join Boss tới khi rảnh (Join Boss dừng hẳn thì thôi theo dõi),
        rồi đọc lại số làm mốc và vuốt tiếp."""
        count = self._read_boss_count()
        if count is None:
            return False
        previous = self._boss_count
        if previous is None or count <= previous:
            self._boss_count = count
            return False
        self.record(f"Tìm route: số boss tăng {previous} -> {count}, vào Join Boss")
        self.activity_changed.emit(self.serial, JOIN_BOSS)
        self._ensure_server()
        self._check_boss()      # chạy Join Boss tới khi rảnh (hoặc dừng hẳn: thôi, vuốt tiếp)
        again = self._read_boss_count()
        self._boss_count = again if again is not None else count
        self.record("Join Boss rảnh, tiếp tục tìm route")
        return True          # đã rời màn đang quét (scan_city bỏ qua; quét thế giới thì về gốc kéo lại)

    def _is_done(self, task, ran) -> bool:
        """Nhiệm vụ đã xong hôm nay: theo dấu trong DB (`done`), hoặc (không có dấu) đã chạy hết một lượt."""
        if task.done is None:
            return task.key in ran
        return bool(task.done(self.ctx, self.settings.get(task.group, {})))

    def _is_due(self, task) -> bool:
        """Việc theo giờ đã tới giờ làm (so với giờ lần làm trước lưu trong DB)."""
        return bool(task.due(self.ctx, self.settings.get(task.group, {})))

    def _check_boss(self) -> bool:
        """Một lượt Join Boss, rảnh thì nhường (exit_when_idle). False nếu Join Boss dừng hẳn."""
        self.activity_changed.emit(self.serial, JOIN_BOSS)
        self.ctx._boss_event.clear()
        # Cấu hình tạm: boss trả về IDLE khi rảnh để nhường nhiệm vụ; không sửa settings gốc.
        result = self._run_activity(JOIN_BOSS, {**self.settings.get(JOIN_BOSS, {}), "exit_when_idle": True})
        if result == BOSS_IDLE:
            return True
        self.record("Join Monster War dừng; chạy tiếp các nhiệm vụ khác")
        return False

    def _run_task(self, task, boss: bool, idle_abort=None) -> bool:
        """Chạy 1 nhiệm vụ. Có Join Boss: tối đa OTHERS_WINDOW giây, boss mới cũng ngắt; không có Join
        Boss: không giới hạn thời gian. must_finish: không bị Bubble / boss / thời gian ngắt (chỉ Stop).
        Việc idle_only: `idle_abort` = có nhiệm vụ khác tới lượt thì ngắt; có Join Boss thì sau mỗi cú kéo kiểm tra số boss (arc_sweep.WATCH_EVERY) (vào Join Boss rồi
        kéo tiếp, không bị boss mới ngắt cả việc).
        True nếu chạy hết một lượt, False nếu bị ngắt (chưa xong: chuyển xuống cuối danh sách)."""
        if boss and not task.must_finish:
            # Timeout chỉ phát hiện khi BotContext kiểm tra; không ngắt cưỡng chế. Việc `idle_only` (quét dài) không giới hạn 120 giây, chỉ boss mới ngắt.
            if not task.idle_only:
                self.ctx._deadline = time.monotonic() + OTHERS_WINDOW
            self.ctx._boss_interrupt_enabled = not task.idle_only
        self.ctx._idle_abort = idle_abort
        if task.idle_only and boss:
            self._boss_count = None
            self.ctx.swipe_count = 0

            def watch(bot):          # vào Join Boss giữa chừng thì không để "có nhiệm vụ khác tới lượt" ngắt Join Boss
                aborting, self.ctx._idle_abort = self.ctx._idle_abort, None
                try:
                    return self._watch_boss_count(bot)
                finally:
                    self.ctx._idle_abort = aborting
            self.ctx.swipe_watch = watch   # chỉ việc idle_only: có nhiệm vụ khác tới lượt thì ngắt (YieldToTask)
        try:
            # Lo bubble trước (không có Join Boss thì không có bước nào khác lo), rồi xét Stop / boss mới.
            self.guards.call(None, self.ctx.check)
            if task.must_finish:
                # Bubble / Auto Times Out vừa lo xong -> hoãn tới khi nhiệm vụ xong.
                self.guards.hold()
            self.activity_changed.emit(self.serial, task.group)
            self.record(f"Bắt đầu: {task.key}")
            result = self._run_one(task)
            if result is False:
                self.record(f"Kết thúc lượt: {task.key} (còn PENDING; "
                            "chuyển nhiệm vụ kế tiếp)")
            elif (task.done is not None
                    and not task.done(self.ctx,
                                      self.settings.get(task.group, {}))):
                self.record(f"Kết thúc lượt: {task.key} (chưa DONE trong DB; "
                            "sẽ chạy lại)")
            else:
                self.record(f"Xong: {task.key}")
            return True
        # Bị ngắt: chưa xong, nhiệm vụ giữ vị trí và được gọi lại từ đầu hàm run() sau Join Boss; worker không lưu điểm thực thi.
        except TimedOut:
            self.record(f"Tạm dừng: {task.key} (hết {OTHERS_WINDOW} giây, quay lại Join Monster War)")
            return False    # hết OTHERS_WINDOW giây
        except BossAvailable:
            self.record(f"Tạm dừng: {task.key} (có boss mới, chuyển sang Join Monster War)")
            return False
        except YieldToTask:
            self.record(f"Tạm dừng: {task.key} (có nhiệm vụ khác tới lượt)")
            return False
        except YieldToBoss:
            self.record(f"Tạm dừng: {task.key} (nhường lượt cho Join Monster War)")
            return False
        except StopRequested:
            self.record(f"Dừng: {task.key} (người dùng bấm Stop)")
            raise
        # Luôn gỡ deadline, kể cả khi Stop/lỗi, để không ảnh hưởng lượt chạy boss.
        finally:
            self.guards.release()
            self.ctx._idle_abort = None
            self.ctx.swipe_watch = None
            self.ctx._boss_interrupt_enabled = False
            self.ctx._deadline = None

    @property
    def server_time(self) -> str:
        """Giờ reset server "HH:MM" người dùng chọn ở màn Home, dùng chung mọi thiết bị."""
        return self.server_clock.value

    def _ensure_server(self):
        """Chưa có server -> đọc server trong game rồi báo ra UI để lưu lại."""
        # Đã biết server thì không đọc lại.
        if self.server:
            return
        self.activity_changed.emit(self.serial, "Get Server")
        # Đọc server trong game; nếu chưa đọc được, lần gọi sau sẽ thử lại.
        server = self.guards.call("Get Server", get_server, self.ctx)
        if server:
            self.server = server
            self.ctx.server = server
            self.record(f"Đọc được server: {server}")
            self._register_boss_listener()
            # Gửi server cho UI xử lý/lưu; worker chỉ cập nhật self.server.
            self.server_found.emit(self.serial, server)

    def _on_bubble_disabled(self):
        """Không đủ kim cương: bỏ tích Bubble ở cấu hình và báo UI bỏ tích."""
        self.settings.setdefault("Initialization", {})["bubble"] = False
        self.bubble_disabled.emit(self.serial)

    def _is_daily_done(self, task: str) -> bool:
        return done_today(self.daily_done.get(task), self.server_time)

    def _set_civilization(self, civ: int):
        self.ctx.civilization = civ
        self.civilization_found.emit(self.serial, int(civ))

    def _set_city_map(self, city_map: dict):
        self.ctx.city_map = dict(city_map)
        self.city_map_found.emit(self.serial, json.dumps(city_map))

    def _forget_daily(self, task: str):
        self.daily_done.pop(task, None)
        self.daily_task_cleared.emit(self.serial, task)

    def _mark_daily_done(self, task: str):
        self.daily_done[task] = datetime.now().isoformat(timespec="seconds")
        self.daily_task_done.emit(self.serial, task)
        self.record(f"Hoàn thành: {task}")

    def _register_boss_listener(self):
        if self.boss_board is not None and JOIN_BOSS in self.activities:
            self.boss_board.register(self.serial, self.server, self.ctx._boss_event)

    def _report_boss(self, coords):
        if self.boss_board is not None:
            self.boss_board.publish(self.serial, self.server, coords)

    def _run_one(self, task):
        """Chạy thẳng hàm run riêng của nhiệm vụ (không qua hàm run của activity). Bubble được lo trước; tới hạn
        giữa chừng thì nhiệm vụ làm lại từ đầu."""
        self._current = task.key
        return self.guards.call(task.key, task.run, self.ctx, self.settings.get(task.group, {}))

    def _run_activity(self, activity: str, tab_settings: dict):
        self._current = activity
        # Tra registry để lấy hàm run theo tên activity.
        run = ACTIVITIES.get(activity)
        # Tên không tồn tại: ghi log, chờ ngắn rồi bỏ qua; ctx.sleep vẫn kiểm tra Stop/timeout.
        if run is None:
            self.log(f"Unknown activity: {activity}")
            self.ctx.sleep(1.0)
            return None
        # Trả nguyên kết quả; để exception truyền lên cấp điều phối xử lý.
        # Bubble được lo trước; tới hạn giữa chừng thì activity làm lại từ đầu.
        return self.guards.call(activity, run, self.ctx, tab_settings)

    def log(self, message: str):
        # Gắn serial vào log để phân biệt các thiết bị; gửi thêm lên tab Logs của thiết bị.
        _print_safe(f"[{self.serial}] {message}")
        self.log_message.emit(self.serial, message)

    def record(self, message: str):
        # Sự kiện đáng lưu (bắt đầu / xong / dừng nhiệm vụ...): vừa là log thường, vừa lưu DB (History).
        self.log(message)
        self.history.emit(self.serial, message)
