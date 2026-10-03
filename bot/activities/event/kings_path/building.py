"""
building.py — bước chung sau khi bấm Go của các nhiệm vụ King's Path mở chức năng của một
công trình trong thành (City Tax: Chợ -> Tax; Patrol: Tường thành -> Patrol; Heal: Bệnh viện ->
Heal / Speed Up). Giống mở menu doanh trại ở gather_troops/train_troop: chờ về thành -> bấm giữa
màn hình (công trình ở giữa) -> icon chức năng trong menu -> màn chức năng.
"""
from .constants import BUILDING_CENTER, GO_EXTRA_WAIT, MENU_TRIES, MENU_WAIT, SCREEN_WAIT


def open_menu(bot, name: str, icons: dict[str, str]):
    """Sau Go: chờ thêm GO_EXTRA_WAIT giây (cùng GO_WAIT là 10 s) -> bấm giữa màn hình -> chờ
    MENU_WAIT giây -> tìm các icon `icons` ({tên: ảnh}, xét theo thứ tự); không thấy icon nào
    thì bấm giữa thêm lần nữa (MENU_TRIES lần). Trả (tên, vị trí) icon đầu tiên thấy, hoặc
    (None, None)."""
    bot.sleep(GO_EXTRA_WAIT)
    for _ in range(MENU_TRIES):
        bot.tap_percent(*BUILDING_CENTER, delay=MENU_WAIT)
        screen = bot.screenshot()
        for key, icon in icons.items():
            pos = bot.find(icon, screen=screen)
            if pos is not None:
                return key, pos
    bot.record(f"{name}: menu icon not found")
    return None, None


def open_building(bot, name: str, icon: str, screen: str) -> bool:
    """open_menu với một icon: thấy thì bấm, chờ màn có `screen` (tối đa SCREEN_WAIT giây).
    True nếu đã vào màn chức năng."""
    _, pos = open_menu(bot, name, {"icon": icon})
    if pos is None:
        return False
    bot.tap(*pos)
    if bot.wait_for(screen, timeout=SCREEN_WAIT) is not None:
        return True
    bot.record(f"{name}: screen not shown after menu icon")
    return False
