"""
event — phần phân phối của nhóm "Event" nằm ở worker: khai báo nhiệm vụ (tasks.py) và luật chạy (policy.py).

Các nhiệm vụ trong bot/activities/event/ chỉ làm thao tác trong game rồi báo kết quả (TaskResult); ở đây quyết định nhiệm
vụ nào được chạy (ô tích, group bật), bỏ qua nhiệm vụ đã xong / đã đạt mục tiêu / Day khoá, ghi kết quả và khi nào nhận
thưởng event.
"""
from .tasks import TASKS

__all__ = ["TASKS"]
