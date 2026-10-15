"""
city_vip — Daily Activities: City VIP (nhận VIP ở thành, chỉ làm lúc 0h đến 1h giờ máy tính và khi đã có route công trình trong DB).

- run.py:       `in_window`, `claim_vip` (TODO), `JOB` (luật của việc cho bot/worker/priority.py)
- constants.py: nhãn, key, khung giờ
"""
from .constants import DONE_KEY, KEY, LABEL
from .run import JOB, claim_vip, in_window

__all__ = ["DONE_KEY", "JOB", "KEY", "LABEL", "claim_vip", "in_window"]
