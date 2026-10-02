"""
run.py — nhiệm vụ Train Troop (King's Path, Day 3): giống hệt Ground Troop của Gather
Troops (Day 3 -> tab phụ "Strong Troops" -> Go -> doanh trại -> Train lính bộ), chỉ khác
luôn chọn lính cấp I (vòng đầu tiên). Flow chung: xem gather_troops/train_troop/run.py.
"""
from ...common import EventState
from ...constants import KINGS_PATH_ICON
from ...gather_troops import train_troop
from ..constants import TITLE, TITLE_REGION
from .constants import DAY, DAY_3, KEY, LOWEST, TAB, TAB_SELECTED, THRESHOLDS, TIERS

NAME = "Train Troop"

TROOP = train_troop.TroopTask(
    key=KEY, name=NAME, day=DAY, day_tab=DAY_3,
    tab=TAB, tab_selected=TAB_SELECTED,
    tiers=TIERS, thresholds=THRESHOLDS, lowest=LOWEST,
    event_icon=KINGS_PATH_ICON, title=TITLE, title_region=TITLE_REGION, first_tier=True,
)


def run(bot, task: dict, state: EventState):
    """`task` là settings của nhiệm vụ: {"value": int, "day": int}."""
    train_troop.run(bot, task, state, TROOP)
