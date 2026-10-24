"""Hoạt động Super Value Return độc lập với Valuable Event."""
from .. import scan
from ..common import return_home
from ..lobby import open_named
from ..screens import GiftScreen, identify
from . import (city_growth_plan, empire_depot, login_gifts, lucky_raffle,
                refining_weekly_card)
from .run import run_opened

KEY = "gift_super_value_return"
TASKS = (
    login_gifts.TASK,
    empire_depot.TASK,
    lucky_raffle.TASK,
    city_growth_plan.TASK,
    refining_weekly_card.TASK,
)


def _sweep(bot, pending: list[str]) -> set[str]:
    todo = [task for task in TASKS if task.key in pending]
    if not todo:
        return set()
    if identify(bot, bot.screenshot()) != GiftScreen.SUPER_VALUE_RETURN:
        if not open_named(bot, GiftScreen.SUPER_VALUE_RETURN):
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
