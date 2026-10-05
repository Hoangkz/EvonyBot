"""
bot_worker.py — BotWorker: chạy các nhiệm vụ của một thiết bị trên QThread riêng, tới khi Stop.

Thứ tự ưu tiên: Bubble > Auto Times Out > Join Boss > nhiệm vụ (scheduler.py, độ ưu tiên trong priority.json).
- Bubble: lo trước mọi lần chạy (_with_bubble); tới hạn thì ngắt mọi thứ đang chạy (BubbleDue).
- Auto Times Out (số phút chọn ở màn Home, chung mọi thiết bị): lo ngay sau bubble; chạy đủ số phút kể từ
  lần đóng game trước thì ngắt mọi thứ đang chạy (RestartDue) và đóng game; nhiệm vụ đang dở làm lại.
- Có chọn Join Boss: mỗi vòng chạy Join Boss (rảnh thì nhường), rồi 1 nhiệm vụ tối đa OTHERS_WINDOW
  giây; xong nhiệm vụ là quay lại Join Boss ngay. Hết giờ / có boss mới -> quay lại, nhiệm vụ đang dở
  làm lại đầu tiên ở vòng sau. Join Boss dừng hẳn (không phải rảnh) -> vẫn chạy tiếp các nhiệm vụ.
- Nhiệm vụ must_finish (priority.json): đã bắt đầu thì chạy tới xong; Bubble / Auto Times Out / boss mới /
  120 giây không ngắt (chỉ Stop). Xong rồi mới tới Bubble, Auto Times Out và Join Boss.
- Không chọn Join Boss: không có giới hạn 120 giây, các nhiệm vụ chạy lần lượt tới khi xong.
- Không tích Bubble: không có luật Bubble (không lo bubble, không bị ngắt vì bubble).
- Không còn nhiệm vụ tới lượt: nghỉ ngắn rồi xét lại (thread vẫn sống); qua mốc reset server thì các
  nhiệm vụ đã xong lại tới lượt.
- Chỉ chọn mỗi Join Boss: chạy Join Boss liên tục như trước.
"""
import json
import os
import sys
import threading
import time
import traceback
from datetime import datetime

from PyQt5.QtCore import QThread, pyqtSignal

from ..activities import ACTIVITIES
from ..activities.join_monster_war import IDLE as BOSS_IDLE
from ..common import GAME_PACKAGE, NotEnoughGems, get_server, keep_bubble
from ..daily_reset import done_today, last_reset
from ..context import BotContext, BotInterrupted, TimedOut
from ..context.errors import BossAvailable, BubbleDue, RestartDue, StopRequested, YieldToBoss
from .scheduler import Scheduler
from .server_clock import ServerClock
from .tasks import build_tasks, load_must_finish, load_priorities
from .status import STATUS_ERROR, STATUS_RUNNING, STATUS_STOPPED

JOIN_BOSS = "Join Monster War"
OTHERS_WINDOW = 120   # giây tối đa cho 1 nhiệm vụ khi có Join Boss (không có Join Boss: không giới hạn)
IDLE_WAIT = 5         # giây nghỉ khi không còn nhiệm vụ nào tới lượt
BUBBLE = "Bubble"
BUBBLE_RENEW_BEFORE = 7200   # bubble còn <= 2 tiếng -> dùng bubble mới
BUBBLE_RETRY = 300           # đọc / dùng bubble không được -> 5 phút sau thử lại
AUTO_RESTART = "Auto Times Out"
RESTART_WAIT = 3             # giây chờ sau khi đóng game


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


