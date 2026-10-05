"""
alliance_help — Daily Activities: Alliance Help (theo giờ, như Alliance Donation).

- run.py:       `help_all(bot)` (một lần thử) + `TASK` (common.Task)
- constants.py: ảnh riêng của nhiệm vụ
"""
from .constants import KEY, LABEL
from .run import TASK, help_all

__all__ = ["KEY", "LABEL", "TASK", "help_all"]
