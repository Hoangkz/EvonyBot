"""
run.py — nhiệm vụ Black Market (King's Path, Day 5): Day 5 -> tab phụ "Market Trade" -> Go ->
Chợ -> Black Market -> mua cho đủ mục tiêu. Flow chung tới Go: xem ../path_task.py; mở Chợ:
../building.py.

Màn Black Market (6 món ở vị trí cố định, mỗi bước chụp 1 ảnh):
1. Vừa bấm một món mà hiện hộp "Are you sure you want to purchase ...?" -> Confirm (+1 lần mua).
2. Bỏ các món trả bằng kim cương; món còn mua được (nút giá xanh) -> bấm, mỗi món 1 lần mỗi bộ
   hàng (bấm mà không ra hộp xác nhận thì bỏ qua món đó).
3. Mua hết -> cắt ô vật phẩm 1 -> Instant Refresh (hết lượt miễn phí thì bằng kim cương; có hộp
   xác nhận thì Confirm) -> chờ 2 s -> ô 1 đã khác = refresh xong, mua tiếp bộ mới; còn giống thì
   chờ thêm 1 s (tối đa 10 lần), vẫn giống thì bấm Refresh lại.
Dừng (Back): số đã mua (OCR dòng Go) + số mua lượt này >= mục tiêu -> xong cả vòng event
(mark_target_reached). Chưa mua đủ mà dừng (hết hàng / không thấy Instant Refresh / kẹt) -> không lưu done,
lượt sau đọc lại số đã mua ở dòng Go rồi mua tiếp; bị ngắt (120 s / boss) cũng vậy.
"""
import numpy as np

from ...city_building import MARKET
from ...common import EventState, mark_target_reached
from .. import path_task
from ..building import open_menu
from ..constants import SCREEN_WAIT
from .constants import (
    BUY_WAIT,
    CONFIRM,
    DAY,
    GEM,
    GEM_THRESHOLD,
    INSTANT_REFRESH,
    ITEM_BOX,
    KEY,
    MAX_IDLE_STEPS,
    MENU_BLACK_MARKET,
    REFRESH_CHECKS,
    REFRESH_FIRST_CHECK,
    REFRESH_TRIES,
    SAME_ITEM,
    SLOT_GREEN,
    SLOT_HALF,
    SLOTS,
    TAB,
    TAB_INDEX,
    TAB_SELECTED,
    TITLE,
)

NAME = "Black Market"


def _buy(bot, path, done, target):
    """Sau Go: mở Black Market rồi mua các món không trả bằng kim cương cho đủ mục tiêu."""
    _, pos = open_menu(bot, NAME, MARKET, {"black_market": MENU_BLACK_MARKET})
    if pos is None:
        return None
    bot.tap(*pos)
    if bot.wait_for(TITLE, timeout=SCREEN_WAIT) is None:
        bot.record(f"{NAME}: Black Market screen not shown")
        return None
    progress = done or 0
    tried = set()        # món đã thử trong bộ hàng hiện tại
    last = None          # "buy" (vừa bấm một món) / "refresh" (vừa bấm Instant Refresh) / None
    idle = 0             # số bước liên tiếp chưa mua được món nào
    while idle < MAX_IDLE_STEPS:
        idle += 1
        if progress >= target:
            return _finish(bot, path, f"bought {progress} / {target}, done")
        screen = bot.screenshot()
        if bot.find(TITLE, screen=screen) is None:
            bot.record(f"{NAME}: not on Black Market screen, stop")
            return None
        confirm = bot.find(CONFIRM, screen=screen)
        if confirm is not None and last == "buy":
            progress += 1
            idle = 0
            bot.log(f"{NAME}: buy confirmed ({progress} / {target})")
            bot.tap(*confirm, delay=BUY_WAIT)
            last = None
            continue
        slot = next((i for i, (x, y) in enumerate(SLOTS)
                     if i not in tried and _buyable(bot, screen, x, y)), None)
        if slot is not None:
            tried.add(slot)
            bot.tap(*SLOTS[slot], delay=BUY_WAIT)
            last = "buy"
            continue
        if bot.find(INSTANT_REFRESH, screen=screen) is None:
            # Chưa mua đủ: không lưu done (kể cả hôm nay), lượt sau đọc lại tiến độ rồi thử lại.
            bot.record(f"{NAME}: nothing to buy and no Instant Refresh ({progress} / {target}), stop")
            bot.back(delay=1)
            return None
        bot.record(f"{NAME}: all bought, Instant Refresh ({progress} / {target})")
        if not _refresh(bot, screen):
            bot.record(f"{NAME}: items did not change after {REFRESH_TRIES} refreshes, stop")
            return None
        tried.clear()
        last = None
    bot.record(f"{NAME}: nothing bought in {MAX_IDLE_STEPS} steps ({progress} / {target}), stop")
    return None


def _refresh(bot, screen) -> bool:
    """Bấm Instant Refresh và chờ tới khi ô vật phẩm 1 khác ảnh trước khi bấm (= đã ra hàng mới).
    Hộp xác nhận (refresh bằng kim cương) -> Confirm. True nếu đã ra hàng mới."""
    before = bot.crop(screen, *ITEM_BOX)
    for _ in range(REFRESH_TRIES):
        refresh = bot.find(INSTANT_REFRESH)
        if refresh is None:
            return False
        bot.tap(*refresh, delay=REFRESH_FIRST_CHECK)
        for _ in range(REFRESH_CHECKS):
            now = bot.screenshot()
            confirm = bot.find(CONFIRM, screen=now)
            if confirm is not None:
                bot.log(f"{NAME}: confirm paid refresh")
                bot.tap(*confirm, delay=REFRESH_FIRST_CHECK)
                continue
            if bot.best_match(before, screen=bot.crop(now, *ITEM_BOX))[0] < SAME_ITEM:
                return True
            bot.sleep(1)
        bot.log(f"{NAME}: items unchanged after {REFRESH_CHECKS} checks, Refresh again")
    return False


def _buyable(bot, screen, x: int, y: int) -> bool:
    """Nút giá còn xanh (chưa mua) và không có icon kim cương."""
    hw, hh = SLOT_HALF
    box = screen[y - hh:y + hh, x - hw:x + hw].astype(np.int16)
    if float((box[..., 1] - box[..., 2]).mean()) <= SLOT_GREEN:
        return False
    area = bot.crop(screen, x - hw, y - hh, 2 * hw, 2 * hh)
    return bot.find(GEM, threshold=GEM_THRESHOLD, screen=area) is None


def _finish(bot, path, message: str):
    """Đã mua đủ mục tiêu: Back, xong cả vòng event."""
    bot.log(f"{NAME}: {message}")
    bot.back(delay=1)
    mark_target_reached(bot, path.key)
    return None


PATH = path_task.PathTask(
    key=KEY, name=NAME, day=DAY, tab_index=TAB_INDEX,
    tab_selected=TAB_SELECTED, tab=TAB, after_go=_buy,
)


def run(bot, task: dict, state: EventState):
    """`task` là settings của nhiệm vụ: {"value": int, "day": int}."""
    path_task.run(bot, task, state, PATH)
