"""
run.py — Daily Activities "Wheel of Fortune": phần làm nhiệm vụ sau Go (after_go) (quay 1 lần).
Mở dòng Activity + bấm Go: ../common.py (open_task_or_finish, daily_job).

Luồng mới (after_go, sau khi open_task bấm Go): như King's Path Wheel sau Go (event/kings_path/wheel spin_wheel) —
100 Spins nếu có, không thì 10 Spins đúng SPINS_10_GOAL lần (không quay tới hết chip, không vào Purchase Chips)
-> Back, đánh dấu xong hôm nay.
"""
from ...event.kings_path.wheel.run import spin_wheel
from ..common import Task, mark_task_done
from .constants import FOLDER, KEY, LABEL, SPINS_10_GOAL


def after_go(bot) -> bool:
    """Luồng mới, sau khi open_task bấm Go: 100 Spins nếu có, không thì 10 Spins SPINS_10_GOAL lần. True nếu xong
    (đã đánh dấu xong hôm nay)."""
    return spin_wheel(bot, lambda: mark_task_done(bot, TASK), name=LABEL, max_spins_10=SPINS_10_GOAL)


TASK = Task(LABEL, FOLDER, key=KEY)
