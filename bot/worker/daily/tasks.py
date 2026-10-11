"""
tasks.py — khai báo nhiệm vụ của "Daily Activities" cho worker (TaskDef, xem bot/worker/task_def.py); registry.py
gom lại. Chọn nhiệm vụ nào chạy (ô tích ở tab UI), thứ tự, luật chạy (policy.py) đều ở đây, không nằm trong
bot/activities/daily_activities/.

Mỗi việc trong daily_activities.run.TASKS là một nhiệm vụ riêng (việc theo giờ: ô giờ > 0), cộng Buy Stamina / Buy Hammer
(mục General) và nhận thưởng cuối. Thêm việc Daily mới: thêm vào TASKS ở daily_activities/run.py (và key vào
priority.py), không cần sửa file này. Crazy Eggs (ô giờ ở mục General của tab này) khai báo ở worker/event_center/tasks.py.
"""
from functools import partial

from ...activities.daily_activities.constants import GENERAL, REWARDS_KEY
from ...activities.daily_activities.run import HOURLY, TASKS as DAILY_TASKS
from ..task_def import TaskDef
from .policy import (
    HOURLY_CONSTS,
    hourly_hours,
    run_buy_hammers_task,
    run_buy_stamina_task,
    run_daily_task,
    run_hourly_task,
    run_rewards,
    selected_labels,
)

DAILY = "Daily Activities"
STAMINA_KEY = "daily_buy_stamina"
HAMMERS_KEY = "daily_buy_hammers"
HOURLY_KEYS = {task.key for task, _ in HOURLY}


def _general(settings: dict) -> dict:
    general = settings.get(GENERAL, {})
    return general if isinstance(general, dict) else {}


def _stamina_enabled(settings: dict) -> bool:
    general = _general(settings)
    try:
        return bool(general.get("buy_stamina")) and int(general.get("stamina_quantity", 10)) > 0
    except (TypeError, ValueError):
        return False


def _build() -> list[TaskDef]:
    defs = [
        TaskDef(STAMINA_KEY, DAILY, _stamina_enabled, run_buy_stamina_task),
        TaskDef(HAMMERS_KEY, DAILY, lambda s: bool(_general(s).get("buy_all_hammers")), run_buy_hammers_task),
    ]
    for task in DAILY_TASKS:
        if task.key in HOURLY_KEYS:
            consts = HOURLY_CONSTS[task.key]
            defs.append(TaskDef(task.key, DAILY, lambda s, consts=consts: hourly_hours(s, consts) > 0,
                                partial(run_hourly_task, key=task.key)))
        else:
            defs.append(TaskDef(task.key, DAILY, lambda s, label=task.label: label in selected_labels(s),
                                partial(run_daily_task, task=task)))
    defs.append(TaskDef(REWARDS_KEY, DAILY, lambda s: bool(selected_labels(s)), run_rewards))
    return defs


TASKS = _build()
