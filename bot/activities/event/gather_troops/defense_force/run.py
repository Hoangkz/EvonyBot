"""
run.py — nhiệm vụ Defense Force (Gather Troops, Day 4): Day 4 -> tab phụ "Defense Force"
(bên phải) -> Go -> xưởng bẫy (Trap Factory) -> "Build" -> xây bẫy. Flow chung với các
nhiệm vụ train lính: xem ../train_troop/run.py; khác ở icon menu ("Build"), tiêu đề màn
speedup, cấp thấp nhất (3) và mỗi cấp có 4 loại bẫy (xem ../troop_tier.py).
"""
from ...city_building import DEFENSE_FORCE
from ...common import EventState
from .. import train_troop
from .constants import (BUILD, DAY, DAY_4, DEFENSE_FORCE, DEFENSE_FORCE_SELECTED, KEY,
                        LOWEST_LEVEL, SPEEDUP_TITLE, THRESHOLDS, TIERS)

NAME = "Defense Force"

TROOP = train_troop.TroopTask(
    key=KEY, name=NAME, day=DAY, day_tab=DAY_4,
    tab=DEFENSE_FORCE, tab_selected=DEFENSE_FORCE_SELECTED,
    tiers=TIERS, building=DEFENSE_FORCE, thresholds=THRESHOLDS,
    lowest=LOWEST_LEVEL, menu_icon=BUILD, speedup_title=SPEEDUP_TITLE,
)


def run(bot, task: dict, state: EventState):
    """`task` là settings của nhiệm vụ: {"value": int, "level": int, "day": int}."""
    train_troop.run(bot, task, state, TROOP)
