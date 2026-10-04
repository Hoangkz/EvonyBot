"""
run.py — Daily Activities "Resource Tax": handler các action riêng của nhiệm vụ (Chợ -> Tax).
Vòng lặp chung (mở Activity, dòng Go, cuộn, ảnh xong): ../common.py run_task.
"""
from ....common import delay
from ..common import Task, replace_text
from .constants import ACTIONS, DONE_IMAGES, FOLDER, KEY, LABEL


def handle(bot, action, pos, screen):
    if action == "tax":
        bot.tap(*pos, delay=4)
    elif action == "revenue":
        bot.tap(300, 280)
    elif action == "tax_amount":
        bot.tap(200, 300, delay=1)
        replace_text(bot, "0", 1)
        delay(bot, 2)
        bot.tap(200, 440, delay=4)
        bot.tap(195, 415, delay=4)
        return True
    return False


TASK = Task(LABEL, FOLDER, DONE_IMAGES, ACTIONS, handle, key=KEY)
