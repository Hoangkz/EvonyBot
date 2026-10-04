"""
run.py — Daily Activities "Resource Gathering": handler các action riêng của nhiệm vụ (phải chạy ngay sau Offering: bàn tay nổi trong thành thu mọi mỏ tài nguyên).
Vòng lặp chung (mở Activity, dòng Go, cuộn, ảnh xong): ../common.py run_task.
"""
from ..common import Task, open_daily_activity
from .constants import ACTIONS, AFTER_OPEN_TAP, DONE_IMAGES, FOLDER, KEY, LABEL


def handle(bot, action, pos, _screen):
    """Collect all ready city resources using the floating hand shortcut."""
    if action == "hand":
        bot.tap(*pos, delay=3)
        # Go opened the city from the task strip. Re-open and verify Activity
        # by image so a layout change cannot turn this into a Settings tap.
        open_daily_activity(bot)
    return False


TASK = Task(LABEL, FOLDER, DONE_IMAGES, ACTIONS, handle, AFTER_OPEN_TAP, key=KEY)
