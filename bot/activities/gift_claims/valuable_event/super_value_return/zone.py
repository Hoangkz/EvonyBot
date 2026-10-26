"""Hoạt động Super Value Return độc lập với Valuable Event."""
from ... import scan
from ...common import return_home
from ...lobby import open_named
from ...screens import GiftScreen, identify
from .. import (city_growth_plan, empire_depot, hall_of_historic_generals,
                login_gifts, lucky_raffle, refining_weekly_card,
                soul_of_spiritual_beast)
from .run import run_opened

KEY = "gift_super_value_return"
TASKS = (
    login_gifts.TASK,
    empire_depot.TASK,
    hall_of_historic_generals.TASK,
    soul_of_spiritual_beast.TASK,
    lucky_raffle.TASK,
    city_growth_plan.TASK,
    refining_weekly_card.TASK,
)


def _sweep(bot, pending: list[str], deferred: set[str] | None = None) -> set[str]:
    deferred = set() if deferred is None else deferred
    todo = [task for task in TASKS
            if task.key in pending and task.key not in deferred]
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
    deferred.update(key for key, state in results.items()
                    if state == "done_1")
    return {key for key, state in results.items() if state == "not_present"}


def run(bot) -> bool:
    deferred: set[str] = set()
    completed = scan.run_zone(
        bot, KEY, [(task.key, task.label) for task in TASKS],
        lambda current_bot, pending: _sweep(current_bot, pending, deferred))
    return_home(bot)
    return completed
