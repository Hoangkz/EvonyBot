"""
run.py — nhiệm vụ Ranged Troop (Gather Troops, Day 3): Day 3 -> tab phụ "Ranged Troop"
(bên phải) -> Go -> trại cung (Archer Camp) -> Train lính cung. Flow chung: xem
../train_troop/run.py.
"""
from ...common import EventState
from .. import train_troop
from .constants import DAY, DAY_3, KEY, RANGED_TROOP, RANGED_TROOP_SELECTED, THRESHOLDS, TIERS

NAME = "Ranged Troop"

TROOP = train_troop.TroopTask(
    key=KEY, name=NAME, day=DAY, day_tab=DAY_3,
    tab=RANGED_TROOP, tab_selected=RANGED_TROOP_SELECTED,
    tiers=TIERS, thresholds=THRESHOLDS,
)


def run(bot, task: dict, state: EventState):
    """`task` là settings của nhiệm vụ: {"value": int, "level": int, "day": int}."""
    train_troop.run(bot, task, state, TROOP)
