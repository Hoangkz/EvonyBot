"""Gift Claims: hai hoạt động độc lập, mỗi hoạt động có hàm ``run(bot)`` riêng.

- ``valuable_event.run``: Valuable Event + Super Value Return (khu quà ngoài Event Center).
- ``event_center.run``:   Back to Territory (icon ngoài) + các event con trong Event Center.

Mỗi hoạt động có danh sách nhiệm vụ (key trong ``daily_done``); vòng kiểm tra 3 lần nằm ở ``scan.py``. Hiện chưa nối vào
bảng nhiệm vụ của worker (``bot/worker/priority.py``).
"""
from importlib import import_module

from . import event_center, valuable_event
# Lối tắt cho nơi từng import một luồng quà cụ thể từ ``gift_claims``; phần cài đặt nằm ở ``valuable_event/``.
back_to_territory = import_module(f"{__name__}.back_to_territory.run")
empire_depot = import_module(f"{__name__}.valuable_event.empire_depot.run")
limited_offer = import_module(f"{__name__}.valuable_event.limited_offer.run")
login_gifts = import_module(f"{__name__}.valuable_event.login_gifts.run")
super_value_return = import_module(f"{__name__}.valuable_event.super_value_return.run")
from .common import (TEXT_CLAIM_CONTROLS, back_if_close_x,
                     claim_fixed_controls, claim_sparkles, mark_task_done,
                     return_home)
from .screens import GiftScreen

__all__ = ["event_center", "valuable_event"]
