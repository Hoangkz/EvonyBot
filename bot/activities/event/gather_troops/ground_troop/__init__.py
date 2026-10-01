"""
ground_troop — Gather Troops: Ground Troop (Day 2)
(key `ground_troop`, ô chọn ở group Gather Troops).

- run.py:       `run(bot, task, state)` — flow của nhiệm vụ
- constants.py: ảnh, ngưỡng và action riêng của nhiệm vụ
"""
from .constants import KEY
from .run import run

__all__ = ["KEY", "run"]
