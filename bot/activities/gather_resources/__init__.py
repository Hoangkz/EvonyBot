"""
gather_resources — "Gather Resources" activity: gửi các đội quân đi thu thập tài nguyên (lúa, gỗ, đá, sắt).

- run.py:       entry point, `run(bot, settings)`, JOB cho bảng bot/worker/priority.py
- constants.py: loại tài nguyên, cấp, số đội, ảnh Images/Gather/, toạ độ, key lưu DB
- FLOW.md:      luồng chi tiết
"""
from .run import JOB, run

__all__ = ["JOB", "run"]
