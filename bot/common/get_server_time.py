"""Mở menu hoạt động, đọc thời gian đã trôi qua và đổi thành thời điểm reset theo giờ máy."""
from datetime import datetime

from ..ocr import read_server_time
from .delay import delay
from .go_home import go_home

SERVER_TIME = "Server/serverTime.png"
LIST_ACTIVITY = "Server/listActivity.png"
MAX_ROUNDS = 30
VALUE_WIDTH = 190  # Đủ cho YYYY-MM-DD HH:MM:SS ở cỡ chữ của ảnh mẫu.


def get_server_time(bot) -> str | None:
    """Chưa đọc được thì trả None để worker thử lại trước activity sau."""
    for _ in range(MAX_ROUNDS):
        screen = bot.screenshot()
        observed_at = datetime.now()
        # Nhãn ở đầu menu; lấy góc trái để cắt chính xác phần bên phải.
        pos = bot.find(SERVER_TIME, screen=screen, center=False, region=(0, 0, 100, 30))
        if pos is not None:
            w, h = bot.template_size(SERVER_TIME)
            value = bot.crop(screen, pos[0] + w, pos[1], VALUE_WIDTH, h)
            elapsed = read_server_time(value)
            if elapsed is not None:
                # Ví dụ 12:00 - 04:30 = 07:30; phép trừ tự xử lý lùi về ngày trước.
                reset_at = (observed_at - elapsed).isoformat(timespec="seconds")
                bot.log(f"Server reset: {reset_at}")
                return reset_at
            # Menu có thể đang chuyển cảnh: chờ rồi chụp lại, không lưu OCR lỗi.
            delay(bot, 0.5)
            continue

        pos = bot.find(LIST_ACTIVITY, screen=screen)
        if pos is not None:
            bot.tap(*pos)
            # Chỉ mở popup, nút vẫn còn: chờ 2 giây rồi vòng sau chụp lại.
            delay(bot, 2)
        else:
            go_home(bot, screen)
            delay(bot, 0.5)
    bot.log("Server time: không đọc được")
    return None
