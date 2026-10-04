"""
run.py — Daily Activities "General Enhancing": handler các action riêng của nhiệm vụ (tướng -> Cultivate 5 lần (sau Go bấm (30, 50) như bản C#)).
Vòng lặp chung (mở Activity, dòng Go, cuộn, ảnh xong): ../common.py run_task.
"""
from ..common import Task, tap_first
from .constants import ACTIONS, AFTER_OPEN_TAP, DONE_IMAGES, FOLDER, FOLDER_PATH, KEY, LABEL


def handle(bot, action, pos, screen):
    if action == "cultivate":
        bot.tap(*pos, delay=3)
    elif action == "cultivate_loop":
        base = f"{FOLDER_PATH}/TapEnhancing"
        templates = (f"{base}/Agree.png", f"{base}/Disagree.png")
        if tap_first(bot, templates, 5):
            bot.tap(110, 666)
            bot.back(delay=2)
        return True
    return False


TASK = Task(LABEL, FOLDER, DONE_IMAGES, ACTIONS, handle, AFTER_OPEN_TAP, key=KEY)
