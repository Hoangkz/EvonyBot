"""
alliance_donation — Daily Activities: Alliance Donation.

- run.py:       `donate_free(bot)` (một lần donate) + `TASK` (nhãn / key của việc)
- constants.py: hằng số (nhãn, key, ô chọn giờ, key lưu giờ)
"""
from .constants import KEY, LABEL
from .run import TASK

__all__ = ["KEY", "LABEL", "TASK"]
