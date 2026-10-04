"""
run.py — Daily Activities "Gold Levy": handler các action riêng của nhiệm vụ (Thành chính (Keep) -> Levy).
Vòng lặp chung (mở Activity, dòng Go, cuộn, ảnh xong): ../common.py run_task.
"""
from ....common import delay
from ..common import Task, replace_text
from .constants import ACTIONS, DONE_IMAGES, FOLDER, KEY, LABEL


def handle(bot, action, pos, screen):
    if action == "levy":
        # The current city UI opens a radial building menu first. Select Levy
        # before using the two legacy button coordinates inside its dialog.
        bot.tap(*pos, delay=3)
        bot.tap(280, 545, delay=3)
        bot.tap(105, 545, delay=3)
    elif action == "levy_one":
        # Levy1 is the dialog artwork in the current build; its old C# tap at
        # (300, 280) only hit the picture. Use the actual Free Levy buttons.
        bot.tap(280, 545, delay=3)
        bot.tap(105, 545, delay=3)
    elif action == "levy_times":
        bot.tap(190, 300)
        replace_text(bot, "5", 1)
        delay(bot, 2)
        bot.tap(200, 440, delay=4)
        bot.tap(195, 415, delay=2)
    return False


TASK = Task(LABEL, FOLDER, DONE_IMAGES, ACTIONS, handle, key=KEY)
