"""Gift Claims: ba hoạt động độc lập, mỗi hoạt động có hàm ``run(bot)`` riêng.

- ``valuable_event.run``: Valuable Event.
- ``super_value_return.run``: Login Gifts, Empire Depot và các tab cùng màn.
- ``event_center.run``:   Back to Territory (icon ngoài) + các event con trong Event Center.

Mỗi hoạt động có danh sách nhiệm vụ (key trong ``daily_done``) và một key riêng của cả hoạt động (``KEY``); làm xong thì tự
lưu key đó. Dòng của từng hoạt động trong ``bot/worker/priority.py`` dựng bằng ``job(zone)`` (giống ``daily_job`` của Daily
Activities): chung một ô tích "Claim Event Gifts" ở tab Daily Activities (``settings["General"]["gift_claims"]``, mặc định
bật); worker chỉ hỏi hôm nay key đó có trong DB chưa.
"""
from importlib import import_module

from . import event_center, super_value_return, valuable_event
# Lối tắt cho nơi từng import một luồng quà cụ thể từ ``gift_claims``; phần cài đặt nằm ở ``valuable_event/`` và ``super_value_return/``.
back_to_territory = import_module(f"{__name__}.back_to_territory.run")
empire_depot = import_module(f"{__name__}.super_value_return.empire_depot.run")
limited_offer = import_module(f"{__name__}.valuable_event.limited_offer.run")
login_gifts = import_module(f"{__name__}.super_value_return.login_gifts.run")
from .common import (TEXT_CLAIM_CONTROLS, back_if_close_x,
                     claim_fixed_controls, claim_sparkles, mark_task_done,
                     return_home)
from .screens import GiftScreen


def enabled(settings: dict) -> bool:
    """Ô "Claim Event Gifts" ở tab Daily Activities được tích (mặc định bật): chung cho mọi hoạt động Gift Claims."""
    return bool((settings.get("General") or {}).get("gift_claims", True))


def job(zone) -> dict:
    """Dòng nhiệm vụ cho bảng ``priority.py``, giống ``daily_job`` của Daily Activities: chạy khi ô "Claim Event Gifts" được
    tích; xong hôm nay = key riêng của hoạt động (``zone.KEY``) có trong DB. ``zone.run`` tự lưu key đó khi làm xong."""
    return {"run": lambda ctx, _settings: zone.run(ctx),
            "enabled": enabled,
            "done": lambda ctx, _settings: ctx.is_daily_done(zone.KEY)}


__all__ = ["event_center", "super_value_return", "valuable_event", "enabled", "job"]
