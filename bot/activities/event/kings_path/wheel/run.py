"""
run.py — nhiệm vụ Wheel (King's Path, Day 4): Day 4 -> tab phụ "Fortune Wheel" -> Go
-> màn Wheel of Fortune -> quay. Flow chung tới Go: xem ../path_task.py.

Sau Go (mỗi bước chụp 1 ảnh, xét theo thứ tự):
1. Có nút "100 Spins" -> bấm -> Back -> đánh dấu xong (không kiểm tra gì thêm).
2. Màn Purchase Chips (game tự mở khi bấm 10 Spins mà không đủ chip) -> Back, đánh dấu xong
   hôm nay (mai làm tiếp).
3. Có nút "10 Spins" -> bấm liên tục (không cần đóng bảng kết quả) tới bước 2.
"""
from ...common import EventState
from .. import path_task
from .constants import (
    BUTTON_WAIT,
    CHIPS_TITLE,
    DAY,
    KEY,
    MAX_STEPS,
    SPIN_100_WAIT,
    SPIN_10_WAIT,
    SPINS_10,
    SPINS_100,
    SPINS_REGION,
    TAB,
    TAB_INDEX,
    TAB_SELECTED,
    WHEEL_WAIT,
)

NAME = "Wheel"


def _spin(bot, path, done, target):
    """Sau Go: 100 Spins nếu có; không thì 10 Spins liên tục tới khi hết chip."""
    spins_10, misses = 0, 0
    for _ in range(MAX_STEPS):
        screen = bot.screenshot()
        spin_100 = bot.find(SPINS_100, screen=screen, region=SPINS_REGION)
        if spin_100 is not None:
            bot.record(f"{NAME}: 100 Spins, back, done")
            bot.tap(*spin_100, delay=SPIN_100_WAIT)
            bot.back(delay=BUTTON_WAIT)
            bot.mark_daily_done(path.key)
            return
        if bot.find(CHIPS_TITLE, screen=screen) is not None:
            bot.record(f"{NAME}: out of chips after {spins_10} x 10 Spins, done for today")
            bot.back(delay=BUTTON_WAIT)
            bot.mark_daily_done(path.key)
            return
        spin_10 = bot.find(SPINS_10, screen=screen, region=SPINS_REGION)
        if spin_10 is not None:
            misses = 0
            spins_10 += 1
            bot.tap(*spin_10, delay=SPIN_10_WAIT)
            continue
        misses += 1
        if misses > WHEEL_WAIT:
            bot.record(f"{NAME}: Wheel of Fortune not shown")
            return
        bot.sleep(1)
    bot.record(f"{NAME}: too many steps ({spins_10} x 10 Spins), stop")


PATH = path_task.PathTask(
    key=KEY, name=NAME, day=DAY, tab_index=TAB_INDEX,
    tab_selected=TAB_SELECTED, tab=TAB, after_go=_spin,
)


def run(bot, task: dict, state: EventState):
    """`task` là settings của nhiệm vụ: {"value": int, "day": int}."""
    path_task.run(bot, task, state, PATH)