def _seconds_until(iso) -> float | None:
    """Số giây từ bây giờ tới thời điểm ISO (giờ máy); None nếu rỗng / sai định dạng."""
    try:
        return (datetime.fromisoformat(iso) - datetime.now()).total_seconds()
    except (TypeError, ValueError):
        return None


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
        # Bubble: tích ở tab Initialization -> luôn giữ bubble, ưu tiên hơn mọi activity.
        init = settings.get("Initialization", {})
        self.bubble_enabled = bool(init.get("bubble"))
        self.bubble_type = init.get("bubble_type") or "24h"
        self._bubble_expiry = None       # time.monotonic() lúc bubble hết; None = chưa biết
        self._bubble_next_check = 0.0    # time.monotonic() lần xử lý bubble tiếp theo
        # Đang chạy nhiệm vụ must_finish: hoãn bubble / Auto Times Out tới khi xong.
        self._hold_interrupts = False
        # Auto Times Out: hàm trả số phút chọn ở màn Home (đọc lại mỗi lần, đổi là dùng ngay; 0 = tắt),
        # tính từ lúc bot bắt đầu / lần đóng game gần nhất.
        self._auto_timeout = auto_timeout or (lambda: 0)
        self._last_restart = time.monotonic()
        # Thời điểm bubble hết đã lưu trong DB: còn hơn 2 tiếng thì không vào game
        # kiểm tra, hẹn lúc còn 2 tiếng.
        left = _seconds_until(init.get("bubble_until"))
        if left is not None and left > 0:
            self._bubble_expiry = time.monotonic() + left
            self._bubble_next_check = self._bubble_expiry - BUBBLE_RENEW_BEFORE

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
            self.ctx.daily_keys = lambda: list(self.daily_done)
            self.ctx.record = self.record
            # Nền văn minh đã lưu DB (None = chưa biết); bot tự xếp thì lưu lại qua signal.
            self.ctx.civilization = self.settings.get("Initialization", {}).get("civilization") or None
            self.ctx.set_civilization = self._set_civilization
            # Bản đồ thành đã lưu DB ({công trình: [x, y]}, {} = chưa quét); bot quét xong thì lưu lại qua signal.
            self.ctx.city_map = dict(self.settings.get("Initialization", {}).get("city_map") or {})
            self.ctx.set_city_map = self._set_city_map
            self._register_boss_listener()
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
            self._ensure_server()
            self.activity_changed.emit(self.serial, activity)
            self._run_activity(activity, self.settings.get(activity, {}))

    def _run_tasks(self):
        """Vòng lặp chính (xem docstring đầu file) cho tới khi Stop."""
        boss = JOIN_BOSS in self.activities
        tasks = build_tasks(self.activities, {JOIN_BOSS}, load_priorities(), load_must_finish())
        if boss and not tasks:
            self._run_once([JOIN_BOSS])   # chỉ Join Boss: chạy liên tục như trước
            return
        scheduler = Scheduler(tasks, lambda: last_reset(self.server_time))
        resume = None   # nhiệm vụ bị ngắt giữa chừng: làm lại đầu tiên ở vòng sau
        while not self._stop.is_set():
            self._ensure_server()
            if boss:
                boss = self._check_boss()
            task = resume if resume is not None and scheduler.is_due(resume) else scheduler.pick()
            resume = None
            if task is None:
                self._with_bubble(None, self.ctx.sleep, IDLE_WAIT)
                continue
            if not self._run_task(scheduler, task, boss):
                resume = task

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

    def _run_task(self, scheduler: Scheduler, task, boss: bool) -> bool:
        """Chạy 1 nhiệm vụ. Có Join Boss: tối đa OTHERS_WINDOW giây, boss mới cũng ngắt; không có Join
        Boss: không giới hạn thời gian. must_finish: không bị Bubble / boss / thời gian ngắt (chỉ Stop).
        True nếu chạy tới cuối (xong), False nếu bị ngắt (làm lại ở vòng sau)."""
        if boss and not task.must_finish:
            # Timeout chỉ phát hiện khi BotContext kiểm tra; không ngắt cưỡng chế.
            self.ctx._deadline = time.monotonic() + OTHERS_WINDOW
            self.ctx._boss_interrupt_enabled = True
        try:
            # Lo bubble trước (không có Join Boss thì không có bước nào khác lo), rồi xét Stop / boss mới.
            self._with_bubble(None, self.ctx.check)
            if task.must_finish:
                # Bubble / Auto Times Out vừa lo xong -> hoãn tới khi nhiệm vụ xong.
                self._hold_interrupts = True
                self.ctx._bubble_due_at = self.ctx._restart_due_at = None
            self.activity_changed.emit(self.serial, task.group)
            scheduler.started(task)
            self.record(f"Bắt đầu: {task.key}")
            self.ctx.again_after = None
            self._run_activity(task.group, self.settings.get(task.group, {}))
            scheduler.finished(task, again_after=self.ctx.again_after)
            self.record(f"Xong: {task.key}")
            return True
        # Bị ngắt: lượt sau gọi lại từ đầu hàm run(); worker không lưu điểm thực thi.
        except TimedOut:
            self.record(f"Tạm dừng: {task.key} (hết {OTHERS_WINDOW} giây, quay lại Join Monster War)")
            return False    # hết OTHERS_WINDOW giây
        except YieldToBoss:
            return False    # activity vừa xong 1 nhiệm vụ con -> kiểm tra boss ngay, lượt sau làm tiếp
        except BossAvailable:
            self.record(f"Tạm dừng: {task.key} (có boss mới, chuyển sang Join Monster War)")
            return False
        except StopRequested:
            self.record(f"Dừng: {task.key} (người dùng bấm Stop)")
            raise
        # Luôn gỡ deadline, kể cả khi Stop/lỗi, để không ảnh hưởng lượt chạy boss.
        finally:
            self._hold_interrupts = False
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
        server = self._with_bubble("Get Server", get_server, self.ctx)
        if server:
            self.server = server
            self.record(f"Đọc được server: {server}")
            self._register_boss_listener()
            # Gửi server cho UI xử lý/lưu; worker chỉ cập nhật self.server.
            self.server_found.emit(self.serial, server)

    def _with_bubble(self, label, fn, *args):
        """Gọi fn sau khi lo xong bubble rồi Auto Times Out. Tới hạn giữa chừng (BubbleDue / RestartDue)
        -> xử lý rồi gọi lại fn từ đầu."""
        while True:
            acted = self._ensure_bubble()
            acted = self._ensure_restart() or acted
            if acted and label:
                self.activity_changed.emit(self.serial, label)
            try:
                return fn(*args)
            except BubbleDue:
                self.log(f"Bubble tới hạn; xử lý bubble rồi làm lại {label or 'bước đang dở'}")
            except RestartDue:
                self.log(f"Tới giờ Auto Times Out; đóng game rồi làm lại {label or 'bước đang dở'}")

    def _ensure_bubble(self) -> bool:
        """Có tích Bubble: chưa biết thời gian -> đi lấy; còn <= 2 tiếng -> dùng
        bubble mới. Rồi hẹn ctx ngắt activity đúng lúc cần xử lý lần sau.
        Trả về True nếu vừa thao tác trong game (màn hình đã đổi)."""
        if not self.bubble_enabled:
            return False
        ctx = self.ctx
        if self._hold_interrupts:
            ctx._bubble_due_at = None
            return False
        if time.monotonic() < self._bubble_next_check:
            ctx._bubble_due_at = self._bubble_next_check
            return False

        # Bước bubble không bị boss / deadline 120 giây / Auto Times Out cắt ngang; khôi phục sau đó
        # (_ensure_restart chạy ngay sau sẽ hẹn lại Auto Times Out).
        saved = (ctx._deadline, ctx._boss_interrupt_enabled)
        ctx._deadline, ctx._boss_interrupt_enabled, ctx._bubble_due_at = None, False, None
        ctx._restart_due_at = None
        try:
            self.activity_changed.emit(self.serial, BUBBLE)
            # Vào game đọc lại cả khi đã biết: có thể bubble đã được gia hạn tay.
            try:
                remaining = keep_bubble(ctx, self.bubble_type, BUBBLE_RENEW_BEFORE)
            except NotEnoughGems:
                # Không mua được thì thôi giữ bubble: bỏ tích ở UI, không thử lại nữa.
                self.record(f"Bubble: không đủ kim cương mua {self.bubble_type}, bỏ tích Bubble")
                self.bubble_enabled = False
                self.settings.setdefault("Initialization", {})["bubble"] = False
                self.bubble_disabled.emit(self.serial)
                return True
            if remaining is None:
                self.log("Bubble: không đọc được thời gian, sẽ thử lại sau")
            else:
                self._set_bubble_remaining(remaining)
                if remaining <= BUBBLE_RENEW_BEFORE:
                    self.log(f"Bubble: chưa dùng được bubble {self.bubble_type}, sẽ thử lại sau")
        finally:
            ctx._deadline, ctx._boss_interrupt_enabled = saved
            # Còn > 2 tiếng -> hẹn lúc còn đúng 2 tiếng; không thì thử lại sau BUBBLE_RETRY.
            if self._bubble_expiry is not None and self._bubble_left() > BUBBLE_RENEW_BEFORE:
                self._bubble_next_check = self._bubble_expiry - BUBBLE_RENEW_BEFORE
            else:
                self._bubble_next_check = time.monotonic() + BUBBLE_RETRY
            # Đã bỏ tích (không đủ kim cương) thì không hẹn nữa.
            ctx._bubble_due_at = self._bubble_next_check if self.bubble_enabled else None
        return True

    def _ensure_restart(self) -> bool:
        """Auto Times Out (phút, màn Home; 0 = tắt): chạy đủ số phút kể từ lần đóng game trước -> đóng game
        (bot đang chạy tự mở lại qua go_home). Chưa tới giờ thì hẹn ctx ngắt activity đúng lúc.
        Trả về True nếu vừa đóng game (màn hình đã đổi)."""
        ctx = self.ctx
        minutes = self._auto_timeout()
        if self._hold_interrupts or minutes <= 0:
            ctx._restart_due_at = None
            return False
        due = self._last_restart + minutes * 60
        if time.monotonic() < due:
            ctx._restart_due_at = due
            return False

        # Bước đóng game không bị boss / deadline 120 giây / bubble cắt ngang; khôi phục sau đó.
        saved = (ctx._deadline, ctx._boss_interrupt_enabled, ctx._bubble_due_at)
        ctx._deadline, ctx._boss_interrupt_enabled = None, False
        ctx._bubble_due_at = ctx._restart_due_at = None
        try:
            self.activity_changed.emit(self.serial, AUTO_RESTART)
            self.record(f"Auto Times Out: đã chạy {minutes} phút, đóng game")
            # Chỉ đóng game; activity chạy sau thấy launcher thì tự mở lại (go_home).
            ctx.shell(f"am force-stop {GAME_PACKAGE}")
            ctx.sleep(RESTART_WAIT)
        finally:
            ctx._deadline, ctx._boss_interrupt_enabled, ctx._bubble_due_at = saved
            self._last_restart = time.monotonic()
            ctx._restart_due_at = self._last_restart + minutes * 60
        return True

    def _bubble_left(self) -> float:
        return self._bubble_expiry - time.monotonic()

    def _set_bubble_remaining(self, seconds: float):
        seconds = max(0, seconds)
        self._bubble_expiry = time.monotonic() + seconds
        self.bubble_found.emit(self.serial, int(seconds))

    def _is_daily_done(self, task: str) -> bool:
        return done_today(self.daily_done.get(task), self.server_time)

    def _set_civilization(self, civ: int):
        self.ctx.civilization = civ
        self.civilization_found.emit(self.serial, int(civ))

    def _set_city_map(self, city_map: dict):
        self.ctx.city_map = dict(city_map)
        self.city_map_found.emit(self.serial, json.dumps(city_map))

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
        return self._with_bubble(activity, run, self.ctx, tab_settings)

    def log(self, message: str):
        # Gắn serial vào log để phân biệt các thiết bị; gửi thêm lên tab Logs của thiết bị.
        _print_safe(f"[{self.serial}] {message}")
        self.log_message.emit(self.serial, message)

    def record(self, message: str):
        # Sự kiện đáng lưu (bắt đầu / xong / dừng nhiệm vụ...): vừa là log thường, vừa lưu DB (History).
        self.log(message)
        self.history.emit(self.serial, message)
