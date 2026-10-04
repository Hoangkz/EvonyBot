"""
run.py — Daily Activities "Patrol": handler các action riêng của nhiệm vụ (Tường thành -> Patrol 3 lần).
Vòng lặp chung (mở Activity, dòng Go, cuộn, ảnh xong): ../common.py run_task.
"""
from ..common import Task
from .constants import ACTIONS, DONE_IMAGES, FOLDER, KEY, LABEL


def handle(bot, action, pos, screen):
    if action == "patrol":
        for attempt in range(3):
            if attempt:
                bot.tap(108, 668, delay=3)  # Refresh rewards (gold)
            bot.tap(169, 607, delay=1)      # Select All
            bot.tap(286, 668, delay=3)      # Patrol
        bot.back(delay=2)
        return True
    if action == "patrol_button":
        bot.tap(*pos, delay=2)
    return False


TASK = Task(LABEL, FOLDER, DONE_IMAGES, ACTIONS, handle, key=KEY)
