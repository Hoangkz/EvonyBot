"""
offering — Daily Activities: Offering.

- run.py:       `handle(bot, action, pos, screen)` + `TASK` (common.Task)
- constants.py: ảnh riêng của nhiệm vụ
"""
from .constants import KEY, LABEL
from .run import TASK, handle

__all__ = ["KEY", "LABEL", "TASK", "handle"]
