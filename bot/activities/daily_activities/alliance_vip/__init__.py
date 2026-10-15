"""
alliance_vip — Daily Activities: Alliance VIP (mua VIP Monthly / Daily ở Alliance Shop).

- run.py:       `buy_vip(bot, month, day)` + `JOB` (luật của việc cho bot/worker/priority.py)
- constants.py: ảnh / hằng số
"""
from .constants import DAY_KEY, LABEL, MONTH_KEY
from .run import JOB, buy_vip

__all__ = ["DAY_KEY", "JOB", "LABEL", "MONTH_KEY", "buy_vip"]
