"""
refine_equipment — "Refine Equipment" activity: tinh luyện trang bị ở Lò rèn, cày tới khi có thuộc tính mong muốn.

- run.py:       entry point, `run(bot, settings)`, JOB cho bảng bot/worker/priority.py
- constants.py: key lưu DB, key settings, giới hạn
- FLOW.md:      luồng chi tiết; TODO.md: phần còn thiếu (chọn trang bị, đọc thuộc tính)
"""
from .run import JOB, run

__all__ = ["JOB", "run"]
