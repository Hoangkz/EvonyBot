"""
donate — King's Path: Donate (Day 2, tab phụ "Teamwork")
(key `kings_path_donate`, ô chọn ở group King's Path trong ui/tabs/event.py).

- run.py:       `run(bot, task, state)` — flow của nhiệm vụ
- constants.py: ảnh riêng của nhiệm vụ
"""
from .constants import KEY
from .run import run

__all__ = ["KEY", "run"]
