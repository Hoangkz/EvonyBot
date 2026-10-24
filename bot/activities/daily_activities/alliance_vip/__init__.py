"""
alliance_vip — Daily Activities: Alliance VIP (mua vật phẩm đã tích ở Alliance Shop, từ Daily Sale trở xuống).

- run.py:       `buy_vip(bot)` + `JOB` (luật của việc cho bot/worker/priority.py)
- constants.py: ảnh / hằng số
"""
from .constants import DAY_KEY, LABEL
from .run import JOB, buy_vip

__all__ = ["DAY_KEY", "JOB", "LABEL", "buy_vip"]
