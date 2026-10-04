"""
run.py — Daily Activities "Alliance Donation": handler các action riêng của nhiệm vụ (Liên minh -> Donate).
Vòng lặp chung (mở Activity, dòng Go, cuộn, ảnh xong): ../common.py run_task.
"""
from ..common import Task
from .constants import ACTIONS, DONE_IMAGES, FOLDER, FOLDER_PATH, KEY, LABEL


def handle(bot, action, pos, screen):
    if action == "donate":
        _, y = pos
        row_y = max(0, y)
        region = bot.crop(screen, 0, row_y, screen.shape[1], 390)
        donate = bot.find(f"{FOLDER_PATH}/Donate.png", screen=region)
        if donate is None:
            return True
        bot.tap(donate[0], donate[1] + row_y, delay=1)
    return False


TASK = Task(LABEL, FOLDER, DONE_IMAGES, ACTIONS, handle, key=KEY)
