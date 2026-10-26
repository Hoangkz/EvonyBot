"""
greet_champion — Daily Activities: Greet the Champion (bot chào đủ 5 lần mới tính xong).

- run.py:       `after_go(bot)` + `TASK` (common.Task)
- constants.py: ảnh riêng của nhiệm vụ
"""
from .constants import KEY, LABEL
from .run import TASK, after_go

__all__ = ["KEY", "LABEL", "TASK", "after_go"]
