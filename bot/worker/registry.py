"""
registry.py — gom nhiệm vụ của worker.

Mọi nhiệm vụ đều khai báo ở worker (TaskDef, xem task_def.py): daily/, event/, event_center/ (tasks.py) và standalone.py
(Alliance Capacity, Open Gift Box, Black Market, Battlefield Shop). Việc phân phối là của worker; bot/activities/ chỉ làm
thao tác trong game. File này chỉ nối các danh sách đó lại.

Khi bấm Start, worker lấy mọi nhiệm vụ có nhóm được chọn và đã được tích, sắp theo độ ưu tiên (tasks.py build_tasks) rồi gọi
thẳng `run` riêng của từng nhiệm vụ — không đi qua hàm run của activity. Join Monster War không nằm ở đây (luật riêng trong
BotWorker).
"""
from .daily import TASKS as DAILY_ACTIVITIES
from .event import TASKS as EVENT
from .event_center import TASKS as EVENT_CENTER
from .standalone import TASKS as STANDALONE
from .task_def import TaskDef  # noqa: F401 (các nơi khác import TaskDef từ đây)

# Thứ tự = thứ tự xoay vòng khi cùng độ ưu tiên.
REGISTRY: list[TaskDef] = [
    *STANDALONE,
    *EVENT_CENTER,
    *DAILY_ACTIVITIES,
    *EVENT,
]
