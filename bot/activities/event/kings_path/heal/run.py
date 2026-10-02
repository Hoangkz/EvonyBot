"""
run.py — nhiệm vụ Heal (King's Path, Day 3): Day 3 -> tab phụ "Healing Heart" -> Go ->
Bệnh viện -> Heal / Speed Up -> làm lại từ đầu (đọc lại số đã heal). Flow chung tới Go: xem
../path_task.py.

Sau Go: bấm giữa màn hình (Bệnh viện) -> menu:
1. Có "Speed Up" (đang chữa dở): bấm -> màn Healing Speedup -> Finish All (như train lính) ->
   trả AGAIN.
2. Có "Heal" (rảnh): bấm -> màn Hospital: Reset (bỏ chọn hết, nút đổi thành Select All) -> cuộn
   danh sách xuống cuối LIST_SCROLLS lần (lính cấp thấp nhất ở dưới cùng) -> bấm ô số dòng cuối ->
   thanh nhập: gõ số cần heal (mục tiêu - số đã heal, OCR ở dòng Go; gõ số tối đa, game tự hạ về
   số lính có) -> OK -> Heal -> Speed Up -> Finish All -> trả AGAIN.
AGAIN: không bấm giữa lại, đi lại từ màn chính -> Event Center -> King's Path -> Day 3 -> Healing
Heart -> OCR lại số đã heal -> đủ mục tiêu thì xong, chưa thì Go lần nữa (lặp tới khi đủ).
Không đọc được số đã heal ở dòng Go thì không heal (không biết cần bao nhiêu).
Hết lính bị thương -> Back, đánh dấu xong hôm nay (mai làm tiếp): menu Bệnh viện không có Speed
Up, không có Heal mà có Upgrade (chỉ Citizen / Detail / Upgrade — heal_menu_empty.png), hoặc màn
Hospital "Wounded Troops 0/0" không có dòng lính nào (heal_empty.png).
"""
from ...common import EventState
from ...gather_troops.train_troop.constants import (
    CHECKBOX_OFF,
    CONFIRM,
    CONFIRM_POS,
    FINISH_ALL,
    FINISH_ALL_POS,
    FINISH_ALL_TITLE,
    SPEEDUP_SETTINGS,
    SPEEDUP_SETTINGS_POS,
)
from .. import path_task
from ..building import open_menu
from ..constants import SCREEN_WAIT
from .constants import (
    DAY,
    DISMISS,
    DISMISS_TO_AMOUNT,
    HEAL_BUTTON,
    HEAL_BUTTON_THRESHOLD,
    HEAL_WAIT,
    HOSPITAL_TITLE,
    INPUT_DELETES,
    INPUT_OK,
    INPUT_WAIT,
    KEY,
    LIST_SCROLLS,
    LIST_SWIPE,
    MENU_HEAL,
    MENU_SPEED_UP,
    MENU_UPGRADE,
    RESET,
    SPEED_UP,
    SPEEDUP_STEPS,
    SPEEDUP_TITLE,
    SPEEDUP_WAIT,
    TAB,
    TAB_INDEX,
    TAB_SELECTED,
)

NAME = "Heal"
_SPEED_UP, _HEAL, _EMPTY = "speed_up", "heal", "empty"


def _heal(bot, path, done, target):
    """Sau Go: menu Bệnh viện -> Speed Up hoặc Heal; xong trả AGAIN (đọc lại tiến độ)."""
    # Upgrade có cả ở menu rảnh -> xét sau cùng: không có Speed Up, không có Heal mà có Upgrade.
    action, pos = open_menu(bot, NAME, {_SPEED_UP: MENU_SPEED_UP, _HEAL: MENU_HEAL,
                                        _EMPTY: MENU_UPGRADE})
    if action == _EMPTY:
        return _no_wounded(bot, path)
    if action == _SPEED_UP:
        bot.log(f"{NAME}: hospital busy, Speed Up")
        bot.tap(*pos)
        return path_task.AGAIN if _finish_all(bot) else None
    if action != _HEAL:
        return None
    if done is None:
        bot.log(f"{NAME}: progress unknown, not healing")
        return None
    bot.log(f"{NAME}: hospital idle, Heal (done {done}, target {target})")
    bot.tap(*pos)
    if bot.wait_for(HOSPITAL_TITLE, timeout=SCREEN_WAIT) is None:
        bot.log(f"{NAME}: Hospital screen not shown")
        return None
    if not bot.find_all(DISMISS):
        return _no_wounded(bot, path)
    _reset_and_scroll(bot)
    if not _heal_lowest(bot, target - done):
        return None
    speed_up = bot.wait_for(SPEED_UP, timeout=SCREEN_WAIT)
    if speed_up is None:
        bot.log(f"{NAME}: Speed Up not shown after Heal")
        return path_task.AGAIN
    bot.tap(*speed_up)
    _finish_all(bot)
    return path_task.AGAIN


