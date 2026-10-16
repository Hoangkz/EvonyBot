"""Hoạt động Valuable Event: Valuable Event + Super Value Return (khu quà ngoài Event Center)."""
from .. import scan
from ..common import return_home
from ..lobby import open_named
from ..screens import GiftScreen
from . import (
    ancient_dynasty_treasury, city_growth_plan, empire_depot, general_vault,
    limited_offer, login_gifts, lucky_raffle, refining_stone_sprint,
    resource_consumption_sprint, speedup_sprint, strategic_stockpile,
    successive_purchase_benefits, sulis_wishing, super_blazon_sale,
    super_value_weekly_card,
)

KEY = "gift_valuable_event"

# (màn cha, các nhiệm vụ nằm trong màn đó)
GROUPS = (
    (GiftScreen.VALUABLE_EVENT, (
        resource_consumption_sprint.TASK, ancient_dynasty_treasury.TASK,
        general_vault.TASK, refining_stone_sprint.TASK, strategic_stockpile.TASK,
        limited_offer.TASK, speedup_sprint.TASK, super_blazon_sale.TASK,
        sulis_wishing.TASK, super_value_weekly_card.TASK,
        successive_purchase_benefits.TASK,
    )),
    (GiftScreen.SUPER_VALUE_RETURN, (
        empire_depot.TASK, lucky_raffle.TASK, city_growth_plan.TASK,
        login_gifts.TASK,
    )),
)
TASKS = tuple(task for _, tasks in GROUPS for task in tasks)


def _sweep(bot, pending: list[str]) -> set[str]:
    inspected: set[str] = set()
    for screen, tasks in GROUPS:
        todo = [task for task in tasks if task.key in pending]
        if not todo:
            continue
        if not open_named(bot, screen):
            bot.record(f"Gift Claims: không mở được {screen.value}; chưa tính là không thấy")
            continue
        for task in todo:
            bot.check()
            # GiftTask.run: thấy event thì nhận quà rồi tự đánh dấu xong; không thấy thì back về màn chính.
            task.run(bot)
            inspected.add(task.key)
        return_home(bot)
    return inspected


def run(bot) -> bool:
    """Chạy hoạt động Valuable Event; True khi mọi nhiệm vụ của nó đã xong hôm nay."""
    return scan.run_zone(bot, KEY, [(task.key, task.label) for task in TASKS], _sweep)
