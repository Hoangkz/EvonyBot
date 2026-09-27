"""
wait_gone.py — chờ màn hình vừa nhận diện biến mất (màn hình đã đổi).
"""
import time

from .delay import delay


def wait_gone(bot, targets, action, pos, top_left=(), timeout=10.0, interval=0.3,
              tolerance=10):
    """Trong tối đa `timeout` giây, cứ `interval` giây chụp màn hình 1 lần và
    kiểm tra `action` còn ở vị trí `pos` không (lệch dưới `tolerance` pixel vẫn
    coi là cùng chỗ); hết thì dừng ngay. Trả về ảnh chụp cuối cùng.

    Để nhẹ CPU, chỉ dò các ảnh của `action` trong `targets` và chỉ trong vùng
    nhỏ quanh `pos`, không quét lại toàn bộ `targets` trên cả màn hình."""
    end = time.monotonic() + timeout   # thời điểm hết hạn chờ
    # Các ảnh ứng với action này (nhiều ảnh có thể cùng 1 action, VD: TAP).
    paths = [path for path, act in targets if act == action]
    while True:
        delay(bot, interval)
        screen = bot.screenshot()
        # Không nhận ra màn hình nào (action None) -> không có gì để chờ.
        if action is None or pos is None:
            return screen
        # Màn hình đã đổi hoặc hết thời gian chờ -> trả về ảnh vừa chụp.
        if not _still_there(bot, screen, paths, pos, action in top_left, tolerance) \
                or time.monotonic() >= end:
            return screen


def _still_there(bot, screen, paths, pos, is_top_left, tolerance) -> bool:
    """Có ảnh nào trong `paths` còn nằm ở `pos` (tâm ảnh, hoặc góc trên-trái
    nếu `is_top_left`) trên `screen` không."""
    for path in paths:
        w, h = bot.template_size(path)
        # Góc trên-trái của ảnh lúc được nhận diện.
        x, y = pos if is_top_left else (pos[0] - w // 2, pos[1] - h // 2)
        # Chỉ dò trong vùng bằng ảnh, nới thêm `tolerance` pixel mỗi phía.
        region = bot.crop(screen, x - tolerance, y - tolerance, w + 2 * tolerance,
                          h + 2 * tolerance)
        if bot.find(path, screen=region) is not None:
            return True
    return False
