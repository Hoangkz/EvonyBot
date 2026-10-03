"""
run.py — nhiệm vụ Donate (King's Path, Day 2): Day 2 -> tab phụ "Teamwork" -> dòng
"Donate to the Alliance" -> Go -> màn Alliance Science -> bấm Donate cho đủ mục tiêu.
Flow chung tới Go: xem ../path_task.py.

Sau Go (màn Alliance Science):
- Hộp "Spend N Gems on clearing the Cooldown?" -> Okay.
- Nút "Donate" -> bấm, đếm 1 lần. Đủ (mục tiêu - số đã làm) lần -> đánh dấu xong.
- Hết lượt (nút kim cương) -> bấm để mua lại lượt, tối đa MAX_GEM_BUYS (5) lần; quá thì dừng.
Không đọc được số đã làm ở dòng Go thì không donate (không biết lúc nào dừng, tránh tiêu
kim cương). Bị ngắt giữa chừng: lượt sau đọc lại số đã làm ở dòng Go rồi làm tiếp.

Ô Patrol ở tab Event = 0 (không làm Patrol): không vào King's Path mà donate qua Liên minh ->
Alliance Science (alliance.py). Vòng donate dùng chung: donating.py.
"""
from ...common import EventState, mark_target_reached
from .. import path_task
from . import alliance
from .constants import (
    DAY,
    EVENT_TAB,
    KEY,
    PATROL_KEY,
    ROW_TITLE,
    SCIENCE_TITLE,
    SCIENCE_WAIT,
    TAB,
    TAB_INDEX,
    TAB_SELECTED,
)
from .donating import donate_times

NAME = "Donate"


def _donate(bot, path, done, target):
    """Sau Go: donate (mục tiêu - số đã làm) lần ở màn Alliance Science."""
    if done is None:
        bot.record(f"{NAME}: progress unknown, not donating")
        return
    if bot.wait_for(SCIENCE_TITLE, timeout=SCIENCE_WAIT) is None:
        bot.record(f"{NAME}: Alliance Science not shown")
        return
    need = target - done
    donated = donate_times(bot, NAME, need)
    if donated >= need:
        bot.record(f"{NAME}: donated {donated}, done")
        mark_target_reached(bot, path.key)


def _patrol_enabled(bot) -> bool:
    """Ô Patrol ở tab Event có bật (giá trị khác 0) không. Không có cấu hình tab Event (VD test
    chỉ truyền settings của nhiệm vụ) -> coi như bật."""
    event = (getattr(bot, "settings", None) or {}).get(EVENT_TAB)
    if not event:
        return True
    patrol = event.get(PATROL_KEY)
    if not isinstance(patrol, dict):
        return False
    return str(patrol.get("value", 0)) not in ("", "0")


PATH = path_task.PathTask(
    key=KEY, name=NAME, day=DAY, tab_index=TAB_INDEX,
    tab_selected=TAB_SELECTED, tab=TAB,
    row_title=ROW_TITLE, after_go=_donate,
)


def run(bot, task: dict, state: EventState):
    """`task` là settings của nhiệm vụ: {"value": int, "day": int}. Không làm Patrol -> donate qua
    Liên minh (alliance.py), không vào King's Path."""
    if not _patrol_enabled(bot):
        alliance.run(bot, task)
        return
    path_task.run(bot, task, state, PATH)
