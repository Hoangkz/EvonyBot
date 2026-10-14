"""
material_composing — Daily Activities: Material Composing.

- run.py:       `handle(bot, action, pos, screen)` + `TASK` (common.Task)
- constants.py: ảnh riêng của nhiệm vụ
"""
from .constants import KEY, LABEL
from .run import TASK, after_go, handle

__all__ = ["KEY", "LABEL", "TASK", "after_go", "handle"]
