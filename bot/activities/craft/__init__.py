"""
craft — "Craft" activity: chế tạo trang bị vàng trở lên đã tích ở tab Craft, mỗi trang bị một số lượng.

- run.py:       entry point, `run(bot, settings)`, JOB cho bảng bot/worker/priority.py
- constants.py: nhóm trang bị, thư mục ảnh Images/Craft/<nhóm>/NN_<Tên>.png, key lưu DB và `catalog()`
"""
from .run import JOB, run

__all__ = ["JOB", "run"]
