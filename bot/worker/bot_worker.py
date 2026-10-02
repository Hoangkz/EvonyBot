"""
bot_worker.py — BotWorker: chạy các nhiệm vụ của một thiết bị trên QThread riêng, tới khi Stop.

Thứ tự ưu tiên: Bubble > Join Boss > nhiệm vụ (scheduler.py, độ ưu tiên trong priority.json).
- Bubble: lo trước mọi lần chạy (_with_bubble); tới hạn thì ngắt mọi thứ đang chạy (BubbleDue).
- Có chọn Join Boss: mỗi vòng chạy Join Boss (rảnh thì nhường), rồi 1 nhiệm vụ tối đa OTHERS_WINDOW
  giây; xong nhiệm vụ là quay lại Join Boss ngay. Hết giờ / có boss mới -> quay lại, nhiệm vụ đang dở
  làm lại đầu tiên ở vòng sau. Join Boss dừng hẳn (không phải rảnh) -> vẫn chạy tiếp các nhiệm vụ.
- Không chọn Join Boss: không có giới hạn 120 giây, các nhiệm vụ chạy lần lượt tới khi xong.
- Không tích Bubble: không có luật Bubble (không lo bubble, không bị ngắt vì bubble).
- Không còn nhiệm vụ tới lượt: nghỉ ngắn rồi xét lại (thread vẫn sống); qua mốc reset server thì các
  nhiệm vụ đã xong lại tới lượt.
- Chỉ chọn mỗi Join Boss: chạy Join Boss liên tục như trước.
"""
import os
import threading
import time
import traceback
from datetime import datetime

from PyQt5.QtCore import QThread, pyqtSignal

from ..activities import ACTIVITIES
from ..activities.join_monster_war import IDLE as BOSS_IDLE
from ..common import NotEnoughGems, get_server, keep_bubble
from ..daily_reset import done_today, last_reset
from ..context import BotContext, BotInterrupted, TimedOut
from ..context.errors import BossAvailable, BubbleDue, StopRequested, YieldToBoss
from .scheduler import Scheduler
from .server_clock import ServerClock
from .tasks import build_tasks, load_priorities
from .status import STATUS_ERROR, STATUS_RUNNING, STATUS_STOPPED

JOIN_BOSS = "Join Monster War"
OTHERS_WINDOW = 120   # giây tối đa cho 1 nhiệm vụ khi có Join Boss (không có Join Boss: không giới hạn)
IDLE_WAIT = 5         # giây nghỉ khi không còn nhiệm vụ nào tới lượt
BUBBLE = "Bubble"
BUBBLE_RENEW_BEFORE = 3600   # bubble còn <= 1 tiếng -> dùng bubble mới
BUBBLE_RETRY = 300           # đọc / dùng bubble không được -> 5 phút sau thử lại


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
    bubble_disabled = pyqtSignal(str)         # (serial) không đủ kim cương -> bỏ tích Bubble
    log_message = pyqtSignal(str, str)        # (serial, dòng log) -> tab Logs > Info
    history = pyqtSignal(str, str)            # (serial, sự kiện) -> lưu DB + tab Logs > History

    def __init__(self, serial: str, activities: list[str], settings: dict, parent=None, *,
                 boss_board=None, daily_done: dict | None = None, server_clock: ServerClock | None = None):
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
        # Thời điểm bubble hết đã lưu trong DB: còn hơn 1 tiếng thì không vào game
        # kiểm tra, hẹn lúc còn 1 tiếng.
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
            self.ctx.record = self.record
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
        tasks = build_tasks(self.activities, {JOIN_BOSS}, load_priorities())
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
        Boss: không giới hạn thời gian. True nếu chạy tới cuối (xong), False nếu bị ngắt (làm lại ở vòng sau)."""
        if boss:
            # Timeout chỉ phát hiện khi BotContext kiểm tra; không ngắt cưỡng chế.
            self.ctx._deadline = time.monotonic() + OTHERS_WINDOW
            self.ctx._boss_interrupt_enabled = True
        try:
            # Lo bubble trước (không có Join Boss thì không có bước nào khác lo), rồi xét Stop / boss mới.
            self._with_bubble(None, self.ctx.check)
            self.activity_changed.emit(self.serial, task.group)
            scheduler.started(task)
            self.record(f"Bắt đầu: {task.key}")
            self._run_activity(task.group, self.settings.get(task.group, {}))
            scheduler.finished(task)
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
        """Gọi fn sau khi lo xong bubble. Bubble tới hạn giữa chừng (BubbleDue)
        -> xử lý bubble rồi gọi lại fn từ đầu."""
        while True:
            if self._ensure_bubble() and label:
                self.activity_changed.emit(self.serial, label)
            try:
                return fn(*args)
            except BubbleDue:
                self.log(f"Bubble tới hạn; xử lý bubble rồi làm lại {label or 'bước đang dở'}")

    def _ensure_bubble(self) -> bool:
        """Có tích Bubble: chưa biết thời gian -> đi lấy; còn <= 1 tiếng -> dùng
        bubble mới. Rồi hẹn ctx ngắt activity đúng lúc cần xử lý lần sau.
        Trả về True nếu vừa thao tác trong game (màn hình đã đổi)."""
        if not self.bubble_enabled:
            return False
        ctx = self.ctx
        if time.monotonic() < self._bubble_next_check:
            ctx._bubble_due_at = self._bubble_next_check
            return False

        # Bước bubble không bị boss / deadline 120 giây cắt ngang; khôi phục sau đó.
        saved = (ctx._deadline, ctx._boss_interrupt_enabled)
        ctx._deadline, ctx._boss_interrupt_enabled, ctx._bubble_due_at = None, False, None
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
            # Còn > 1 tiếng -> hẹn lúc còn đúng 1 tiếng; không thì thử lại sau BUBBLE_RETRY.
            if self._bubble_expiry is not None and self._bubble_left() > BUBBLE_RENEW_BEFORE:
                self._bubble_next_check = self._bubble_expiry - BUBBLE_RENEW_BEFORE
            else:
                self._bubble_next_check = time.monotonic() + BUBBLE_RETRY
            # Đã bỏ tích (không đủ kim cương) thì không hẹn nữa.
            ctx._bubble_due_at = self._bubble_next_check if self.bubble_enabled else None
        return True

    def _bubble_left(self) -> float:
        return self._bubble_expiry - time.monotonic()

    def _set_bubble_remaining(self, seconds: float):
        seconds = max(0, seconds)
        self._bubble_expiry = time.monotonic() + seconds
        self.bubble_found.emit(self.serial, int(seconds))

    def _is_daily_done(self, task: str) -> bool:
        return done_today(self.daily_done.get(task), self.server_time)

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
        print(f"[{self.serial}] {message}")
        self.log_message.emit(self.serial, message)

    def record(self, message: str):
        # Sự kiện đáng lưu (bắt đầu / xong / dừng nhiệm vụ...): vừa là log thường, vừa lưu DB (History).
        self.log(message)
        self.history.emit(self.serial, message)
