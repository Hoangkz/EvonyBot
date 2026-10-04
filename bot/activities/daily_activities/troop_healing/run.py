"""
run.py — Daily Activities "Troop Heading": handler các action riêng của nhiệm vụ (Bệnh viện -> Heal (nhãn Troop Heading giữ như bản C# / tab UI)).
Vòng lặp chung (mở Activity, dòng Go, cuộn, ảnh xong): ../common.py run_task.

Luồng mới (after_go, sau khi open_task bấm Go) giống King's Path Heal (event/kings_path/heal), dùng lại các
bước của nó (Reset + cuộn, chọn số lính từng dòng bằng OCR, Healing Speedup -> Finish All):
1. Bệnh viện ở giữa -> menu Bệnh viện:
   - "Speed Up" (đang chữa dở) -> Healing Speedup -> Finish All -> mở lại menu (tối đa MENU_ROUNDS lần);
   - "Heal" -> màn Hospital; không có Speed Up / Heal mà có "Upgrade" -> không có lính bị thương.
2. Màn Hospital: không có dòng lính -> không có lính bị thương. Có: Reset -> cuộn xuống cuối -> chọn
   HEAL_GOAL lính từ dòng dưới cùng (cấp thấp nhất) lên -> Heal -> Speed Up -> Finish All.
3. Heal xong -> đánh dấu xong hôm nay. Không có lính bị thương -> Back, cũng đánh dấu xong hôm nay (mai
   kiểm tra lại; ít hơn HEAL_GOAL thì heal hết số có).
"""
from ....common import delay
from ...event.city_building import HOSPITAL
from ...event.kings_path.building import open_menu
from ...event.kings_path.constants import SCREEN_WAIT
from ...event.kings_path.heal.constants import (
    DISMISS,
    EXTRA_WAIT,
    HOSPITAL_TITLE,
    MENU_HEAL,
    MENU_SPEED_UP,
    MENU_UPGRADE,
    SPEED_UP,
)
from ...event.kings_path.heal.run import _finish_all, _heal_rows, _reset_and_scroll
from ..common import Task, mark_task_done, replace_text
from .constants import ACTIONS, DONE_IMAGES, FOLDER, HEAL_GOAL, KEY, LABEL, MENU_ROUNDS

_SPEED_UP, _HEAL, _EMPTY = "speed_up", "heal", "empty"


def handle(bot, action, pos, screen):
    if action == "heal_all":
        bot.tap(*pos, delay=4)
    elif action == "select":
        bot.tap(*pos, delay=2)
        replace_text(bot, "150", 1)
        delay(bot, 2)
        bot.tap(330, 670, delay=4)
        bot.tap(330, 670, delay=2)
    elif action == "heal_info":
        bot.tap(*pos, delay=2)
        bot.swipe_percent(65, 70, 65, 60, duration=1.0, delay=1)
        bot.swipe_percent(65, 70, 65, 60, duration=1.0, delay=1)
    return False


def after_go(bot) -> bool:
    """Luồng mới, sau khi open_task bấm Go: heal HEAL_GOAL lính ở Bệnh viện (giống King's Path Heal).
    True nếu xong hôm nay (đã heal, hoặc không có lính bị thương); False nếu lỗi."""
    for _ in range(MENU_ROUNDS):
        # Upgrade có cả ở menu rảnh -> xét sau cùng: không có Speed Up, không có Heal mà có Upgrade.
        action, pos = open_menu(bot, LABEL, HOSPITAL, {_SPEED_UP: MENU_SPEED_UP, _HEAL: MENU_HEAL,
                                                       _EMPTY: MENU_UPGRADE})
        if action == _EMPTY:
            return _no_wounded(bot)
        if action == _SPEED_UP:
            bot.log(f"{LABEL}: hospital busy, Speed Up first")
            bot.tap(*pos, delay=EXTRA_WAIT)
            if not _finish_all(bot):
                return False
            continue   # mở lại menu Bệnh viện (công trình vẫn ở giữa)
        if action != _HEAL:
            return False
        return _heal(bot, pos)
    bot.record(f"{LABEL}: hospital still busy after {MENU_ROUNDS} rounds")
    return False


def _heal(bot, pos) -> bool:
    """Menu Bệnh viện rảnh: Heal -> màn Hospital -> chọn HEAL_GOAL lính -> Heal -> Speed Up -> Finish All."""
    bot.log(f"{LABEL}: Heal {HEAL_GOAL} troops")
    bot.tap(*pos, delay=EXTRA_WAIT)
    if bot.wait_for(HOSPITAL_TITLE, timeout=SCREEN_WAIT) is None:
        bot.record(f"{LABEL}: Hospital screen not shown")
        return False
    if not bot.find_all(DISMISS):
        return _no_wounded(bot)
    _reset_and_scroll(bot)
    if not _heal_rows(bot, HEAL_GOAL):
        return False
    speed_up = bot.wait_for(SPEED_UP, timeout=SCREEN_WAIT)
    if speed_up is None:
        bot.record(f"{LABEL}: Speed Up not shown after Heal")
    else:
        bot.tap(*speed_up, delay=EXTRA_WAIT)
        _finish_all(bot)
    mark_task_done(bot, TASK)
    return True


def _no_wounded(bot) -> bool:
    """Không có lính bị thương: Back, đánh dấu xong hôm nay."""
    bot.record(f"{LABEL}: no wounded troops, done for today")
    bot.back(delay=1 + EXTRA_WAIT)
    mark_task_done(bot, TASK)
    return True


TASK = Task(LABEL, FOLDER, DONE_IMAGES, ACTIONS, handle, key=KEY)
