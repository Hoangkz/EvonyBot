"""Durable inventory of every known daily gift location.

The inventory, not a transient red badge, is the source of truth for what has
to be inspected in a server day.  A location may only write its key after its
own flow has opened the page and completed the safe inspection.  The worker
uses :meth:`BotWorker.is_daily_done`, so a timestamp automatically expires at
the configured server reset (14:00 by default).
"""
from dataclasses import dataclass

from .valuable_event import (
    city_growth_plan, empire_depot, general_vault, limited_offer, login_gifts,
    lucky_raffle, refining_stone_sprint, speedup_sprint, strategic_stockpile,
    successive_purchase_benefits, sulis_wishing, super_blazon_sale,
    super_value_weekly_card,
)
from .event_center import (
    blessing_of_pallas, dragon_battle, dwarfs_treasure, grace_of_star_trail,
    hypnos_dream, poseidons_day, precious_blazon_exchange,
    revelation_of_horus, sealed_imperial_treasury,
)
from .common import GiftTask


@dataclass(frozen=True)
class ClaimLocation:
    """One named place that must be inspected once per server day."""

    zone: str
    task: GiftTask


VALUABLE_EVENT = "valuable_event"
EVENT_CENTER = "event_center"


def _policy_task(module) -> GiftTask:
    """Expose Event Center policies without duplicating their DB key.

    A policy runner returns true only after its matching page was inspected;
    the GiftTask wrapper then records the per-event checkpoint.
    """
    policy = module.POLICY
    return GiftTask(policy.key, policy.label, module.run)


LOCATIONS = (
    ClaimLocation(VALUABLE_EVENT, general_vault.TASK),
    ClaimLocation(VALUABLE_EVENT, refining_stone_sprint.TASK),
    ClaimLocation(VALUABLE_EVENT, strategic_stockpile.TASK),
    ClaimLocation(VALUABLE_EVENT, limited_offer.TASK),
    ClaimLocation(VALUABLE_EVENT, speedup_sprint.TASK),
    ClaimLocation(VALUABLE_EVENT, super_blazon_sale.TASK),
    ClaimLocation(VALUABLE_EVENT, sulis_wishing.TASK),
    ClaimLocation(VALUABLE_EVENT, super_value_weekly_card.TASK),
    ClaimLocation(VALUABLE_EVENT, successive_purchase_benefits.TASK),
    ClaimLocation(VALUABLE_EVENT, empire_depot.TASK),
    ClaimLocation(VALUABLE_EVENT, lucky_raffle.TASK),
    ClaimLocation(VALUABLE_EVENT, city_growth_plan.TASK),
    ClaimLocation(VALUABLE_EVENT, login_gifts.TASK),
    ClaimLocation(EVENT_CENTER, _policy_task(blessing_of_pallas)),
    ClaimLocation(EVENT_CENTER, dragon_battle.TASK),
    ClaimLocation(EVENT_CENTER, _policy_task(precious_blazon_exchange)),
    ClaimLocation(EVENT_CENTER, _policy_task(poseidons_day)),
    ClaimLocation(EVENT_CENTER, _policy_task(hypnos_dream)),
    ClaimLocation(EVENT_CENTER, grace_of_star_trail.TASK),
    ClaimLocation(EVENT_CENTER, _policy_task(sealed_imperial_treasury)),
    ClaimLocation(EVENT_CENTER, _policy_task(dwarfs_treasure)),
    ClaimLocation(EVENT_CENTER, _policy_task(revelation_of_horus)),
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

