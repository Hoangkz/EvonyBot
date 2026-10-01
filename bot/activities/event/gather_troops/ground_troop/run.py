"""
run.py — nhiệm vụ Ground Troop (Gather Troops, Day 2): Day 2 -> tab phụ "Ground Troop"
-> Go -> doanh trại (Barracks) -> Train lính bộ. Flow chung: xem ../train_troop/run.py.
"""
from ...common import EventState
from .. import train_troop
from .constants import DAY, DAY_2, GROUND_TROOP, GROUND_TROOP_SELECTED, KEY, THRESHOLDS, TIERS

NAME = "Ground Troop"

TROOP = train_troop.TroopTask(
    key=KEY, name=NAME, day=DAY, day_tab=DAY_2,
    tab=GROUND_TROOP, tab_selected=GROUND_TROOP_SELECTED,
    tiers=TIERS, thresholds=THRESHOLDS,
)


def run(bot, task: dict, state: EventState):
    """`task` là settings của nhiệm vụ: {"value": int, "level": int, "day": int}."""
    train_troop.run(bot, task, state, TROOP)
