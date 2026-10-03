"""
run.py — nhiệm vụ Siege Machine (Gather Troops, Day 4): Day 4 -> tab phụ "Siege Machine"
(bên trái) -> Go -> xưởng (Workshop) -> Train xe công thành. Flow chung: xem
../train_troop/run.py.
"""
from ...city_building import WORKSHOP
from ...common import EventState
from .. import train_troop
from .constants import DAY, DAY_4, KEY, SIEGE_MACHINE, SIEGE_MACHINE_SELECTED, THRESHOLDS, TIERS

NAME = "Siege Machine"

TROOP = train_troop.TroopTask(
    key=KEY, name=NAME, day=DAY, day_tab=DAY_4,
    tab=SIEGE_MACHINE, tab_selected=SIEGE_MACHINE_SELECTED,
    tiers=TIERS, building=WORKSHOP, thresholds=THRESHOLDS,
)


def run(bot, task: dict, state: EventState):
    """`task` là settings của nhiệm vụ: {"value": int, "level": int, "day": int}."""
    train_troop.run(bot, task, state, TROOP)
