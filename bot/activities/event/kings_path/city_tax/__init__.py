"""
city_tax — King's Path: City Tax (Day 1, tab phụ "City Tax")
(key `kings_path_city_tax`, ô chọn ở group King's Path trong ui/tabs/event.json).

- run.py:       `run(bot, task, state)` — flow của nhiệm vụ
- constants.py: ảnh riêng của nhiệm vụ
"""
from .constants import KEY
from .run import run

__all__ = ["KEY", "run"]
