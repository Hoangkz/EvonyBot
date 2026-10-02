"""
get_server.py — lấy số server của tài khoản (dòng "Empire Name: S. 1257").
"""
from ..ocr import read_server
from .click_images import click_images
from .delay import delay
from .exit_images import exit_images
from .find_first import find_first
from .go_home import go_home

EMPIRE_NAME = "Server/empireName.png"
FOUND = "found"
TAP = "tap"
BACK = "back"
MAX_ROUNDS = 30     # số vòng tối đa trước khi bỏ cuộc (lần chạy activity sau thử lại)


def _targets() -> list[tuple[str, str]]:
    """(ảnh, action); ảnh đứng trước được ưu tiên hơn."""
    return [
        *[(path, BACK) for path in exit_images()],
        *[(path, TAP) for path in click_images()],
        (EMPIRE_NAME, FOUND),                   # dòng "Empire Name:" -> đọc server
        ("Server/account.png", TAP),
        ("Server/setting.png", TAP),
        ("Server/listActivity.png", TAP),
    ]


def get_server(bot) -> str | None:
    """Mở màn hình thông tin tài khoản và đọc số server (VD: "1257"): thấy
    "Empire Name:" thì đọc số sau "S."; thấy các nút trên đường đi thì bấm
    vào; không thấy gì thì go_home. Trả về None nếu sau MAX_ROUNDS vòng vẫn
    không đọc được."""
    targets = _targets()
    screen = bot.screenshot()
    for _ in range(MAX_ROUNDS):
        action, pos = find_first(bot, screen, targets, top_left={FOUND})
        if action == FOUND:
            # Vùng ngay bên phải chữ "Empire Name:" chứa "S. <server>".
            w, h = bot.template_size(EMPIRE_NAME)
            server = read_server(bot.crop(screen, pos[0] + w, pos[1], 80, h))
            if server is not None:
                bot.log(f"Server: {server}")
                return server
            # Chưa đọc được (có thể màn hình đang chuyển) -> chụp lại.
            delay(bot, 0.5)
            screen = bot.screenshot()
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
    bot.log("Server: không đọc được")
    return None
