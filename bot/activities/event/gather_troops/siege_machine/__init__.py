"""
siege_machine — Gather Troops: Siege Machine (Day 4, tab phụ bên trái)
(key `siege_machine`, ô chọn ở group Gather Troops).

- run.py:       `run(bot, task, state)` — cấu hình TroopTask, flow chung ở ../train_troop
- constants.py: ảnh, ngưỡng riêng của nhiệm vụ
"""
from .constants import KEY
from .run import run

__all__ = ["KEY", "run"]
