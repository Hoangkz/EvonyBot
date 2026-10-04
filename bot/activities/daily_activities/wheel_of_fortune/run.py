"""
run.py — Daily Activities "Wheel of Fortune": handler các action riêng của nhiệm vụ (quay 1 lần).
Vòng lặp chung (mở Activity, dòng Go, cuộn, ảnh xong): ../common.py run_task.
"""
from ..common import Task, tap_first
from .constants import ACTIONS, AFTER_OPEN_TAP, DONE_IMAGES, FOLDER, FOLDER_PATH, KEY, LABEL


def handle(bot, action, pos, screen):
    if action == "spin":
        template = f"{FOLDER_PATH}/SpinOnce.png"
        if tap_first(bot, (template,), 1):
            bot.tap(170, 550)
            bot.back(delay=2)
        return True
    return False


TASK = Task(LABEL, FOLDER, DONE_IMAGES, ACTIONS, handle, AFTER_OPEN_TAP, key=KEY)
