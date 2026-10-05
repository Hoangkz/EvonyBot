"""
run.py — Daily Activities "Wheel of Fortune": handler các action riêng của nhiệm vụ (quay 1 lần).
Vòng lặp chung (mở Activity, dòng Go, cuộn, ảnh xong): ../common.py run_task.

Luồng mới (after_go, sau khi open_task bấm Go): như King's Path Wheel sau Go (event/kings_path/wheel spin_wheel) —
100 Spins nếu có, không thì 10 Spins đúng SPINS_10_GOAL lần (không quay tới hết chip, không vào Purchase Chips)
-> Back, đánh dấu xong hôm nay.
"""
from ...event.kings_path.wheel.run import spin_wheel
from ..common import Task, mark_task_done, tap_first
from .constants import ACTIONS, AFTER_OPEN_TAP, DONE_IMAGES, FOLDER, FOLDER_PATH, KEY, LABEL, SPINS_10_GOAL


def handle(bot, action, pos, screen):
    if action == "spin":
        template = f"{FOLDER_PATH}/SpinOnce.png"
        if tap_first(bot, (template,), 1):
            bot.tap(170, 550)
            bot.back(delay=2)
        return True
    return False



def after_go(bot) -> bool:
    """Luồng mới, sau khi open_task bấm Go: 100 Spins nếu có, không thì 10 Spins SPINS_10_GOAL lần. True nếu xong
    (đã đánh dấu xong hôm nay)."""
    return spin_wheel(bot, lambda: mark_task_done(bot, TASK), name=LABEL, max_spins_10=SPINS_10_GOAL)


TASK = Task(LABEL, FOLDER, DONE_IMAGES, ACTIONS, handle, AFTER_OPEN_TAP, key=KEY)
