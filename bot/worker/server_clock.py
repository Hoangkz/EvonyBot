"""
server_clock.py — ServerClock: giờ reset server dùng chung mọi worker (một giá trị cho mọi thiết bị,
lưu ở bảng `settings` của DB).

Chưa biết giờ reset: worker đầu tiên cần tới thì nhận việc đi lấy (claim); các worker khác không lấy
nữa mà chạy bình thường (daily_reset tạm dùng 0h giờ máy) cho tới khi có giá trị. Lấy không được thì
nhả việc để lần sau (worker này hoặc worker khác) thử lại.
"""
import threading


class ServerClock:
    def __init__(self, server_time: str = ""):
        self._lock = threading.Lock()
        self._value = server_time or ""
        self._claimed = False

    @property
    def value(self) -> str:
        """Thời điểm reset (ISO, giờ máy), hoặc "" nếu chưa biết."""
        with self._lock:
            return self._value

    def set(self, server_time: str):
        with self._lock:
            self._value = server_time or ""

    def claim(self) -> bool:
        """True nếu worker gọi được giao đi lấy giờ reset: chưa có giá trị và chưa ai đang lấy."""
        with self._lock:
            if self._value or self._claimed:
                return False
            self._claimed = True
            return True

    def release(self, server_time: str | None):
        """Worker đã nhận việc báo kết quả: có giá trị thì lưu; rồi nhả việc."""
        with self._lock:
            if server_time:
                self._value = server_time
            self._claimed = False
