"""
offer — King's Path: Offer (Day 3, tab phụ "God's Blessing")
(key `kings_path_offer`, ô chọn ở group King's Path trong ui/tabs/event.json).

- run.py:       `run(bot, task, state)` — flow của nhiệm vụ
- constants.py: ảnh riêng của nhiệm vụ
"""
from .constants import KEY
from .run import run

__all__ = ["KEY", "run"]
