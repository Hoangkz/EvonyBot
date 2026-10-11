"""
registry.py — bảng nhiệm vụ của worker, dựng từ priority.py.

Mọi nhiệm vụ nằm trong bảng priority.py: mỗi dòng có `key`, độ ưu tiên và `policy` (luật chạy, xem policies.py). Dòng không
có `policy` (Bubble, Join Monster War, gift_*) không phải nhiệm vụ của bộ chọn. Thêm nhiệm vụ mới = thêm một dòng vào
priority.py (và hàm làm việc trong bot/activities/); không cần file khai báo riêng.

Khi bấm Start, worker lấy mọi nhiệm vụ có nhóm được chọn và đã được tích (tasks.py build_tasks), sắp theo độ ưu tiên rồi
gọi thẳng `run` của từng nhiệm vụ. Join Monster War không nằm ở đây (luật riêng trong BotWorker).
"""
from .policies import build_registry
from .priority import DATA
from .task_def import TaskDef  # noqa: F401 (các nơi khác import TaskDef từ đây)

REGISTRY: list[TaskDef] = build_registry(DATA)
