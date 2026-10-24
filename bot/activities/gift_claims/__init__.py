"""Gift Claims: ba hoạt động độc lập, mỗi hoạt động có hàm ``run(bot)`` riêng.

- ``valuable_event.run``: Valuable Event.
- ``super_value_return.run``: Login Gifts, Empire Depot và các tab cùng màn.
- ``event_center.run``:   Back to Territory (icon ngoài) + các event con trong Event Center.

Mỗi hoạt động có danh sách nhiệm vụ (key trong ``daily_done``); vòng kiểm tra 3 lần nằm ở ``scan.py``. Worker ưu tiên
Event Center trước Valuable Event và Super Value Return (``bot/worker/priority.py``, nhóm "Gift Claims"), khi ô
"Claim Event Gifts" ở tab Daily Activities được tích (``settings["General"]["gift_claims"]`, mặc định bật).
"""
from importlib import import_module
import time

from . import event_center, valuable_event
from .valuable_event import super_value_return
# Lối tắt cho nơi từng import một luồng quà cụ thể từ ``gift_claims``; phần cài đặt nằm ở ``valuable_event/``.
back_to_territory = import_module(f"{__name__}.back_to_territory.run")
empire_depot = import_module(f"{__name__}.valuable_event.empire_depot.run")
limited_offer = import_module(f"{__name__}.valuable_event.limited_offer.run")
login_gifts = import_module(f"{__name__}.valuable_event.login_gifts.run")
from .common import (TEXT_CLAIM_CONTROLS, back_if_close_x,
                     claim_fixed_controls, claim_sparkles, mark_task_done,
                     return_home, skipped_for_run)
from .screens import GiftScreen

RETRY_WINDOW_SECONDS = 120.0
RETRY_AFTER_ATTR = "_gift_claims_zone_retry_after"


def _retry_after(ctx) -> dict[str, float]:
    values = getattr(ctx, RETRY_AFTER_ATTR, None)
    if not isinstance(values, dict):
        values = {}
        setattr(ctx, RETRY_AFTER_ATTR, values)
    return values


def job(zone) -> dict:
    """Dòng nhiệm vụ cho bảng ``priority.py``: chạy ``zone.run`` khi ô nhận quà được tích; xong khi key tổng của zone có trong DB."""
    def run(ctx, _settings):
        window_started = time.monotonic()
        completed = bool(zone.run(ctx))
        retry_after = _retry_after(ctx)
        if completed:
            retry_after.pop(zone.KEY, None)
        else:
            # The next eligibility is measured from when this zone started,
            # not from when a slow 30-device run finally returned.
            retry_after[zone.KEY] = window_started + RETRY_WINDOW_SECONDS
            ctx.record(f"Gift Claims: {zone.KEY} còn PENDING; nghỉ đến lượt "
                       "120s kế tiếp để chạy khu nhận quà tiếp theo")
        return completed

    def done(ctx, _settings):
        if ctx.is_daily_done(zone.KEY) or skipped_for_run(ctx, zone.KEY):
            return True
        return time.monotonic() < _retry_after(ctx).get(zone.KEY, 0.0)

    return {"run": run,
            "enabled": lambda settings: bool((settings.get("General") or {}).get("gift_claims", True)),
            "done": done}


__all__ = ["event_center", "super_value_return", "valuable_event", "job"]
