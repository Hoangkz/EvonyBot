"""
run.py — Daily Activities "Trap Buiding": handler các action riêng của nhiệm vụ (công trình bẫy -> Build (nhãn Trap Buiding giữ như bản C# / tab UI)).
Vòng lặp chung (mở Activity, dòng Go, cuộn, ảnh xong): ../common.py run_task.
"""
from ....common import delay
from ..common import Task, replace_text
from .constants import ACTIONS, DONE_IMAGES, FOLDER, KEY, LABEL


def handle(bot, action, pos, screen):
    if action == "interface":
        # In 5.25 the four trap types are fixed buttons, not a troop carousel.
        # Pick the visible tier-I trap and submit the requested amount directly.
        bot.tap(95, 453, delay=1)
        bot.tap(336, 582)
        replace_text(bot, "150", 3)
        delay(bot, 2)
        bot.tap(300, 660)
    elif action == "build":
        bot.tap(336, 582)
        replace_text(bot, "150", 3)
        delay(bot, 2)
        bot.tap(300, 660)
    elif action == "speed":
        bot.tap(*pos, delay=2)
        bot.tap(100, 670, delay=2)
        bot.back(delay=2)
    return False


TASK = Task(LABEL, FOLDER, DONE_IMAGES, ACTIONS, handle, key=KEY)
