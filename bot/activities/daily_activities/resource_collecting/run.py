"""
run.py — Daily Activities "Resource Collecting": handler các action riêng của nhiệm vụ (Học viện -> Collection; xong khi dòng ClaimCollecting hết Go. Finish1.png là icon Skill Book Shop của Học viện, không dùng làm ảnh xong).
Vòng lặp chung (mở Activity, dòng Go, cuộn, ảnh xong): ../common.py run_task.
"""
from ..common import Task, open_daily_activity
from .constants import ACTIONS, DONE_IMAGES, FOLDER, KEY, LABEL


def handle(bot, action, pos, screen):
    if action == "collection":
        bot.tap(*pos, delay=4)
        # Collection is the indirect action. Return explicitly and let
        # VERIFY_COLLECTING check the real ClaimCollecting row's Go button.
        open_daily_activity(bot)
    return False


TASK = Task(LABEL, FOLDER, DONE_IMAGES, ACTIONS, handle, key=KEY)
