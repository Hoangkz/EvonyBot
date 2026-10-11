"""
daily — phần phân phối của nhóm "Daily Activities" nằm ở worker: khai báo nhiệm vụ (tasks.py) và luật chạy (policy.py).

Các việc Daily trong bot/activities/daily_activities/ chỉ làm thao tác trong game rồi trả TaskResult; ở đây quyết định
việc nào được chạy, đã xong hôm nay chưa, thử lại khi nào, bao lâu thử một lần (việc theo giờ) và khi nào nhận thưởng cuối.
"""
from .tasks import TASKS

__all__ = ["TASKS"]
