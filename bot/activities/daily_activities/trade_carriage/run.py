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
    DISPATCH_TRIES,
    DONE_IMAGES,
    FOLDER,
    GIFT_BOXES,
    GIFT_MAX,
    GIFT_POPUP,
    GIFT_POPUP_WAITS,
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
    _claim_gifts(bot)   # ưu tiên: nhận quà trước khi làm gì khác
    dispatched = 0
    out_of_turns = False
    for _ in range(DISPATCH_MAX):
        if not _dispatch_opens(bot):
            if bot.find(DISPATCH, threshold=THRESHOLD) is None:
                bot.record(f"{LABEL}: Dispatch button not found")
            else:
                # Bấm Dispatch DISPATCH_TRIES lần (mỗi lần xét lại hộp quà / bảng che màn) mà bảng hàng không mở: hết lượt hôm nay.
                bot.record(f"{LABEL}: Dispatch did not open the goods panel after {DISPATCH_TRIES} tries (no transports left?)")
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


def _dispatch_opens(bot) -> bool:
    """Bấm Dispatch và chờ bảng hàng hoá (Select Formation); không mở thì thử lại, tối đa DISPATCH_TRIES lần. Mỗi lần bấm
    xong chuẩn bị lại màn (`_ready`: nhận hộp quà, đóng bảng che) để lần đầu sau khi nhận quà không bị coi nhầm là hết lượt."""
    for _ in range(DISPATCH_TRIES):
        if not _ready(bot):
            return False
        bot.tap(*bot.find(DISPATCH, threshold=THRESHOLD), delay=RESULT_WAIT)
        if bot.wait_for(SELECT_FORMATION, timeout=POPUP_WAIT, threshold=THRESHOLD) is not None:
            return True
    return False


def _find_gift(bot):
    """Tâm hộp quà đầu tiên tìm thấy (thử lần lượt mọi ảnh trong GIFT_BOXES), hoặc None."""
    screen = bot.screenshot()
    return next((pos for path in GIFT_BOXES
                 if (pos := bot.find(path, screen=screen, threshold=THRESHOLD)) is not None), None)


def _claim_gifts(bot):
    """Ưu tiên đầu tiên mỗi khi ở màn My Carriage: còn hộp quà thì bấm, chờ 1 giây xem popup nhận thưởng (GIFT_POPUP)
    hiện chưa: hiện -> Back, rồi xét hộp quà kế (nhiều xe tới cùng lúc); chưa hiện -> chờ thêm tối đa GIFT_POPUP_WAITS lần
    (mỗi lần 1 giây), vẫn chưa hiện thì bỏ qua quà, làm các bước tiếp theo."""
    for _ in range(GIFT_MAX):
        box = _find_gift(bot)
        if box is None:
            return
        bot.record(f"{LABEL}: claiming gift box")
        bot.tap(*box)
        for _ in range(1 + GIFT_POPUP_WAITS):
            bot.sleep(1)
            if bot.find(GIFT_POPUP) is not None:
                bot.log(f"{LABEL}: gift claimed, back")
                bot.back(delay=1)
                break
        else:
            bot.log(f"{LABEL}: no claim popup after {1 + GIFT_POPUP_WAITS}s, continue")
            return


def _ready(bot) -> bool:
    """Màn My Carriage sẵn sàng Dispatch: nhận hộp quà trước (`_claim_gifts`), đóng bảng còn mở. False nếu không thấy nút
    Dispatch."""
    for _ in range(4):
        _claim_gifts(bot)
        if bot.find(DISPATCH, threshold=THRESHOLD) is not None:
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
