"""
run.py — Daily Activities "Trap Buiding": phần làm nhiệm vụ sau Go (after_go) (công trình bẫy -> Build (nhãn Trap Buiding giữ như bản C# / tab UI)).
Mở dòng Activity + bấm Go: ../common.py (open_task_or_finish, daily_job).

Luồng mới (after_go, sau khi open_task bấm Go): ../train.py train_after_go, giống Gather Troops Trap Factory
(event/gather_troops/trap_factory) — Trap Factory -> "Build" -> bẫy đang hiện khi vào (không tìm loại / cấp)
-> số mặc định của ô (không nhập) -> ceil(TRAP_GOAL / số mỗi mẻ) mẻ -> Trap Building Speedup -> Finish All -> xong hôm nay.
"""
import math

from ...event.city_building import TRAP_FACTORY
from ...event.gather_troops.trap_factory.constants import BUILD, SPEEDUP_TITLE
from ..common import Task
from ..train import train_after_go
from .constants import FOLDER, KEY, LABEL, TRAP_GOAL


def after_go(bot) -> bool:
    """Luồng mới, sau khi open_task bấm Go: xây bẫy đang hiện khi vào màn Train bẫy cho đủ TRAP_GOAL (số mặc
    định mỗi mẻ, không nhập số). True nếu xong (đã đánh dấu xong hôm nay)."""
    return train_after_go(bot, TASK, TRAP_FACTORY, BUILD, lambda batch: math.ceil(TRAP_GOAL / batch),
                          speedup_title=SPEEDUP_TITLE)


TASK = Task(LABEL, FOLDER, key=KEY)
