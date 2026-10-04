"""
run.py — Daily Activities "Troop Heading": handler các action riêng của nhiệm vụ (Bệnh viện -> Heal (nhãn Troop Heading giữ như bản C# / tab UI)).
Vòng lặp chung (mở Activity, dòng Go, cuộn, ảnh xong): ../common.py run_task.
"""
from ....common import delay
from ..common import Task, replace_text
from .constants import ACTIONS, DONE_IMAGES, FOLDER, KEY, LABEL


def handle(bot, action, pos, screen):
    if action == "heal_all":
        bot.tap(*pos, delay=4)
    elif action == "select":
        bot.tap(*pos, delay=2)
        replace_text(bot, "150", 1)
        delay(bot, 2)
        bot.tap(330, 670, delay=4)
        bot.tap(330, 670, delay=2)
    elif action == "heal_info":
        bot.tap(*pos, delay=2)
        bot.swipe_percent(65, 70, 65, 60, duration=1.0, delay=1)
        bot.swipe_percent(65, 70, 65, 60, duration=1.0, delay=1)
    return False


TASK = Task(LABEL, FOLDER, DONE_IMAGES, ACTIONS, handle, key=KEY)
