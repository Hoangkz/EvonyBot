"""
run.py — nhiệm vụ Donate (King's Path, Day 2): Day 2 -> tab phụ "Teamwork" -> dòng
"Donate to the Alliance" -> Go -> màn Alliance Science -> bấm Donate cho đủ mục tiêu.
Flow chung tới Go: xem ../path_task.py.

Sau Go (màn Alliance Science):
- Hộp "Spend N Gems on clearing the Cooldown?" -> Okay.
- Nút "Donate" -> bấm, đếm 1 lần. Đủ (mục tiêu - số đã làm) lần -> đánh dấu xong.
- Hết lượt (nút kim cương) -> bấm để mua lại lượt, tối đa MAX_GEM_BUYS (4) lần; quá thì dừng.
Không đọc được số đã làm ở dòng Go thì không donate (không biết lúc nào dừng, tránh tiêu
kim cương). Bị ngắt giữa chừng: lượt sau đọc lại số đã làm ở dòng Go rồi làm tiếp.
"""
from ...common import EventState
from .. import path_task
from .constants import (
    DAY,
    DONATE_BUTTON,
    DONATE_WAIT,
    GEMS_BUTTON,
    GEMS_WAIT,
    KEY,
    MAX_GEM_BUYS,
    MAX_MISSES,
    OKAY,
    ROW_TITLE,
    SCIENCE_TITLE,
    SCIENCE_WAIT,
    TAB,
    TAB_INDEX,
    TAB_SELECTED,
)

NAME = "Donate"


def _donate(bot, path, done, target):
    """Sau Go: donate (mục tiêu - số đã làm) lần ở màn Alliance Science."""
    if done is None:
        bot.log(f"{NAME}: progress unknown, not donating")
        return
    need = target - done
    if bot.wait_for(SCIENCE_TITLE, timeout=SCIENCE_WAIT) is None:
        bot.log(f"{NAME}: Alliance Science not shown")
        return
    donated = gem_buys = misses = 0
    while donated < need:
        action, pos = _read_screen(bot, bot.screenshot())
        if action is None:
            misses += 1
            if misses > MAX_MISSES:
                bot.log(f"{NAME}: screen not recognised, stop ({donated}/{need})")
                return
            bot.sleep(1)
            continue
        misses = 0
        if action == "okay":
            bot.tap(*pos, delay=GEMS_WAIT)
        elif action == "donate":
            bot.tap(*pos, delay=DONATE_WAIT)
            donated += 1
        else:
            if gem_buys >= MAX_GEM_BUYS:
                bot.log(f"{NAME}: bought donations {MAX_GEM_BUYS} times, stop ({donated}/{need})")
                return
            gem_buys += 1
            bot.log(f"{NAME}: out of donations, buy with gems ({gem_buys}/{MAX_GEM_BUYS})")
            bot.tap(*pos, delay=GEMS_WAIT)
    bot.log(f"{NAME}: donated {donated}, done")
    bot.mark_daily_done(path.key)


def _read_screen(bot, screen):
    """(action, vị trí) trên màn Alliance Science: "okay" (hộp xác nhận), "donate" /
    "gems" (nút của thẻ khoa học trên cùng); (None, None) nếu không phải màn đó."""
    if bot.find(SCIENCE_TITLE, screen=screen) is None:
        return None, None
    okay = bot.find(OKAY, screen=screen)
    if okay is not None:
        return "okay", okay
    for action, template in (("donate", DONATE_BUTTON), ("gems", GEMS_BUTTON)):
        points = bot.find_all(template, screen=screen)
        if points:
            return action, min(points, key=lambda p: p[1])
    return None, None


PATH = path_task.PathTask(
    key=KEY, name=NAME, day=DAY, tab_index=TAB_INDEX,
    tab_selected=TAB_SELECTED, tab=TAB,
    row_title=ROW_TITLE, after_go=_donate,
)


def run(bot, task: dict, state: EventState):
    """`task` là settings của nhiệm vụ: {"value": int, "day": int}."""
    path_task.run(bot, task, state, PATH)
