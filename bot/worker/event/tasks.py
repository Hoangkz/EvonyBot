"""
tasks.py — khai báo nhiệm vụ của "Event" cho worker (TaskDef, xem bot/worker/task_def.py); registry.py gom lại.
Chọn nhiệm vụ nào chạy (ô tích, group bật), luật chạy (policy.py) đều ở đây, không nằm trong bot/activities/event/.

Mỗi nhiệm vụ trong EVENTS (bot/activities/event/run.py) là một nhiệm vụ riêng, cộng bước nhận thưởng "<event>_claim" của
từng event. Thêm nhiệm vụ Event mới: thêm vào EVENTS ở bot/activities/event/run.py (và key vào priority.py), không cần
sửa file này. Event 3 ngày khai báo ở event_center/tasks.py.
"""
from functools import partial

from ...activities.event.run import EVENTS
from ..task_def import TaskDef
from .policy import group_active, run_claim, run_event_task, task_enabled

EVENT = "Event"


def _build() -> list[TaskDef]:
    defs = []
    for event, name, icon, tasks in EVENTS:
        keys = [key for key, _ in tasks]
        for key, run_task in tasks:
            defs.append(TaskDef(
                key, EVENT,
                lambda s, event=event, key=key: group_active(s, event) and task_enabled(s, key),
                partial(run_event_task, key=key, run_task=run_task)))
        defs.append(TaskDef(
            f"{event}_claim", EVENT,
            lambda s, event=event, keys=keys: group_active(s, event) and any(task_enabled(s, k) for k in keys),
            partial(run_claim, event=event, name=name, icon=icon, keys=keys)))
    return defs


TASKS = _build()
