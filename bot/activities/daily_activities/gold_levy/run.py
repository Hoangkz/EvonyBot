"""
run.py — Daily Activities "Gold Levy": phần làm nhiệm vụ sau Go (after_go) (Thành chính (Keep) -> Levy).
Mở dòng Activity + bấm Go: ../common.py (open_task_or_finish, daily_job).

Sau Go: menu tròn của Thành chính -> "Levy" -> popup Levy -> bấm "Free Levy All" -> báo xong hôm nay
-> Back đóng popup. Nút đã xám (hết lượt free) cũng coi là xong.
"""
from ...event.city_building import KEEP
from ...event.kings_path.building import open_menu
from ...result import done as report_done
from ..common import Task, mark_task_done
from .constants import BACKS_AFTER_LEVY, FOLDER, FOLDER_PATH, KEY, LABEL, LEVY_ALL_WAIT, POPUP_WAIT

FREE_LEVY_ALL = f"{FOLDER_PATH}/FreeLevyAll.png"
FREE_LEVY_ALL_DONE = f"{FOLDER_PATH}/FreeLevyAllDone.png"
POPUP_BUTTONS = (FREE_LEVY_ALL, FREE_LEVY_ALL_DONE)
MENU_LEVY = f"{FOLDER_PATH}/Levy.png"


def after_go(bot) -> bool:
    """Luồng mới, sau khi open_task bấm Go (hai phiên bản giống nhau từ đây): Thành chính ở giữa ->
    open_menu (nhận ra / tự học ảnh công trình, icon "Levy") -> popup Levy (chờ tối đa POPUP_WAIT giây):
    "Free Levy All" vàng -> bấm; xám (hết lượt free) -> không bấm. Cả hai: xong hôm nay, Back đóng popup.
    False nếu không mở được popup Levy."""
    _, pos = open_menu(bot, LABEL, KEEP, {"levy": MENU_LEVY})
    if pos is None:
        return False
    bot.tap(*pos, delay=2)
    for _ in range(POPUP_WAIT):
        screen = bot.screenshot()
        button = bot.find(FREE_LEVY_ALL, screen=screen)
        if button is not None:
            bot.tap(*button, delay=LEVY_ALL_WAIT)
            bot.record(f"{LABEL}: Free Levy All")
            break
        if bot.find(FREE_LEVY_ALL_DONE, screen=screen) is not None:
            bot.log(f"{LABEL}: Free Levy All already used")
            break
        bot.sleep(1)
    else:
        bot.record(f"{LABEL}: Levy popup not shown")
        return False
    _finish(bot)
    mark_task_done(bot, TASK)
    return True


def _finish(bot) -> bool:
    """Báo xong hôm nay rồi Back tới khi popup Levy đóng."""
    report_done(bot, label=LABEL, key=KEY)
    for _ in range(BACKS_AFTER_LEVY):
        screen = bot.screenshot()
        if all(bot.find(path, screen=screen) is None for path in POPUP_BUTTONS):
            break
        bot.back(delay=2)
    return True


TASK = Task(LABEL, FOLDER, key=KEY)
