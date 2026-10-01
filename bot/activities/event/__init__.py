"""
event — "Event" activity.

- run.py:           entry point, `run(bot, settings)`: chạy lần lượt các nhiệm vụ đã bật
- common.py:        phần dùng chung (quà đăng nhập, tìm Event Center, bấm nút event)
- constants.py:     image folders, limits and action names
- gather_troops/:   nhiệm vụ event Gather Troops, mỗi nhiệm vụ một thư mục
                    (cultivate_generals/run.py + constants.py, ...)
"""
from .run import run

__all__ = ["run"]
