"""
run.py — flow nhiệm vụ Ground Troop (Gather Troops, Day 2).

Ví dụ tối giản của một nhiệm vụ Event: phần đi từ màn chính tới màn event nằm trong
run_task() (xem event/common.py), nhiệm vụ chỉ cần ảnh riêng + hàm handle.

Flow:
1. Màn chính -> nút dưới Event Center -> danh sách event -> icon Gather Troops
   (run_task, giống hệt Cultivate Generals).
2. Màn Gather Troops vừa mở (tab Day 1 / Be Prepared): dừng — các bước sau chưa làm.
"""
from ...common import EVENT_OPENED, STOP, EventState, run_task
from ...constants import GATHER_TROOPS_ICON
from .constants import REGIONS, THRESHOLDS


def run(bot, task: dict, state: EventState):
    """`task` là settings của nhiệm vụ: {"value": int, "level": int, "day": int}."""

    def handle(action, pos, screen):
        if action == EVENT_OPENED:
            return STOP   # TODO: bấm tab Day 2 ...
        return None       # chưa có ảnh riêng: mọi action để handle_common lo

    run_task(bot, state, "Ground Troop", GATHER_TROOPS_ICON, handle,
             regions=REGIONS, thresholds=THRESHOLDS)
