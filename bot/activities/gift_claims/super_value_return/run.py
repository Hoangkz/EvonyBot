"""Danh sách event của Super Value Return: ảnh tab + flow (ExactFlow) của từng event; cách đi hàng tab ở zone.py."""
from dataclasses import dataclass

from . import (city_growth_plan, empire_depot, login_gifts, lucky_raffle,
                refining_weekly_card)
from ..valuable_event.named_flow import ExactFlow


@dataclass(frozen=True)
class SuperValueSpec:
    task: object
    tab: str
    flow: ExactFlow


SPECS = (
    SuperValueSpec(empire_depot.TASK, "SuperValueReturn/EmpireDepot/tab_current", ExactFlow(
        claims=("SuperValueReturn/EmpireDepot/button_claimable_current",),
        done=("SuperValueReturn/EmpireDepot/chest_open",))),
    SuperValueSpec(login_gifts.TASK, "SuperValueReturn/LoginGifts/tab_text", ExactFlow()),
    SuperValueSpec(lucky_raffle.TASK, "SuperValueReturn/LuckyRaffle/tab", lucky_raffle.FLOW),
    SuperValueSpec(refining_weekly_card.TASK, "SuperValueReturn/RefiningWeeklyCard/tab",
                   refining_weekly_card.FLOW),
    # Kept for event rotations that still expose the older free reward column.
    SuperValueSpec(city_growth_plan.TASK, "SuperValueReturn/CityGrowthPlan/tab", ExactFlow(
        claims=("SuperValueReturn/CityGrowthPlan/button_claim_all", "Common/button_claim_all_text"),
        # Screenshot supplied by the user belongs to this tab: require row 15
        # and its green claimed check in the same crop, not any earlier check.
        done=("SuperValueReturn/CityGrowthPlan/level_15_claimed",),
        scroll_claims=True)),
)

KEYS = {spec.task.key for spec in SPECS}
