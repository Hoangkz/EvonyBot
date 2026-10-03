"""
run.py — nhiệm vụ Heal (King's Path, Day 3): Day 3 -> tab phụ "Healing Heart" -> Go ->
Bệnh viện -> Heal / Speed Up -> làm lại từ đầu (đọc lại số đã heal). Flow chung tới Go: xem
../path_task.py.

Sau Go: bấm giữa màn hình (Bệnh viện) -> menu:
1. Có "Speed Up" (đang chữa dở): bấm -> màn Healing Speedup -> Finish All (như train lính) ->
   trả AGAIN.
2. Có "Heal" (rảnh): bấm -> màn Hospital: Reset (bỏ chọn hết, nút đổi thành Select All) -> cuộn
   danh sách xuống cuối LIST_SCROLLS lần (lính cấp thấp nhất ở dưới cùng) -> chọn nhiều dòng một
   lần, từ dòng dưới cùng lên: OCR số lính bị thương mỗi dòng ("0 / 8,147", ocr/read_heal_count.py),
   bấm ô số -> thanh nhập: gõ min(còn thiếu, số lính) -> OK; đủ số cần heal (mục tiêu - số đã heal,
   OCR ở dòng Go) hoặc hết dòng đang thấy thì thôi -> Heal -> Speed Up -> Finish All -> trả AGAIN
   (thiếu thì lượt sau heal tiếp).
AGAIN: không bấm giữa lại, đi lại từ màn chính -> Event Center -> King's Path -> Day 3 -> Healing
Heart -> OCR lại số đã heal -> đủ mục tiêu thì xong, chưa thì Go lần nữa (lặp tới khi đủ).
Không đọc được số đã heal ở dòng Go thì không heal (không biết cần bao nhiêu).
Hết lính bị thương -> Back, đánh dấu xong hôm nay (mai làm tiếp): menu Bệnh viện không có Speed
Up, không có Heal mà có Upgrade (chỉ Citizen / Detail / Upgrade — heal_menu_empty.png), hoặc màn
Hospital "Wounded Troops 0/0" không có dòng lính nào (heal_empty.png).
"""
from .....ocr import read_heal_count
from .....ocr.read_heal_count import CROP as HEAL_COUNT_CROP
from ...city_building import HOSPITAL
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
    EXTRA_WAIT,
    HEAL_BUTTON,
    HEAL_BUTTON_THRESHOLD,
    HEAL_WAIT,
    HOSPITAL_TITLE,
    INPUT_DELETES,
    INPUT_OK,
    INPUT_TRIES,
    INPUT_WAIT,
    KEY,
    LIST_SCROLLS,
    LIST_SWIPE,
    LIST_SWIPE_WAIT,
    MENU_HEAL,
    MENU_SPEED_UP,
    MENU_UPGRADE,
    MIN_DISMISS_Y,
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
    action, pos = open_menu(bot, NAME, HOSPITAL, {_SPEED_UP: MENU_SPEED_UP, _HEAL: MENU_HEAL,
                                        _EMPTY: MENU_UPGRADE})
    if action == _EMPTY:
        return _no_wounded(bot, path)
    if action == _SPEED_UP:
        bot.log(f"{NAME}: hospital busy, Speed Up")
        bot.tap(*pos, delay=EXTRA_WAIT)
        return path_task.AGAIN if _finish_all(bot) else None
    if action != _HEAL:
        return None
    if done is None:
        bot.record(f"{NAME}: progress unknown, not healing")
        return None
    bot.log(f"{NAME}: hospital idle, Heal (done {done}, target {target})")
    bot.tap(*pos, delay=EXTRA_WAIT)
    if bot.wait_for(HOSPITAL_TITLE, timeout=SCREEN_WAIT) is None:
        bot.record(f"{NAME}: Hospital screen not shown")
        return None
    if not bot.find_all(DISMISS):
        return _no_wounded(bot, path)
    _reset_and_scroll(bot)
    if not _heal_rows(bot, target - done):
        return None
    speed_up = bot.wait_for(SPEED_UP, timeout=SCREEN_WAIT)
    if speed_up is None:
        bot.record(f"{NAME}: Speed Up not shown after Heal")
        return path_task.AGAIN
    bot.tap(*speed_up, delay=EXTRA_WAIT)
    _finish_all(bot)
    return path_task.AGAIN


def _no_wounded(bot, path):
    """Không có lính bị thương: Back, đánh dấu xong hôm nay."""
    bot.record(f"{NAME}: no wounded troops, done for today")
    bot.back(delay=1 + EXTRA_WAIT)
    bot.mark_daily_done(path.key)
    return None


def _reset_and_scroll(bot):
    """Màn Hospital: còn nút Reset (đang chọn hết) thì bấm; rồi cuộn xuống cuối danh sách."""
    reset = bot.find(RESET)
    if reset is not None:
        bot.log(f"{NAME}: Reset selection")
        bot.tap(*reset, delay=1 + EXTRA_WAIT)
    for _ in range(LIST_SCROLLS):
        bot.swipe_percent(*LIST_SWIPE, duration=0.5, delay=LIST_SWIPE_WAIT)


