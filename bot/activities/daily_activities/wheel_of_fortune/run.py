"""
run.py — Daily Activities "Wheel of Fortune": handler các action riêng của nhiệm vụ (quay 1 lần).
Vòng lặp chung (mở Activity, dòng Go, cuộn, ảnh xong): ../common.py run_task.

Luồng mới (after_go, sau khi open_task bấm Go): giống hệt King's Path Wheel sau Go (event/kings_path/wheel
spin_wheel) — 100 Spins nếu có, không thì 10 Spins liên tục tới khi hết chip -> Back, đánh dấu xong hôm nay.
"""
from ...event.kings_path.wheel.run import spin_wheel
from ..common import Task, mark_task_done, tap_first
from .constants import ACTIONS, AFTER_OPEN_TAP, DONE_IMAGES, FOLDER, FOLDER_PATH, KEY, LABEL


def handle(bot, action, pos, screen):
    if action == "spin":
        template = f"{FOLDER_PATH}/SpinOnce.png"
        if tap_first(bot, (template,), 1):
            bot.tap(170, 550)
            bot.back(delay=2)
        return True
    return False



def after_go(bot) -> bool:
    """Luồng mới, sau khi open_task bấm Go: quay Wheel of Fortune như King's Path. True nếu xong (đã đánh dấu
    xong hôm nay)."""
    return spin_wheel(bot, lambda: mark_task_done(bot, TASK), name=LABEL)


TASK = Task(LABEL, FOLDER, DONE_IMAGES, ACTIONS, handle, AFTER_OPEN_TAP, key=KEY)
