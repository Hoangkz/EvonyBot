"""
train_troop — flow chung của các nhiệm vụ train lính trong Gather Troops (Ground Troop,
Mounted Troop, ...). Nhiệm vụ khai báo một TroopTask (tab Day, tab phụ, ảnh cấp lính)
rồi gọi run(bot, task, state, troop).

- run.py:       TroopTask, run() — flow
- constants.py: ảnh / ngưỡng của màn Train, Training Speedup dùng chung
"""
from .run import TroopTask, run

__all__ = ["TroopTask", "run"]
