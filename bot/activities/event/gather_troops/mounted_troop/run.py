"""
run.py — nhiệm vụ Mounted Troop (Gather Troops, Day 3): Day 3 -> tab phụ "Mounted Troop"
-> Go -> chuồng ngựa (Stables) -> Train lính kỵ. Flow chung: xem ../train_troop/run.py.
"""
from ...common import EventState
from .. import train_troop
from .constants import DAY, DAY_3, KEY, MOUNTED_TROOP, MOUNTED_TROOP_SELECTED, THRESHOLDS, TIERS

NAME = "Mounted Troop"

TROOP = train_troop.TroopTask(
    key=KEY, name=NAME, day=DAY, day_tab=DAY_3,
    tab=MOUNTED_TROOP, tab_selected=MOUNTED_TROOP_SELECTED,
    tiers=TIERS, thresholds=THRESHOLDS,
)


def run(bot, task: dict, state: EventState):
    """`task` là settings của nhiệm vụ: {"value": int, "level": int, "day": int}."""
    train_troop.run(bot, task, state, TROOP)
