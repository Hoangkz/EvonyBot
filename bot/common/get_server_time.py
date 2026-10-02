"""
get_server_time.py — mở menu hoạt động, đọc thời gian đã trôi qua và đổi
thành thời điểm reset theo giờ máy.
"""
from datetime import datetime

from ..ocr import read_server_time
from .click_images import click_images
from .delay import delay
from .exit_images import exit_images
from .find_first import find_first
from .go_home import go_home

SERVER_TIME = "Server/serverTime.png"
FOUND = "found"
TAP = "tap"
BACK = "back"
MAX_ROUNDS = 30     # số vòng tối đa trước khi bỏ cuộc (lần chạy activity sau thử lại)
VALUE_WIDTH = 190   # Đủ cho YYYY-MM-DD HH:MM:SS ở cỡ chữ của ảnh mẫu.


def _targets() -> list[tuple[str, str]]:
    """(ảnh, action); ảnh đứng trước được ưu tiên hơn."""
    return [
        *[(path, BACK) for path in exit_images()],
        *[(path, TAP) for path in click_images()],
        (SERVER_TIME, FOUND),                   # nhãn thời gian ở đầu menu -> đọc time
        ("Server/setting.png", TAP),
        ("Server/listActivity.png", TAP),
    ]


def get_server_time(bot) -> str | None:
    """Mở menu hoạt động và đọc thời gian server: thấy nhãn thời gian thì
    đọc phần bên phải rồi tính thời điểm reset; thấy nút listActivity thì
    bấm vào; không thấy gì thì go_home. Trả về None nếu sau MAX_ROUNDS vòng
    vẫn không đọc được (worker thử lại trước activity sau)."""
    targets = _targets()
    # Nhãn ở đầu menu; lấy góc trái để cắt chính xác phần bên phải.
    regions = {SERVER_TIME: (0, 0, 100, 30)}
    screen = bot.screenshot()
    observed_at = datetime.now()
    for _ in range(MAX_ROUNDS):
        action, pos = find_first(bot, screen, targets, top_left={FOUND}, regions=regions)
        if action == FOUND:
            w, h = bot.template_size(SERVER_TIME)
            elapsed = read_server_time(bot.crop(screen, pos[0] + w, pos[1], VALUE_WIDTH, h))
            if elapsed is not None:
                # Ví dụ 12:00 - 04:30 = 07:30; phép trừ tự xử lý lùi về ngày trước.
                reset_at = (observed_at - elapsed).isoformat(timespec="seconds")
                bot.log(f"Server reset: {reset_at}")
                return reset_at
            # Chưa đọc được (có thể màn hình đang chuyển) -> chụp lại.
            delay(bot, 0.5)
            screen = bot.screenshot()
            observed_at = datetime.now()
            continue
        if action == TAP:
            bot.tap(*pos)
            # Nút có thể vẫn còn khi popup mở: chờ 2 giây rồi chụp lại.
            delay(bot, 2)
        elif action == BACK:
            bot.back()
            delay(bot, 1)
        else:
            # Không thấy ảnh nào -> về màn hình chính.
            go_home(bot, screen)
            delay(bot, 0.3)
        # Dùng ảnh mới để nhận diện ở vòng lặp tiếp theo.
        screen = bot.screenshot()
        observed_at = datetime.now()
    bot.log("Server time: không đọc được")
    return None
