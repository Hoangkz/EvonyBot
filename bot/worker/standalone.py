"""
standalone.py — khai báo nhiệm vụ của các nhóm chỉ có một nhiệm vụ: Alliance Capacity, Open Gift Box, Black Market,
Battlefield Shop (TaskDef, xem task_def.py); registry.py gom lại. Các nhóm này chỉ làm thao tác trong game
(bot/activities/<nhóm>/run.py); chọn chạy, "xong hôm nay", chạy một lần là việc của worker.
"""
from ..activities.alliance_capacity.run import run as alliance_capacity_run
from ..activities.battlefield_shop.run import run as battlefield_shop_run
from ..activities.black_market.run import run as black_market_run
from ..activities.open_gift_box.constants import KEY as OPEN_GIFT_BOX_KEY
from ..activities.open_gift_box.run import run as open_gift_box_run
from .task_def import TaskDef, always


def run_open_gift_box(ctx, settings: dict):
    """Mở mọi hộp quà đã chọn; mở hết (run trả done=True) thì lưu "xong hôm nay"."""
    if open_gift_box_run(ctx, settings).done:
        ctx.mark_daily_done(OPEN_GIFT_BOX_KEY)


TASKS = [
    TaskDef("alliance_capacity", "Alliance Capacity", always, alliance_capacity_run),
    TaskDef("open_gift_box", "Open Gift Box", always, run_open_gift_box),
    # once: xong rồi thì không làm lại khi qua mốc reset (chỉ chạy lại khi Stop rồi Start).
    TaskDef("black_market_market", "Black Market", always, black_market_run, once=True),
    TaskDef("battlefield_shop", "Battlefield Shop", always, battlefield_shop_run),
]
