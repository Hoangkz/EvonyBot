"""
run.py — flow nhiệm vụ <tên nhiệm vụ> (<Event>, Day N).

Phần đi từ màn chính tới màn event nằm trong run_task() (event/common.py), nhiệm vụ
chỉ khai báo ảnh riêng (_TARGETS) và hàm handle.

Flow:
1. Màn chính -> quà đăng nhập -> nút dưới Event Center -> danh sách event -> icon event
   (run_task, giống mọi nhiệm vụ Event).
2. Màn event: tab chưa chọn thì bấm.
3. Tab đang chọn: làm nhiệm vụ, xong thì đánh dấu xong (tới lần reset server).
"""
from ...common import EVENT_OPENED, HANDLED, STOP, EventState, run_task
from ...constants import GATHER_TROOPS_ICON
from .constants import (
    KEY,
    ON_TAB,
    OPEN_TAB,
    REGIONS,
    TAB,
    TAB_SELECTED,
    THRESHOLDS,
)

NAME = "My Task"   # tên trong log


def run(bot, task: dict, state: EventState):
    """`task` là settings của nhiệm vụ: ô tích {"enabled", "day"} /
    ô chọn {"value", "level"?, "day"}."""
    if bot.is_daily_done(KEY):
        bot.log(f"{NAME}: already done")
        return

    def handle(action, pos, screen):
        """None = không phải action của nhiệm vụ (run_task / handle_common lo),
        HANDLED = đã xử lý -> quét lại, STOP = nhiệm vụ kết thúc."""
        if action == EVENT_OPENED:
            return None              # vừa mở màn event: quét tiếp
        if action == OPEN_TAB:
            bot.tap(*pos, delay=2)
        elif action == ON_TAB:
            # TODO: phần riêng của nhiệm vụ.
            bot.mark_daily_done(KEY)
            return STOP
        else:
            return None
        return HANDLED

    run_task(bot, state, NAME, GATHER_TROOPS_ICON, handle,
             targets=_TARGETS, regions=REGIONS, thresholds=THRESHOLDS)


# Ảnh riêng của nhiệm vụ: màn sau trước, màn trước sau; "đang chọn" trước "chưa chọn".
_TARGETS = [
    (TAB_SELECTED, ON_TAB),
    (TAB, OPEN_TAB),
]
