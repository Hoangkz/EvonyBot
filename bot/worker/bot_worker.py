"""
bot_worker.py — BotWorker: runs the device's selected activities once each
on its own QThread (Join Boss keeps going until it stops by itself or Stop).
"""
import threading
import time

from PyQt5.QtCore import QThread, pyqtSignal

from ..activities import ACTIVITIES
from ..activities.join_monster_war import IDLE as BOSS_IDLE
from ..common import get_server, get_server_time
from ..context import BotContext, BotInterrupted, TimedOut
from .status import STATUS_ERROR, STATUS_RUNNING, STATUS_STOPPED

JOIN_BOSS = "Join Monster War"
OTHERS_WINDOW = 120   # giây tối đa làm activity khác trước khi quay lại kiểm tra boss


# Điều phối activity của một thiết bị trên QThread riêng.
class BotWorker(QThread):
    # Gửi serial kèm dữ liệu để UI cập nhật đúng thiết bị.
    activity_changed = pyqtSignal(str, str)   # (serial, activity)
    status_changed = pyqtSignal(str, str)     # (serial, status)
    server_found = pyqtSignal(str, str)       # (serial, server)

    server_time_found = pyqtSignal(str, str)  # (serial, thời điểm reset giờ máy)

    def __init__(self, serial: str, activities: list[str], settings: dict, parent=None):
        super().__init__(parent)
        # Lưu thiết bị và sao chép danh sách activity cho lượt chạy.
        self.serial = serial
        self.activities = list(activities)
        # Nhận cấu hình từ UI; ở đây giữ tham chiếu, không sao chép settings.
        self.settings = settings            # DeviceView.get_settings() snapshot
        # Dùng server đã cấu hình; nếu thiếu sẽ thử đọc trong game.
        self.server = settings.get("Initialization", {}).get("server") or ""
        # Cờ Stop dùng chung giữa UI và BotContext.
        self._stop = threading.Event()
        self.server_time = settings.get("Initialization", {}).get("server_time") or ""

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
            # Hết activity phụ: chạy boss với cấu hình gốc rồi kết thúc điều phối.
            if not pending:
                self._run_once([JOIN_BOSS])
                return

            # Lấy giờ reset trước: menu này cũng nằm trên đường lấy server.
            self._ensure_server_time()
            self._ensure_server()
            self.activity_changed.emit(self.serial, JOIN_BOSS)
            # Tạo cấu hình tạm: boss trả về IDLE khi rảnh để nhường activity phụ; không sửa settings gốc.
            result = self._run_activity(JOIN_BOSS, {**self.settings.get(JOIN_BOSS, {}), "exit_when_idle": True})
            # Boss trả về khác IDLE: chạy nốt danh sách chờ rồi kết thúc.
            if result != BOSS_IDLE:
                self._run_once(pending)   # bắt đầu từ activity đang dở
                return

            # Boss rảnh: cấp chung 120 giây cho cả nhóm activity phụ, không phải từng activity.
            # Dùng monotonic để không bị ảnh hưởng bởi chỉnh giờ hệ thống.
            # Timeout chỉ phát hiện khi BotContext kiểm tra; không ngắt cưỡng chế.
            self.ctx._deadline = time.monotonic() + OTHERS_WINDOW
            try:
                # Chạy lần lượt các activity còn chờ trong khoảng thời gian được cấp.
                while pending:
                    self.activity_changed.emit(self.serial, pending[0])
                    self._run_activity(pending[0], self.settings.get(pending[0], {}))
                    # Chỉ xóa khi activity trả về bình thường; nếu timeout thì vẫn giữ trong pending.
                    pending.pop(0)
            # Hết thời gian: giữ activity đang dở và quay lại kiểm tra boss.
            # Lượt sau gọi lại từ đầu hàm run(); worker không lưu điểm thực thi.
            except TimedOut:
                pass    # hết 2 phút -> pending[0] là activity đang dở, lượt sau làm tiếp
            # Luôn gỡ deadline, kể cả khi Stop/lỗi, để không ảnh hưởng lượt chạy boss.
            finally:
                self.ctx._deadline = None

    def _ensure_server_time(self):
        """Chỉ đọc khi chưa có thời điểm reset; không đọc được thì lần sau thử lại."""
        if self.server_time:
            return
        self.activity_changed.emit(self.serial, "Get Server Time")
        server_time = get_server_time(self.ctx)
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
        server = get_server(self.ctx)
        if server:
            self.server = server
            # Gửi server cho UI xử lý/lưu; worker chỉ cập nhật self.server.
            self.server_found.emit(self.serial, server)

    def _run_activity(self, activity: str, tab_settings: dict):
        # Tra registry để lấy hàm run theo tên activity.
        run = ACTIVITIES.get(activity)
        # Tên không tồn tại: ghi log, chờ ngắn rồi bỏ qua; ctx.sleep vẫn kiểm tra Stop/timeout.
        if run is None:
            self.log(f"Unknown activity: {activity}")
            self.ctx.sleep(1.0)
            return None
        # Trả nguyên kết quả; để exception truyền lên cấp điều phối xử lý.
        return run(self.ctx, tab_settings)

    def log(self, message: str):
        # Gắn serial vào log để phân biệt các thiết bị.
        print(f"[{self.serial}] {message}")
