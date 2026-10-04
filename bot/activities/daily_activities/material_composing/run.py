"""
run.py — Daily Activities "Material Composing": handler các action riêng của nhiệm vụ (ghép pha lê cấp 3, 3 lần).
Vòng lặp chung (mở Activity, dòng Go, cuộn, ảnh xong): ../common.py run_task.
"""
from ....common import delay
from ..common import Task
from .constants import ACTIONS, AFTER_OPEN_TAP, DONE_IMAGES, FOLDER, FOLDER_PATH, KEY, LABEL


def handle(bot, action, pos, screen):
    if action == "level_one":
        delay(bot, 4)
        bot.tap(*pos, delay=2)
    elif action == "crystal":
        _, y = pos
        row_y = max(0, y)
        region = bot.crop(screen, 0, row_y, screen.shape[1], 250)
        compose = bot.find(f"{FOLDER_PATH}/Compose1.png", screen=region)
        if compose is not None:
            bot.tap(compose[0], compose[1] + row_y, delay=4)
    elif action == "compose":
        _, y = pos
        row_y = max(0, y)
        region = bot.crop(screen, 0, row_y, screen.shape[1], 666)
        lv3 = bot.find(f"{FOLDER_PATH}/Lv3Crystal.png", screen=region)
        if lv3 is not None:
            bot.tap(lv3[0], lv3[1] + row_y, delay=2)
            for _ in range(3):
                bot.tap(100, 670, delay=2)
            bot.back(delay=2)
        return True
    return False


TASK = Task(LABEL, FOLDER, DONE_IMAGES, ACTIONS, handle, AFTER_OPEN_TAP, key=KEY)
