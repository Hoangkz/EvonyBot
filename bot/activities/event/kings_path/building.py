"""
building.py — bước chung sau khi bấm Go của các nhiệm vụ King's Path mở chức năng của một
công trình trong thành (City Tax: Chợ -> Tax; Patrol: Tường thành -> Patrol; Heal ...).
Giống mở menu doanh trại ở gather_troops/train_troop: chờ về thành -> bấm giữa màn hình (công
trình ở giữa) -> icon chức năng trong menu -> màn chức năng.
"""
from .constants import BUILDING_CENTER, GO_EXTRA_WAIT, MENU_TRIES, MENU_WAIT, SCREEN_WAIT


def open_building(bot, name: str, icon: str, screen: str) -> bool:
    """Sau Go: chờ thêm GO_EXTRA_WAIT giây (cùng GO_WAIT là 10 s) -> bấm giữa màn hình -> chờ
    MENU_WAIT giây -> thấy `icon` thì bấm, chờ màn có `screen`; không thấy icon thì bấm giữa
    thêm lần nữa (MENU_TRIES lần). True nếu đã vào màn chức năng."""
    bot.sleep(GO_EXTRA_WAIT)
    for _ in range(MENU_TRIES):
        bot.tap_percent(*BUILDING_CENTER, delay=MENU_WAIT)
        pos = bot.find(icon)
        if pos is not None:
            bot.tap(*pos)
            if bot.wait_for(screen, timeout=SCREEN_WAIT) is not None:
                return True
            bot.log(f"{name}: screen not shown after menu icon")
            return False
    bot.log(f"{name}: menu icon not found")
    return False
