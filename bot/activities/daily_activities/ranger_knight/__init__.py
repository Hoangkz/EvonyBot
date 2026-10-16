"""
ranger_knight — Daily Activities: Ranger Knight Order (Claim, rồi Quick Dispatch -> Send).

- run.py:       `after_go(bot)` + `TASK` (common.Task)
- constants.py: ảnh riêng của nhiệm vụ
"""
from .constants import KEY, LABEL
from .run import TASK, after_go

__all__ = ["KEY", "LABEL", "TASK", "after_go"]
