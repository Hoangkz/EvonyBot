"""
viking_summon — nhiệm vụ Event Center "Viking Challenge": triệu hồi boss Viking của mình (Summon).

- run.py:       entry point, `run(bot, settings)`, JOB cho worker (priority.py) và cửa sổ thời gian của sự kiện
- constants.py: ảnh, toạ độ, giới hạn
"""
from .run import run

__all__ = ["run"]
