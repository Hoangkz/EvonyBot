"""
cultivate_generals — Gather Troops: "Cultivate Generals for N time(s)"
(key `gather_troops_cultivate_generals`, ô tích ở group Gather Troops).

- run.py:       `run(bot, task, state)` — flow của nhiệm vụ
- constants.py: ảnh, ngưỡng và action riêng của nhiệm vụ
"""
from .constants import KEY
from .run import run

__all__ = ["KEY", "run"]