def _heal_rows(bot, need: int) -> bool:
    """Chọn `need` lính từ dòng dưới cùng (cấp thấp nhất) lên trong các dòng đang thấy: OCR số lính
    bị thương mỗi dòng ("0 / 8,147"), gõ min(còn thiếu, số lính) vào ô số từng dòng cho tới khi đủ
    -> Heal. Không đọc được số của một dòng -> gõ hết phần còn thiếu vào dòng đó (game tự hạ về số
    lính có) rồi thôi. Hết dòng mà chưa đủ -> vẫn heal phần đã chọn; lượt AGAIN đọc lại tiến độ rồi
    heal tiếp. True nếu đã bấm Heal."""
    screen = bot.screenshot()
    rows = sorted((p for p in bot.find_all(DISMISS, screen=screen) if p[1] >= MIN_DISMISS_Y),
                  key=lambda p: p[1], reverse=True)
    if not rows:
        bot.record(f"{NAME}: troop rows not found")
        return False
    dx, dy, w, h = HEAL_COUNT_CROP
    # Đọc hết trước khi gõ: gõ số làm đổi số bên trái "/", số bên phải giữ nguyên.
    counts = [read_heal_count(bot.crop(screen, x + dx, y + dy, w, h)) for x, y in rows]
    remaining, picked = need, 0
    for (x, y), count in zip(rows, counts):
        amount = remaining if count is None else min(remaining, count)
        if amount <= 0:
            continue
        if not _enter_amount(bot, x, y, amount):
            break
        picked += 1
        bot.log(f"{NAME}: row {picked}: {amount} of {count if count is not None else '?'} troops")
        if count is None:
            remaining = 0   # không biết dòng có bao nhiêu: lượt AGAIN đọc lại tiến độ
            break
        remaining -= amount
        if remaining <= 0:
            break
    if not picked:
        return False
    bot.record(f"{NAME}: heal {need - remaining} / {need} troops in {picked} row(s)")
    heal = bot.find(HEAL_BUTTON, threshold=HEAL_BUTTON_THRESHOLD)
    if heal is None:
        bot.record(f"{NAME}: Heal button not found")
        return False
    bot.tap(*heal, delay=HEAL_WAIT + EXTRA_WAIT)
    return True


def _enter_amount(bot, x: int, y: int, amount: int) -> bool:
    """Dòng có nút Dismiss tại (x, y): bấm ô số -> thanh nhập: xoá số cũ, gõ `amount` -> OK."""
    ax, ay = x + DISMISS_TO_AMOUNT[0], y + DISMISS_TO_AMOUNT[1]
    ok = None
    for _ in range(INPUT_TRIES):
        bot.tap(ax, ay, delay=EXTRA_WAIT)
        ok = bot.wait_for(INPUT_OK, timeout=INPUT_WAIT)
        if ok is not None:
            break
    if ok is None:
        bot.record(f"{NAME}: amount input not shown (tapped {ax}, {ay} x{INPUT_TRIES})")
        return False
    for _ in range(INPUT_DELETES):
        bot.shell("input keyevent KEYCODE_DEL")
    bot.shell(f"input text {amount}")
    bot.sleep(EXTRA_WAIT)
    bot.tap(*ok, delay=1 + EXTRA_WAIT)
    return True


def _finish_all(bot) -> bool:
    """Màn Healing Speedup (như train lính): lần đầu Speedup Settings -> hộp Finish All: tích ô nếu
    chưa tích -> Confirm; rồi Finish All. True nếu đã bấm Finish All."""
    if bot.wait_for(SPEEDUP_TITLE, timeout=SCREEN_WAIT) is None:
        bot.record(f"{NAME}: Healing Speedup screen not shown")
        return False
    settings_done = False
    for _ in range(SPEEDUP_STEPS):
        screen = bot.screenshot()
        if bot.find(FINISH_ALL_TITLE, screen=screen) is not None:
            box = bot.find(CHECKBOX_OFF, screen=screen)
            if box is not None:
                bot.tap(*box, delay=1 + EXTRA_WAIT)
            bot.tap(*_pos_of(bot, bot.screenshot(), CONFIRM, CONFIRM_POS), delay=SPEEDUP_WAIT + EXTRA_WAIT)
            settings_done = True
        elif bot.find(SPEEDUP_TITLE, screen=screen) is not None:
            if not settings_done:
                bot.tap(*_pos_of(bot, screen, SPEEDUP_SETTINGS, SPEEDUP_SETTINGS_POS), delay=SPEEDUP_WAIT + EXTRA_WAIT)
                continue
            bot.log(f"{NAME}: Finish All")
            bot.tap(*_pos_of(bot, screen, FINISH_ALL, FINISH_ALL_POS), delay=SPEEDUP_WAIT + EXTRA_WAIT)
            return True
        else:
            bot.log(f"{NAME}: left Healing Speedup screen")
            return False
    bot.record(f"{NAME}: Finish All not reached")
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
