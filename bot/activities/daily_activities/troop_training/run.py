"""
run.py — Daily Activities "Troop Training": handler các action riêng của nhiệm vụ (doanh trại -> Train).
Vòng lặp chung (mở Activity, dòng Go, cuộn, ảnh xong): ../common.py run_task.

Luồng mới (after_go, sau khi open_task bấm Go): ../train.py train_after_go, giống King's Path Train Troop —
công trình train ngẫu nhiên 1 trong 4 loại -> "Train" -> cấp I -> không nhập số (số mặc định mỗi mẻ) -> số
mẻ = ceil(TRAIN_GOAL / số mỗi mẻ) -> mỗi mẻ Train -> Training Speedup -> Finish All -> xong hôm nay.
"""
import math

from ....common import delay
from ...event.city_building import TROOP, TROOP_BUILDINGS
from ...event.gather_troops.train_troop.constants import TRAIN
from ..common import Task, replace_text
from ..train import train_after_go
from .constants import ACTIONS, DONE_IMAGES, FOLDER, KEY, LABEL, TRAIN_GOAL


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


def after_go(bot) -> bool:
    """Luồng mới, sau khi open_task bấm Go: train cấp I cho đủ TRAIN_GOAL lính (số mặc định mỗi mẻ, không
    nhập số). True nếu xong (đã đánh dấu xong hôm nay)."""
    return train_after_go(bot, TASK, TROOP, TRAIN, lambda batch: math.ceil(TRAIN_GOAL / batch),
                          also=TROOP_BUILDINGS, first_tier=True)


TASK = Task(LABEL, FOLDER, DONE_IMAGES, ACTIONS, handle, key=KEY)
