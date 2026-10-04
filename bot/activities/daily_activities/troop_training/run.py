"""
run.py — Daily Activities "Troop Training": handler các action riêng của nhiệm vụ (doanh trại -> Train).
Vòng lặp chung (mở Activity, dòng Go, cuộn, ảnh xong): ../common.py run_task.
"""
from ....common import delay
from ..common import Task, replace_text
from .constants import ACTIONS, DONE_IMAGES, FOLDER, KEY, LABEL


def handle(bot, action, pos, screen):
    if action == "interface":
        bot.swipe_percent(30, 65, 80, 65, duration=0.3, delay=1)
    elif action == "soldier":
        bot.tap(336, 582)
        replace_text(bot, "500", 3)
        delay(bot, 5)
        bot.tap(300, 660)
    elif action == "speed":
        bot.tap(*pos, delay=4)
        bot.tap(100, 670)
    return False


TASK = Task(LABEL, FOLDER, DONE_IMAGES, ACTIONS, handle, key=KEY)
