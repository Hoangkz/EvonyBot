"""
wait_until.py — chờ tới khi màn hình thoả một điều kiện.
"""
import time

from .delay import delay


def wait_until(bot, check, timeout=10.0, interval=0.3):
    """Cứ `interval` giây chụp màn hình 1 lần và gọi `check(screen)`, tới khi
    nó trả về giá trị khác None / False hoặc hết `timeout` giây.
    Trả về (giá trị của check — None nếu hết giờ, ảnh chụp cuối cùng)."""
    end = time.monotonic() + timeout   # thời điểm hết hạn chờ
    while True:
        delay(bot, interval)
        screen = bot.screenshot()
        value = check(screen)
        if value is not None and value is not False:
            return value, screen
        if time.monotonic() >= end:
            return None, screen
