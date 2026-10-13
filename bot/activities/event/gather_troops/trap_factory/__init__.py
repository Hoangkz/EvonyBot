"""
trap_factory — Gather Troops: Trap Factory (Day 4, tab phụ bên phải, xây bẫy)
(key `trap_factory`, ô chọn ở group Gather Troops).

- run.py:       `run(bot, task, state)` — cấu hình TroopTask, flow chung ở ../train_troop
- constants.py: ảnh, ngưỡng riêng của nhiệm vụ
"""
from .constants import KEY
from .run import run

__all__ = ["KEY", "run"]