def _no_wounded(bot, path):
    """Không có lính bị thương: Back, đánh dấu xong hôm nay."""
    bot.log(f"{NAME}: no wounded troops, done for today")
    bot.back(delay=1)
    bot.mark_daily_done(path.key)
    return None


def _reset_and_scroll(bot):
    """Màn Hospital: còn nút Reset (đang chọn hết) thì bấm; rồi cuộn xuống cuối danh sách."""
    reset = bot.find(RESET)
    if reset is not None:
        bot.log(f"{NAME}: Reset selection")
        bot.tap(*reset, delay=1)
    for _ in range(LIST_SCROLLS):
        bot.swipe_percent(*LIST_SWIPE, duration=0.5, delay=1)


def _heal_lowest(bot, count: int) -> bool:
    """Bấm ô số dòng lính cuối (cấp thấp nhất) -> gõ `count` -> OK -> Heal. True nếu đã bấm Heal."""
    dismisses = bot.find_all(DISMISS)
    if not dismisses:
        bot.log(f"{NAME}: troop rows not found")
        return False
    x, y = max(dismisses, key=lambda p: p[1])
    dx, dy = DISMISS_TO_AMOUNT
    bot.log(f"{NAME}: heal {count} lowest-tier troops")
    bot.tap(x + dx, y + dy)
    ok = bot.wait_for(INPUT_OK, timeout=INPUT_WAIT)
    if ok is None:
        bot.log(f"{NAME}: amount input not shown")
        return False
    for _ in range(INPUT_DELETES):
        bot.shell("input keyevent KEYCODE_DEL")
    bot.shell(f"input text {count}")
    bot.tap(*ok, delay=1)
    heal = bot.find(HEAL_BUTTON, threshold=HEAL_BUTTON_THRESHOLD)
    if heal is None:
        bot.log(f"{NAME}: Heal button not found")
        return False
    bot.tap(*heal, delay=HEAL_WAIT)
    return True


def _finish_all(bot) -> bool:
    """Màn Healing Speedup (như train lính): lần đầu Speedup Settings -> hộp Finish All: tích ô nếu
    chưa tích -> Confirm; rồi Finish All. True nếu đã bấm Finish All."""
    if bot.wait_for(SPEEDUP_TITLE, timeout=SCREEN_WAIT) is None:
        bot.log(f"{NAME}: Healing Speedup screen not shown")
        return False
    settings_done = False
    for _ in range(SPEEDUP_STEPS):
        screen = bot.screenshot()
        if bot.find(FINISH_ALL_TITLE, screen=screen) is not None:
            box = bot.find(CHECKBOX_OFF, screen=screen)
            if box is not None:
                bot.tap(*box, delay=1)
            bot.tap(*_pos_of(bot, bot.screenshot(), CONFIRM, CONFIRM_POS), delay=SPEEDUP_WAIT)
            settings_done = True
        elif bot.find(SPEEDUP_TITLE, screen=screen) is not None:
            if not settings_done:
                bot.tap(*_pos_of(bot, screen, SPEEDUP_SETTINGS, SPEEDUP_SETTINGS_POS), delay=SPEEDUP_WAIT)
                continue
            bot.log(f"{NAME}: Finish All")
            bot.tap(*_pos_of(bot, screen, FINISH_ALL, FINISH_ALL_POS), delay=SPEEDUP_WAIT)
            return True
        else:
            bot.log(f"{NAME}: left Healing Speedup screen")
            return False
    bot.log(f"{NAME}: Finish All not reached")
    return False


def _pos_of(bot, screen, template, fallback):
    """Tâm `template` trên `screen`, không thấy thì toạ độ đo sẵn `fallback`."""
    pos = bot.find(template, screen=screen)
    return fallback if pos is None else pos


PATH = path_task.PathTask(
    key=KEY, name=NAME, day=DAY, tab_index=TAB_INDEX,
    tab_selected=TAB_SELECTED, tab=TAB, after_go=_heal,
)


def run(bot, task: dict, state: EventState):
    """`task` là settings của nhiệm vụ: {"value": int, "day": int}."""
    path_task.run(bot, task, state, PATH)
