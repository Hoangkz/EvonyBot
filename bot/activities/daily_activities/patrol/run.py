"""
run.py — Daily Activities "Patrol": phần làm nhiệm vụ sau Go (after_go) (Tường thành -> Patrol 3 lần).
Mở dòng Activity + bấm Go: ../common.py (open_task_or_finish, daily_job).

Luồng mới (after_go, sau khi open_task bấm Go): giống hệt King's Path Patrol sau Go (event/kings_path/patrol) —
Tường thành -> "Patrol" -> màn Patrol -> patrol_rounds (Select All -> Patrol -> Refresh) làm hết 10 lượt trong ngày
(PATROL_GOAL) hoặc tới khi hết Refresh -> Back, đánh dấu xong hôm nay.
"""
from ...event.city_building import WALLS
from ...event.kings_path.building import open_building
from ...event.kings_path.patrol.constants import MENU_PATROL, PATROL_TITLE
from ...event.kings_path.patrol.run import patrol_rounds
from ..common import Task, mark_task_done
from .constants import FOLDER, KEY, LABEL, PATROL_GOAL


def after_go(bot) -> bool:
    """Luồng mới, sau khi open_task bấm Go: patrol hết lượt trong ngày (hoặc tới khi hết Refresh). True nếu xong
    (đã đánh dấu xong hôm nay); False nếu không mở được màn Patrol / lỗi giữa chừng."""
    if not open_building(bot, LABEL, WALLS, MENU_PATROL, PATROL_TITLE):
        return False

    def finish(message: str, _complete: bool):
        bot.log(f"{LABEL}: {message}")
        bot.back(delay=1)
        mark_task_done(bot, TASK)

    return patrol_rounds(bot, 0, PATROL_GOAL, finish, name=LABEL, key=KEY)


TASK = Task(LABEL, FOLDER, key=KEY)
