"""Durable inventory of every known daily gift location.

The inventory, not a transient red badge, is the source of truth for what has
to be inspected in a server day.  A location may only write its key after its
own flow has opened the page and completed the safe inspection.  The worker
uses :meth:`BotWorker.is_daily_done`, so a timestamp automatically expires at
the configured server reset (14:00 by default).
"""
from dataclasses import dataclass

from . import back_to_territory
from .valuable_event import (
    ancient_dynasty_treasury, city_growth_plan, empire_depot, general_vault,
    limited_offer, login_gifts, lucky_raffle, refining_stone_sprint,
    resource_consumption_sprint, speedup_sprint, strategic_stockpile,
    successive_purchase_benefits, sulis_wishing, super_blazon_sale,
    super_value_weekly_card,
)
from .event_center import (
    blessing_of_pallas, dragon_battle, dwarfs_treasure, giants_wisdom_temple,
    grace_of_star_trail,
    hypnos_dream, poseidons_day, precious_blazon_exchange,
    revelation_of_horus, sealed_imperial_treasury, wishful_windmill_festival,
)
from .common import GiftTask


@dataclass(frozen=True)
class ClaimLocation:
    """One named place that must be inspected once per server day."""

    zone: str
    task: GiftTask


# Quy ước nghiệp vụ:
# - Vùng 1: mọi điểm nhận quà KHÔNG nằm trong Event Center.
# - Vùng 2: thanh phải ngoài thành, gồm Back to Territory và Event Center;
#   chỉ các policy Event Center mới cần mở Event Center trước.
REGION_1 = "region_1"
REGION_2 = "region_2"

# Compatibility aliases for older callers/tests.  ``VALUABLE_EVENT`` includes
# Super Value Return and the other non-Event-Center gift parents as well.
VALUABLE_EVENT = REGION_1
EVENT_CENTER = REGION_2


def _policy_task(module) -> GiftTask:
    """Expose Event Center policies without duplicating their DB key.

    A policy runner returns true only after its matching page was inspected;
    the GiftTask wrapper then records the per-event checkpoint.
    """
    policy = module.POLICY
    return GiftTask(policy.key, policy.label, module.run)


VALUABLE_EVENT_TASKS = (
    resource_consumption_sprint.TASK,
    ancient_dynasty_treasury.TASK,
    general_vault.TASK,
    refining_stone_sprint.TASK,
    strategic_stockpile.TASK,
    limited_offer.TASK,
    speedup_sprint.TASK,
    super_blazon_sale.TASK,
    sulis_wishing.TASK,
    super_value_weekly_card.TASK,
    successive_purchase_benefits.TASK,
)

SUPER_VALUE_RETURN_TASKS = (
    empire_depot.TASK,
    lucky_raffle.TASK,
    city_growth_plan.TASK,
    login_gifts.TASK,
)

REGION_1_TASKS = VALUABLE_EVENT_TASKS + SUPER_VALUE_RETURN_TASKS
REGION_2_OUTER_TASKS = (back_to_territory.TASK,)

LOCATIONS = (
    *(ClaimLocation(REGION_1, task) for task in REGION_1_TASKS),
    *(ClaimLocation(REGION_2, task) for task in REGION_2_OUTER_TASKS),
    ClaimLocation(REGION_2, _policy_task(blessing_of_pallas)),
    ClaimLocation(REGION_2, dragon_battle.TASK),
    ClaimLocation(REGION_2, _policy_task(precious_blazon_exchange)),
    ClaimLocation(REGION_2, _policy_task(poseidons_day)),
    ClaimLocation(REGION_2, _policy_task(hypnos_dream)),
    ClaimLocation(REGION_2, grace_of_star_trail.TASK),
    ClaimLocation(REGION_2, _policy_task(sealed_imperial_treasury)),
    ClaimLocation(REGION_2, _policy_task(dwarfs_treasure)),
    ClaimLocation(REGION_2, _policy_task(giants_wisdom_temple)),
    ClaimLocation(REGION_2, _policy_task(wishful_windmill_festival)),
    ClaimLocation(REGION_2, _policy_task(revelation_of_horus)),
)


def locations(zone: str | None = None) -> tuple[ClaimLocation, ...]:
    """Return every known location, optionally restricted to one outer zone."""
    return tuple(item for item in LOCATIONS if zone is None or item.zone == zone)


def pending(bot, zone: str | None = None) -> tuple[ClaimLocation, ...]:
    """Locations whose timestamp is before the latest server reset."""
    return tuple(item for item in locations(zone) if not bot.is_daily_done(item.task.key))


def complete(bot) -> bool:
    """The aggregate task is eligible only after every location is current."""
    return not pending(bot)

