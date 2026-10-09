"""
three_day — event 3 ngày trong Event Center (tab Limited), VD "Precious Vegetation": làm nhiệm vụ
Alliance (donate) và Heal, nhận quà, đổi quà theo thứ tự ưu tiên.

- run.py:       `run(bot, settings)` — flow; settings là cấu hình tab Event (group "three_day")
- constants.py: ảnh, toạ độ, ngưỡng; icon event mới thả vào Images/EventCenter/ThreeDay/Icons/
"""
from .run import run

__all__ = ["run"]
