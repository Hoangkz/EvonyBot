"""Hoạt động Super Value Return độc lập với Valuable Event."""
from ....common import to_city
from .. import scan
from ..common import on_main, return_home
from ..screens import GiftScreen, identify
from . import (city_growth_plan, empire_depot, login_gifts, lucky_raffle,
                refining_weekly_card)
from .launcher import find_super_value_return
from .run import run_opened

KEY = "gift_super_value_return"
OPEN_ATTEMPTS = 3       # số lần về màn chính tìm nút + bấm
OPEN_WAITS = 8          # sau khi bấm: chụp kiểm tra màn Super Value Return tối đa chừng này lần, mỗi lần chờ 1s
TASKS = (
    login_gifts.TASK,
    empire_depot.TASK,
    lucky_raffle.TASK,
    city_growth_plan.TASK,
    refining_weekly_card.TASK,
)


def open_super_value_return(bot) -> bool:
    """Từ màn chính (có nút •••; đang ở bản đồ thế giới thì to_city vào thành trước) tìm nút vào bằng find_super_value_return
    (TH1-TH5, launcher.py), bấm, chờ tiêu đề SuperValueReturn/title tối đa OPEN_WAITS lần x 1s. Chưa vào thì về màn chính làm
    lại, tối đa OPEN_ATTEMPTS lần."""
    for attempt in range(1, OPEN_ATTEMPTS + 1):
        bot.check()
        if not on_main(bot, bot.screenshot()):
            return_home(bot)
        if to_city(bot):
            bot.record("Gift Claims: đang ở bản đồ thế giới; đã chuyển vào thành")
        if not on_main(bot, bot.screenshot()):
            bot.record(f"Gift Claims: chưa ở màn thành chính (lần {attempt}/{OPEN_ATTEMPTS})")
            continue
        pos = find_super_value_return(bot)
        if pos is None:
            continue
        bot.tap(*pos)
        for _ in range(OPEN_WAITS):
            bot.sleep(1)
            if identify(bot, bot.screenshot()) == GiftScreen.SUPER_VALUE_RETURN:
                bot.record("Gift Claims: đã vào Super Value Return")
                return True
        bot.record(f"Gift Claims: bấm rồi mà chưa vào màn Super Value Return sau {OPEN_WAITS}s "
                   f"(lần {attempt}/{OPEN_ATTEMPTS})")
    bot.record(f"Gift Claims: {OPEN_ATTEMPTS} lần không vào được Super Value Return; lần sau làm tiếp")
    return False


def _sweep(bot, pending: list[str]) -> set[str]:
    todo = [task for task in TASKS if task.key in pending]
    if not todo:
        return set()
    if identify(bot, bot.screenshot()) != GiftScreen.SUPER_VALUE_RETURN:
        if not open_super_value_return(bot):
            bot.record("Gift Claims: không mở được Super Value Return; "
                       "chưa tính là không thấy")
            return set()
    results, scanned_all = run_opened(bot, {task.key for task in todo})
    if not scanned_all:
        return set()
    return {key for key, state in results.items() if state == "not_present"}


def run(bot) -> bool:
    completed = scan.run_zone(
        bot, KEY, [(task.key, task.label) for task in TASKS], _sweep)
    return_home(bot)
    return completed
