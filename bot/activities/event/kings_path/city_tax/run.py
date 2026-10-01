"""
run.py — nhiệm vụ City Tax (King's Path, Day 1): Day 1 -> tab phụ "City Tax" -> Go.
Flow chung tới Go: xem ../path_task.py.
TODO: phần sau Go (after_go) — cần ảnh màn game mở ra sau khi bấm Go.
"""
from ...common import EventState
from .. import path_task
from .constants import DAY, KEY, TAB, TAB_INDEX, TAB_SELECTED

NAME = "City Tax"

PATH = path_task.PathTask(
    key=KEY, name=NAME, day=DAY, tab_index=TAB_INDEX,
    tab_selected=TAB_SELECTED, tab=TAB,
)


def run(bot, task: dict, state: EventState):
    """`task` là settings của nhiệm vụ: {"value": int, "day": int}."""
    path_task.run(bot, task, state, PATH)
