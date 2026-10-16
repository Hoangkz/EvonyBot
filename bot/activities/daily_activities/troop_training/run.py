"""
run.py — Daily Activities "Troop Training": phần làm nhiệm vụ sau Go (after_go) (doanh trại -> Train).
Mở dòng Activity + bấm Go: ../common.py (open_task_or_finish, daily_job).

Luồng mới (after_go, sau khi open_task bấm Go): ../train.py train_after_go, giống King's Path Train Troop —
công trình train ngẫu nhiên 1 trong 4 loại -> "Train" -> cấp I -> không nhập số (số mặc định mỗi mẻ) -> số
mẻ = ceil(TRAIN_GOAL / số mỗi mẻ) -> mỗi mẻ Train -> Training Speedup -> Finish All -> xong hôm nay.
"""
import math

from ...event.city_building import TROOP, TROOP_BUILDINGS
from ...event.gather_troops.train_troop.constants import TRAIN
from ..common import Task
from ..train import train_after_go
from .constants import FOLDER, KEY, LABEL, TRAIN_GOAL


def after_go(bot) -> bool:
    """Luồng mới, sau khi open_task bấm Go: train cấp I cho đủ TRAIN_GOAL lính (số mặc định mỗi mẻ, không
    nhập số). True nếu xong (đã đánh dấu xong hôm nay)."""
    return train_after_go(bot, TASK, TROOP, TRAIN, lambda batch: math.ceil(TRAIN_GOAL / batch),
                          also=TROOP_BUILDINGS, first_tier=True)


TASK = Task(LABEL, FOLDER, key=KEY)
