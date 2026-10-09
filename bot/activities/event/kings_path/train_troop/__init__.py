"""
train_troop — King's Path: Train Troop (Day 3, tab phụ "Strong Troops")
(key `kings_path_train_troop`, ô chọn ở group King's Path trong ui/tabs/event.py).

- run.py:       `run(bot, task, state)` — flow của nhiệm vụ (code riêng, dùng lại bước chung của
                Gather Troops bằng import, không sửa Gather Troops)
- tier.py:      chọn lính cấp I (vuốt hàng cấp sang trái, 4 loại lính)
- constants.py: ảnh riêng của nhiệm vụ
"""
from .constants import KEY
from .run import run

__all__ = ["KEY", "run"]
