"""
bot_worker.py — BotWorker: runs the device's selected activities once each
on its own QThread (Join Boss keeps going until it stops by itself or Stop).
"""
import threading
import time
from datetime import datetime

from PyQt5.QtCore import QThread, pyqtSignal

from ..activities import ACTIVITIES
from ..activities.join_monster_war import IDLE as BOSS_IDLE
from ..common import NotEnoughGems, get_server, get_server_time, keep_bubble
from ..daily_reset import done_today, last_reset
from ..context import BotContext, BotInterrupted, TimedOut
from ..context.errors import BossAvailable, BubbleDue
from .status import STATUS_ERROR, STATUS_RUNNING, STATUS_STOPPED

JOIN_BOSS = "Join Monster War"
DAILY = "Daily Activities"
OTHERS_WINDOW = 120   # giây tối đa làm activity khác trước khi quay lại kiểm tra boss
IDLE_WAIT = 5         # giây nghỉ khi boss rảnh mà không còn activity khác để làm
BUBBLE = "Bubble"
BUBBLE_RENEW_BEFORE = 3600   # bubble còn <= 1 tiếng -> dùng bubble mới
BUBBLE_RETRY = 300           # đọc / dùng bubble không được -> 5 phút sau thử lại


def _seconds_until(iso) -> float | None:
    """Số giây từ bây giờ tới thời điểm ISO (giờ máy); None nếu rỗng / sai định dạng."""
    try:
        return (datetime.fromisoformat(iso) - datetime.now()).total_seconds()
    except (TypeError, ValueError):
        return None


