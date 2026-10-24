"""Hoạt động Valuable Event độc lập (không gồm Super Value Return)."""
from .. import scan
from ..common import return_home
from ..lobby import open_named
from ..screens import GiftScreen, identify
from . import (
    active_monthly_card, ancient_dynasty_treasury, general_vault, limited_offer,
    optional_package, refining_stone_sprint, resource_consumption_sprint,
    runestone_consumption_sprint,
    speedup_sprint, strategic_stockpile,
    successive_purchase_benefits, sulis_wishing, super_blazon_sale,
    super_value_weekly_card, tomb_expedition, wheel_of_dragon_war,
)
from .run import run_opened as run_valuable_opened

KEY = "gift_valuable_event"

TASKS = (
    resource_consumption_sprint.TASK, runestone_consumption_sprint.TASK,
    ancient_dynasty_treasury.TASK,
    general_vault.TASK, refining_stone_sprint.TASK, strategic_stockpile.TASK,
    limited_offer.TASK, speedup_sprint.TASK, super_blazon_sale.TASK,
    sulis_wishing.TASK, super_value_weekly_card.TASK,
    successive_purchase_benefits.TASK, optional_package.TASK,
    active_monthly_card.TASK, tomb_expedition.TASK,
    wheel_of_dragon_war.TASK,
)


def _sweep(bot, pending: list[str]) -> set[str]:
    inspected: set[str] = set()
    todo = [task for task in TASKS if task.key in pending]
    if not todo:
        return inspected
    screen = bot.screenshot()
    if identify(bot, screen) != GiftScreen.VALUABLE_EVENT:
        return_home(bot)
        if not open_named(bot, GiftScreen.VALUABLE_EVENT):
            bot.record("Gift Claims: không mở được ValuableEvent; "
                       "chưa tính là không thấy")
            return inspected
    results, scanned_all = run_valuable_opened(bot, {task.key for task in todo})
    if scanned_all:
        # Only truly absent labels accrue miss 1/3..3/3. A label that was
        # opened but failed its terminal condition stays pending without being
        # misclassified as absent.
        inspected.update(key for key, state in results.items()
                         if state == "not_present")
    return inspected


def run(bot) -> bool:
    """Chạy hoạt động Valuable Event; True khi mọi nhiệm vụ của nó đã xong hôm nay."""
    completed = scan.run_zone(
        bot, KEY, [(task.key, task.label) for task in TASKS], _sweep)
    return_home(bot)
    return completed
