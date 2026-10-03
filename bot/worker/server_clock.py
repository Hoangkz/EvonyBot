"""
server_clock.py — ServerClock: giờ reset server dùng chung mọi worker.

Người dùng chọn giờ reset ở màn Home ("HH:MM", mặc định 14:00, lưu bảng `settings` của DB); main gán
vào đây, các worker đang chạy đọc giá trị mới ngay (bot/daily_reset.py tính mốc reset).
"""
import threading

from ..daily_reset import reset_clock


class ServerClock:
    def __init__(self, server_time: str = ""):
        self._lock = threading.Lock()
        self._value = reset_clock(server_time)

    @property
    def value(self) -> str:
        """Giờ reset "HH:MM"."""
        with self._lock:
            return self._value

    def set(self, server_time: str):
        with self._lock:
            self._value = reset_clock(server_time)
