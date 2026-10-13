"""
run.py — Daily Activities "Trade Carriage": phần sau Go (màn Trade Carriage -> Dispatch tối đa 4 lần).
Mở Quests -> Activity, tìm dòng, bấm Go: ../common.py open_task_or_finish. Ảnh / hằng số: constants.py.

Sau Go ra thẳng màn Trade Carriage. Có hộp quà thì bấm nhận trước. Mỗi lần: Dispatch -> bảng hàng hoá; thấy "First
Refresh Free" thì bấm Refresh Goods (hiện popup hỏi lại vì xe đang cam -> Back) -> Select Formation -> bấm tab My Carriage
đóng bảng, về lại màn My Carriage. Làm đủ DISPATCH_MAX lần (hoặc tới khi game không cho Dispatch nữa) -> báo xong hôm
nay -> Back về thành.
"""
from ..common import Task, mark_task_done
from .constants import (
    ACTIONS,
    BACKS_AFTER,
    DISPATCH,
    DISPATCH_MAX,
    DONE_IMAGES,
    FOLDER,
    GIFT_BOX,
    KEY,
    LABEL,
    MARCH_BUTTON,
    MARCH_WAIT,
    POPUP_WAIT,
    REFRESH_CONFIRM,
    REFRESH_FREE,
    RESULT_WAIT,
    REVIEW_CLOSE,
    SCREEN_WAIT,
    SELECT_FORMATION,
    THRESHOLD,
    TRADE_TITLE,
)


def after_go(bot) -> bool:
    """Sau khi open_task bấm Go: Dispatch tối đa DISPATCH_MAX lần. True (và báo xong hôm nay) khi đã Dispatch ít
    nhất một lần hoặc game không cho Dispatch nữa (hết lượt hôm nay); False nếu không vào được màn Trade Carriage
    hoặc không Dispatch được lần nào."""
    if bot.wait_for(TRADE_TITLE, timeout=SCREEN_WAIT, threshold=THRESHOLD) is None:
        bot.record(f"{LABEL}: Trade Carriage screen not shown")
        _leave(bot)
        return False
    dispatched = 0
    out_of_turns = False
    for _ in range(DISPATCH_MAX):
        if not _ready(bot):
            bot.record(f"{LABEL}: Dispatch button not found")
            break
        bot.tap(*bot.find(DISPATCH, threshold=THRESHOLD), delay=RESULT_WAIT)
        if bot.wait_for(SELECT_FORMATION, timeout=POPUP_WAIT, threshold=THRESHOLD) is None:
            bot.record(f"{LABEL}: Dispatch did not open the goods panel (no transports left?)")
            out_of_turns = True
            break
        _free_refresh(bot)
        formation = bot.wait_for(SELECT_FORMATION, timeout=POPUP_WAIT, threshold=THRESHOLD)
        if formation is None:
            bot.record(f"{LABEL}: Select Formation not shown")
            break
        bot.tap(*formation, delay=RESULT_WAIT)
        march = bot.wait_for(MARCH_BUTTON, timeout=MARCH_WAIT, threshold=THRESHOLD)
        if march is None:
            bot.record(f"{LABEL}: March button not shown")
            break
        bot.tap(*march, delay=RESULT_WAIT)
        bot.tap_percent(*REVIEW_CLOSE, delay=RESULT_WAIT)
        dispatched += 1
        bot.record(f"{LABEL}: dispatched {dispatched}/{DISPATCH_MAX}")
    finished = dispatched > 0 or out_of_turns
    if finished:
        mark_task_done(bot, TASK)
    _leave(bot)
    return finished


def _ready(bot) -> bool:
    """Màn My Carriage sẵn sàng Dispatch: bấm hộp quà (nhận thưởng xe đã tới) nếu có, đóng bảng còn mở. False nếu
    không thấy nút Dispatch."""
    for _ in range(4):
        screen = bot.screenshot()
        box = bot.find(GIFT_BOX, screen=screen, threshold=THRESHOLD)
        if box is not None:
            bot.record(f"{LABEL}: claiming gift box")
            bot.tap(*box, delay=RESULT_WAIT)
            continue
        if bot.find(DISPATCH, screen=screen, threshold=THRESHOLD) is not None:
            return True
        bot.tap_percent(*REVIEW_CLOSE, delay=RESULT_WAIT)   # bảng / popup còn che màn
    return bot.find(DISPATCH, threshold=THRESHOLD) is not None


def _free_refresh(bot):
    """Bảng hàng hoá: còn "First Refresh Free" thì bấm Refresh Goods một lần. Hiện popup hỏi lại (xe đang cam) -> Back."""
    free = bot.find(REFRESH_FREE, threshold=THRESHOLD)
    if free is None:
        return
    bot.tap(*free, delay=RESULT_WAIT)
    if bot.find(REFRESH_CONFIRM, threshold=THRESHOLD) is not None:
        bot.log(f"{LABEL}: carriage is already good, not refreshing")
        bot.back(delay=RESULT_WAIT)
    else:
        bot.log(f"{LABEL}: free refresh used")


def _leave(bot):
    """Back tới khi không còn màn Trade Carriage (về thành)."""
    for _ in range(BACKS_AFTER):
        if bot.find(TRADE_TITLE, threshold=THRESHOLD) is None:
            break
        bot.back(delay=RESULT_WAIT)


TASK = Task(LABEL, FOLDER, DONE_IMAGES, ACTIONS, lambda bot, action, pos, screen: False, key=KEY)
