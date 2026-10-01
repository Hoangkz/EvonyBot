"""
my_task — <Event>: <tên nhiệm vụ>
(key `my_task`, ô tích / ô chọn ở group <Event> trong ui/tabs/event.json).

- run.py:       `run(bot, task, state)` — flow của nhiệm vụ
- constants.py: ảnh, ngưỡng và action riêng của nhiệm vụ
"""
from .constants import KEY
from .run import run

__all__ = ["KEY", "run"]
