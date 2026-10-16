"""
resource_tax — Daily Activities: Resource Tax.

- run.py:       `after_go(bot)` + `TASK` (common.Task)
- constants.py: ảnh riêng của nhiệm vụ
"""
from .constants import KEY, LABEL
from .run import TASK

__all__ = ["KEY", "LABEL", "TASK"]
