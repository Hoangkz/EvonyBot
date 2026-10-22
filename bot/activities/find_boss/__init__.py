"""
find_boss — "Find Boss" activity: ra bản đồ thế giới, quét một hình quạt quanh thành tìm boss (bot/common/boss_scan.py),
chia sẻ boss đang tích vào liên minh, xong thì về toạ độ của mình rồi quét tiếp. Chỉ chạy khi rảnh (không còn nhiệm vụ nào khác).

- run.py:       entry point, `run(bot, settings)`, JOB cho bảng bot/worker/priority.py
- constants.py: key lưu DB, ảnh, giá trị mặc định của tab
"""
from .run import JOB, run

__all__ = ["JOB", "run"]