# Điều phối activity của một thiết bị trên QThread riêng.
class BotWorker(QThread):
    # Gửi serial kèm dữ liệu để UI cập nhật đúng thiết bị.
    activity_changed = pyqtSignal(str, str)   # (serial, activity)
    status_changed = pyqtSignal(str, str)     # (serial, status)
    server_found = pyqtSignal(str, str)       # (serial, server)

    server_time_found = pyqtSignal(str, str)  # (serial, thời điểm reset giờ máy)
    daily_task_done = pyqtSignal(str, str)    # (serial, task Daily Activities vừa xong)
    bubble_found = pyqtSignal(str, int)       # (serial, giây bubble còn lại; 0 = không có)
    bubble_disabled = pyqtSignal(str)         # (serial) không đủ kim cương -> bỏ tích Bubble

    def __init__(self, serial: str, activities: list[str], settings: dict, parent=None, *,
                 boss_board=None, daily_done: dict | None = None):
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
        self.server_time = settings.get("Initialization", {}).get("server_time") or ""
        # {task: done_at} lấy từ DB; task chỉ tính là xong nếu done_at sau mốc reset gần nhất.
        self.daily_done = dict(daily_done or {})
        self._daily_ran_for = None   # mốc reset của lần chạy Daily Activities gần nhất
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
            self._register_boss_listener()
            # Tách activity phụ để chọn chế độ điều phối.
            others = [a for a in self.activities if a != JOIN_BOSS]
            # Có cả boss và activity phụ thì ưu tiên boss; còn lại chạy theo danh sách.
            if JOIN_BOSS in self.activities and others:
                self._boss_priority(others)
            else:
                self._run_once(self.activities)
        # Ngắt có chủ đích (Stop/timeout truyền tới đây) không xem là lỗi.
        except BotInterrupted:
            pass
        # Lỗi ngoài dự kiến: dừng lượt chạy và báo nội dung lỗi.
        except Exception as e:
            status = f"{STATUS_ERROR}: {e}"
            print(f"[{self.serial}] {status}")
        # Luôn xóa activity đang hiển thị và báo trạng thái cuối, kể cả khi lỗi.
        finally:
            if self.boss_board is not None:
                self.boss_board.unregister(self.serial)
            self.activity_changed.emit(self.serial, "None")
            self.status_changed.emit(self.serial, status)

    def _run_once(self, activities: list[str]):
        """Chạy tuần tự mỗi activity 1 lần (nhiệm vụ xong là xong)."""
        # Gọi từng activity theo thứ tự; vòng lặp bên trong do activity tự quản lý.
        for activity in activities:
            # Kiểm tra Stop trước khi bắt đầu activity tiếp theo.
            if self._stop.is_set():
                break
            # Thử lấy server nếu chưa biết, sau đó báo activity hiện tại cho UI.
            # Lấy giờ reset trước: menu này cũng nằm trên đường lấy server.
            self._ensure_server_time()
            self._ensure_server()
            self.activity_changed.emit(self.serial, activity)
            # Truyền cấu hình riêng theo tên; nếu thiếu thì dùng dict rỗng.
            self._run_activity(activity, self.settings.get(activity, {}))

    def _boss_priority(self, others: list[str]):
        """Ưu tiên Join Boss; boss rảnh -> làm activity khác tối đa OTHERS_WINDOW giây
        rồi quay lại kiểm tra boss. Activity bị cắt giữa chừng được làm tiếp đầu
        tiên ở lượt sau; activity chạy tới cuối là hoàn thành, bỏ khỏi danh sách.
        - Join Boss dừng hẳn (không phải rảnh) -> chạy nốt các activity chưa xong.
        - Các activity khác đã hoàn thành hết -> chỉ còn Join Boss."""
        # Danh sách chờ; activity bị timeout vẫn giữ ở đầu để được gọi lại trước.
        pending = list(others)   # activity chưa hoàn thành, pending[0] là cái đang dở
        # Lặp lịch ưu tiên boss cho đến khi Stop hoặc có nhánh return.
        while not self._stop.is_set():
            # Qua mốc reset server -> Daily Activities được làm lại trong ngày mới.
            if DAILY in others and DAILY not in pending and self._daily_reset_passed():
                pending.append(DAILY)
            # Hết activity phụ: chạy boss với cấu hình gốc rồi kết thúc điều phối.
            # Có Daily Activities thì vẫn giữ vòng lặp để chờ ngày mới.
            if not pending and DAILY not in others:
                self._run_once([JOIN_BOSS])
                return

            # Lấy giờ reset trước: menu này cũng nằm trên đường lấy server.
            self._ensure_server_time()
            self._ensure_server()
            self.activity_changed.emit(self.serial, JOIN_BOSS)
            self.ctx._boss_event.clear()
            # Tạo cấu hình tạm: boss trả về IDLE khi rảnh để nhường activity phụ; không sửa settings gốc.
            result = self._run_activity(JOIN_BOSS, {**self.settings.get(JOIN_BOSS, {}), "exit_when_idle": True})
            # Boss trả về khác IDLE: chạy nốt danh sách chờ rồi kết thúc.
            if result != BOSS_IDLE:
                self._run_once(pending)   # bắt đầu từ activity đang dở
                return

            # Boss rảnh: cấp chung 120 giây cho cả nhóm activity phụ, không phải từng activity.
            # Dùng monotonic để không bị ảnh hưởng bởi chỉnh giờ hệ thống.
            # Timeout chỉ phát hiện khi BotContext kiểm tra; không ngắt cưỡng chế.
            if not pending:
                # Chỉ còn chờ ngày mới cho Daily Activities: nghỉ ngắn rồi kiểm tra boss lại.
                self._with_bubble(None, self.ctx.sleep, IDLE_WAIT)
                continue
            self.ctx._deadline = time.monotonic() + OTHERS_WINDOW
            self.ctx._boss_interrupt_enabled = True
            try:
                # Chạy lần lượt các activity còn chờ trong khoảng thời gian được cấp.
                while pending:
                    self.ctx.check()
                    self.activity_changed.emit(self.serial, pending[0])
                    self._run_activity(pending[0], self.settings.get(pending[0], {}))
                    # Chỉ xóa khi activity trả về bình thường; nếu timeout thì vẫn giữ trong pending.
                    pending.pop(0)
            # Hết thời gian: giữ activity đang dở và quay lại kiểm tra boss.
            # Lượt sau gọi lại từ đầu hàm run(); worker không lưu điểm thực thi.
            except TimedOut:
                pass    # hết 2 phút -> pending[0] là activity đang dở, lượt sau làm tiếp
            except BossAvailable:
                self.log("New boss on this server; switching to Join Monster War")
            except BubbleDue:
                pass    # bubble tới hạn giữa 2 activity -> lượt sau xử lý bubble trước
            # Luôn gỡ deadline, kể cả khi Stop/lỗi, để không ảnh hưởng lượt chạy boss.
            finally:
                self.ctx._boss_interrupt_enabled = False
                self.ctx._deadline = None

    def _ensure_server_time(self):
        """Chỉ đọc khi chưa có thời điểm reset; không đọc được thì lần sau thử lại."""
        if self.server_time:
            return
        self.activity_changed.emit(self.serial, "Get Server Time")
        server_time = self._with_bubble("Get Server Time", get_server_time, self.ctx)
        if server_time:
            self.server_time = server_time
            self.settings.setdefault("Initialization", {})["server_time"] = server_time
            self.server_time_found.emit(self.serial, server_time)

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
                self.log(f"Bubble: không đủ kim cương mua {self.bubble_type}, bỏ tích Bubble")
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

    def _daily_reset_passed(self) -> bool:
        return self._daily_ran_for is not None and last_reset(self.server_time) > self._daily_ran_for

    def _is_daily_done(self, task: str) -> bool:
        return done_today(self.daily_done.get(task), self.server_time)

    def _mark_daily_done(self, task: str):
        self.daily_done[task] = datetime.now().isoformat(timespec="seconds")
        self.daily_task_done.emit(self.serial, task)

    def _register_boss_listener(self):
        if self.boss_board is not None and JOIN_BOSS in self.activities:
            self.boss_board.register(self.serial, self.server, self.ctx._boss_event)

    def _report_boss(self, coords):
        if self.boss_board is not None:
            self.boss_board.publish(self.serial, self.server, coords)

    def _run_activity(self, activity: str, tab_settings: dict):
        # Tra registry để lấy hàm run theo tên activity.
        run = ACTIVITIES.get(activity)
        # Tên không tồn tại: ghi log, chờ ngắn rồi bỏ qua; ctx.sleep vẫn kiểm tra Stop/timeout.
        if run is None:
            self.log(f"Unknown activity: {activity}")
            self.ctx.sleep(1.0)
            return None
        if activity == DAILY:
            self._daily_ran_for = last_reset(self.server_time)
        # Trả nguyên kết quả; để exception truyền lên cấp điều phối xử lý.
        # Bubble được lo trước; tới hạn giữa chừng thì activity làm lại từ đầu.
        return self._with_bubble(activity, run, self.ctx, tab_settings)

    def log(self, message: str):
        # Gắn serial vào log để phân biệt các thiết bị.
        print(f"[{self.serial}] {message}")
