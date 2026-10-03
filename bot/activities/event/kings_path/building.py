"""
building.py — bước chung sau khi bấm Go của các nhiệm vụ King's Path mở chức năng của một
công trình trong thành (City Tax: Chợ -> Tax; Patrol: Tường thành -> Patrol; Heal: Bệnh viện ->
Heal / Speed Up). Giống mở menu doanh trại ở gather_troops/train_troop: chờ về thành -> nhận ra
công trình bằng ảnh đã học / học ảnh mới (../city_building.py) -> bấm giữa -> icon chức năng
trong menu -> màn chức năng.
"""
from ..city_building import remember_building, tap_building
from .constants import MENU_TRIES, MENU_WAIT, SCREEN_WAIT


def open_menu(bot, name: str, building: str, icons: dict[str, str]):
    """Sau Go: tap_building (tìm ảnh học của `building`, bấm giữa, chờ MENU_WAIT giây) -> tìm
    các icon `icons` ({tên: ảnh}, xét theo thứ tự). Thấy icon thì lưu ảnh công trình nếu chưa
    nhận ra (remember_building); không thấy icon nào thì làm lại (MENU_TRIES lần). Trả (tên,
    vị trí) icon đầu tiên thấy, hoặc (None, None)."""
    for _ in range(MENU_TRIES):
        tap = tap_building(bot, name, building, delay=MENU_WAIT)
        screen = bot.screenshot()
        for key, icon in icons.items():
            pos = bot.find(icon, screen=screen)
            if pos is not None:
                remember_building(bot, name, tap)
                return key, pos
    bot.record(f"{name}: menu icon not found")
    return None, None


def open_building(bot, name: str, building: str, icon: str, screen: str) -> bool:
    """open_menu với một icon: thấy thì bấm, chờ màn có `screen` (tối đa SCREEN_WAIT giây).
    True nếu đã vào màn chức năng."""
    _, pos = open_menu(bot, name, building, {"icon": icon})
    if pos is None:
        return False
    bot.tap(*pos)
    if bot.wait_for(screen, timeout=SCREEN_WAIT) is not None:
        return True
    bot.record(f"{name}: screen not shown after menu icon")
    return False
