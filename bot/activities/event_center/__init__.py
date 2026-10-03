"""
event_center — các nhiệm vụ trong Event Center (nút cúp "Event Center" ở cột phải màn chính).

KHÔNG phải activity (không có trong ACTIVITIES): activity nào cần thì gọi nhiệm vụ ở đây,
VD "Crazy Eggs" -> event_center.crazy_eggs.run.

- common.py:     đi từ màn chính tới một event trong Event Center (run_task):
                 màn chính -> bấm chính Event Center -> tab (Activities, ...) -> cuộn tìm icon
- constants.py:  image folders, limits and action names dùng chung
- crazy_eggs/:   nhiệm vụ đập trứng (Activities -> Crazy Eggs)
"""
from . import crazy_eggs

__all__ = ["crazy_eggs"]
