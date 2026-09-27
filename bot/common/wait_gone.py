"""
wait_gone.py — chờ màn hình vừa nhận diện biến mất (màn hình đã đổi).
"""
import time

from .delay import delay
from .find_first import find_first


def wait_gone(bot, targets, action, pos, top_left=(), timeout=10.0, interval=0.3,
              tolerance=10):
    """Trong tối đa `timeout` giây, cứ `interval` giây chụp màn hình 1 lần và
    dùng `find_first(targets)` kiểm tra `action` còn ở vị trí `pos` không
    (lệch dưới `tolerance` pixel vẫn coi là cùng chỗ); hết thì dừng ngay.
    Trả về ảnh chụp cuối cùng."""
    end = time.monotonic() + timeout   # thời điểm hết hạn chờ
    while True:
        delay(bot, interval)
        screen = bot.screenshot()
        now, now_pos = find_first(bot, screen, targets, top_left=top_left)
        # Cùng action ở cùng vị trí -> màn hình chưa đổi.
        same = now == action and (pos is None or (
            now_pos is not None and abs(now_pos[0] - pos[0]) < tolerance
            and abs(now_pos[1] - pos[1]) < tolerance))
        # Màn hình đã đổi hoặc hết thời gian chờ -> trả về ảnh vừa chụp.
        if not same or time.monotonic() >= end:
            return screen
