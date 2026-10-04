"""
run.py — Daily Activities "Black Market": handler các action riêng của nhiệm vụ (Chợ -> Black Market, mua 3 món tài nguyên).
Vòng lặp chung (mở Activity, dòng Go, cuộn, ảnh xong): ../common.py run_task.
"""
from ..common import Task, tap_first
from .constants import ACTIONS, DONE_IMAGES, FOLDER, FOLDER_PATH, KEY, LABEL


def handle(bot, action, pos, screen):
    if action == "market":
        bot.tap(*pos, delay=2)
    elif action == "buy":
        base = f"{FOLDER_PATH}/Buy"
        templates = tuple(f"{base}/{name}" for name in
                          ("food1.png", "lumber1.png", "ore1.png", "stone1.png"))

        def confirm():
            bot.tap(190, 415, delay=4)
        # (190, 575) used to change page in the C# era. In Evony 5.25 it is
        # "Instant Refresh" and costs gems, so never use it as a fallback.
        tap_first(bot, templates, 3, after=confirm)
        bot.back(delay=2)
        return True
    return False


TASK = Task(LABEL, FOLDER, DONE_IMAGES, ACTIONS, handle, key=KEY)
