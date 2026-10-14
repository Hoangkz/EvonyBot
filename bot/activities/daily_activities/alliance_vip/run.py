"""
run.py — Daily Activities "Alliance VIP": mua sách "100 VIP Points" ở Alliance Shop, nhóm Monthly rồi nhóm Daily Sale.

Flow (mỗi loại có dấu "xong hôm nay" riêng, xem constants.py):
1. Màn chính -> Liên minh -> (cuộn nếu cần) -> "Alliance Shop" -> màn Alliance Shop.
2. Monthly (đầu trang, chưa xong hôm nay): tìm sách VIP nằm TRÊN tiêu đề "Daily Sale". Nút giá xám (VD chưa có thẻ tháng) -> không mua,
   đánh dấu xong hôm nay luôn. Nút xanh -> bấm sách -> popup mua: "+" 5 lần -> bấm mua -> đánh dấu xong.
3. Daily: kéo thật nhanh xuống cuối trang (sách luôn ở cuối, ngay trên tiêu đề "Weekly Sale") rồi tìm sách giữa "Daily Sale" và
   "Weekly Sale", cùng logic xám / xanh. Tới tiêu đề Weekly Sale mà không có sách VIP phía trên -> đánh dấu xong hôm nay.
4. Back về màn Liên minh -> màn chính. Không tới được shop / không thấy sách / popup mua không đóng -> loại đó không đánh dấu, lần sau thử lại.
Lỗi thì lưu `daily_alliance_vip_error` vào DB (save_errors).
"""
import cv2

from ....common import click_images, delay, exit_images, find_first, go_home
from ...result import save_errors
from .constants import (
    ALLIANCE_NAV,
    BUY_DY,
    BUY_WAIT,
    CONFIRM_BUTTON,
    CONFIRM_CHECKS,
    DAILY_HEADER,
    DAY_KEY,
    LABEL,
    MONTH_KEY,
    NAV_MAX_STEPS,
    PLUS,
    PLUS_TAPS,
    PLUS_WAIT,
    POPUP_CHECKS,
    PRICE_BOX,
    PRICE_DY,
    PRICE_MIN_SATURATION,
    SCROLLS,
    SETTLE_TRIES,
    SHOP_ROW,
    SHOP_TITLE,
    BOTTOM_SETTLE,
    BOTTOM_SWIPE,
    BOTTOM_SWIPE_DURATION,
    BOTTOM_SWIPES,
    SWIPE,
    SWIPE_DURATION,
    WEEKLY_HEADER,
    VIP_ICON,
    VIP_THRESHOLD,
)

_ON_SHOP, _TAP, _BACK, _SCROLL, _OUT = "on_shop", "tap", "back", "scroll", "out_alliance"
_ALLIANCE_BUTTON, _ALLIANCE_SCROLL, _OUT_ALLIANCE = ALLIANCE_NAV


def _open_shop(bot) -> bool:
    """Màn chính -> Liên minh -> Alliance Shop. True nếu tới màn Alliance Shop."""
    targets = [
        (SHOP_TITLE, _ON_SHOP),
        (_OUT_ALLIANCE, _OUT),
        (SHOP_ROW, _TAP),
        (_ALLIANCE_SCROLL, _SCROLL),
        *[(path, _BACK) for path in exit_images()],
        *[(path, _TAP) for path in click_images()],
        (_ALLIANCE_BUTTON, _TAP),
    ]
    for _ in range(NAV_MAX_STEPS):
        screen = bot.screenshot()
        action, pos = find_first(bot, screen, targets, top_left={_OUT})
        if action == _ON_SHOP:
            return True
        if action == _TAP:
            bot.tap(*pos)
            delay(bot, 2)
        elif action == _SCROLL:
            bot.swipe_percent(50, 87, 50, 54, duration=1.0)
            delay(bot)
        elif action == _OUT:
            bot.tap(pos[0] + 40, pos[1] + 40)
            delay(bot, 2)
            bot.back()
            delay(bot, 3)
        elif action == _BACK:
            bot.back()
            delay(bot, 2)
        else:
            go_home(bot, screen)
            delay(bot, 2)
    bot.record(f"{LABEL}: Alliance Shop not reached")
    return False


def _price_green(bot, screen, icon) -> bool:
    """Nút giá dưới sách còn xanh (mua được); xám = không mua được."""
    w, h = PRICE_BOX
    x, y = icon[0] - w // 2, icon[1] + PRICE_DY - h // 2
    box = bot.crop(screen, x, y, w, h)
    return float(cv2.cvtColor(box, cv2.COLOR_BGR2HSV)[..., 1].mean()) >= PRICE_MIN_SATURATION


def _vip_icons(bot, screen, scrolled: bool) -> tuple[list, list]:
    """(sách Monthly, sách Daily) trên màn, phân biệt bằng hai tiêu đề nhóm: "Daily Sale" (đầu nhóm Daily) và "Weekly Sale" (cuối nhóm
    Daily, đầu nhóm Weekly). Monthly = sách TRÊN tiêu đề Daily Sale; Daily = sách giữa Daily Sale và Weekly Sale (nếu một tiêu đề đã ra khỏi
    màn: trên Weekly Sale / dưới Daily Sale). Không thấy tiêu đề nào thì dựa vào việc đã cuộn chưa (chưa cuộn = Monthly)."""
    icons = sorted(bot.find_all(VIP_ICON, threshold=VIP_THRESHOLD, screen=screen), key=lambda p: p[1])
    daily_header = bot.find(DAILY_HEADER, screen=screen)
    weekly_header = bot.find(WEEKLY_HEADER, screen=screen)
    if daily_header is not None:
        monthly = [p for p in icons if p[1] < daily_header[1]]
        daily = [p for p in icons if p[1] > daily_header[1] and (weekly_header is None or p[1] < weekly_header[1])]
        return monthly, daily
    if weekly_header is not None:
        return [], [p for p in icons if p[1] < weekly_header[1]]
    return ([], icons) if scrolled else (icons, [])


def _buy(bot, icon, name: str) -> bool:
    """Bấm NÚT GIÁ dưới sách (bấm sách không hiện popup mua) rồi chờ popup mua 1 giây, chưa hiện thì chờ thêm tối đa POPUP_CHECKS lần
    (1 giây / lần). Có popup: "+" PLUS_TAPS lần -> bấm mua. Chờ hết mà vẫn không có popup thì coi như xong (VD đã mua hết lượt, nút
    không còn bấm được). True = đã xong (lưu DB); False chỉ khi bấm mua mà popup vẫn còn mở."""
    bot.tap(icon[0], icon[1] + PRICE_DY)
    plus = None
    for _ in range(1 + POPUP_CHECKS):
        bot.sleep(1)
        plus = bot.find(PLUS)
        if plus is not None:
            break
    if plus is None:
        bot.record(f"{LABEL}: {name} buy popup not shown after {1 + POPUP_CHECKS}s, marked done")
        return True
    for _ in range(PLUS_TAPS):
        bot.tap(*plus, delay=PLUS_WAIT)
    bot.tap(bot.window_size()[0] // 2, plus[1] + BUY_DY)
    # Bấm mua chỉ mở hộp xác nhận: phải bấm Confirm mới mua thật (chỉ khi đó mới lưu DB).
    confirm = None
    for _ in range(CONFIRM_CHECKS):
        bot.sleep(1)
        confirm = bot.find(CONFIRM_BUTTON)
        if confirm is not None:
            break
    if confirm is None:
        if bot.find(PLUS) is not None:
            bot.record(f"{LABEL}: {name} no confirm dialog and buy popup still open, back, not bought")
            bot.back(delay=1)
            return False
        bot.record(f"{LABEL}: {name} no confirm dialog but popup closed, assume bought")
        return True
    bot.tap(*confirm, delay=BUY_WAIT)
    if bot.find(PLUS) is not None or bot.find(CONFIRM_BUTTON) is not None:
        bot.record(f"{LABEL}: {name} still showing buy dialog after Confirm, back, not saved")
        bot.back(delay=1)
        return False
    bot.record(f"{LABEL}: bought {name} VIP (confirmed)")
    return True


def _handle(bot, screen, icon, name: str, key: str) -> bool:
    """Một sách VIP đã thấy: xám -> đánh dấu xong không mua; xanh -> mua rồi đánh dấu. True nếu đã đánh dấu."""
    if not _price_green(bot, screen, icon):
        bot.record(f"{LABEL}: {name} VIP button is gray, marked done")
        bot.mark_daily_done(key)
        return True
    if _buy(bot, icon, name):
        bot.mark_daily_done(key)
        return True
    return False


def buy_vip(bot, month: bool, day: bool) -> None:
    """Vào Alliance Shop, mua VIP Monthly (`month`) rồi Daily (`day`) còn thiếu."""
    if not _open_shop(bot):
        return
    scrolled = settle = 0
    at_bottom = False
    while (month or day) and scrolled <= SCROLLS:
        bot.check()
        screen = bot.screenshot()
        monthly, daily = _vip_icons(bot, screen, scrolled > 0 or at_bottom)
        if month and monthly:
            month = not _handle(bot, screen, monthly[0], "Monthly", MONTH_KEY)
            continue   # popup đã đóng, màn có thể đổi: chụp lại
        if day and daily:
            day = not _handle(bot, screen, daily[0], "Daily", DAY_KEY)
            continue
        if month and scrolled == 0 and settle < SETTLE_TRIES:
            settle += 1   # đầu trang mà chưa thấy sách Monthly: shop có thể còn trôi, chụp lại trước khi cuộn xuống
            bot.sleep(1)
            continue
        if day and not month:
            if not at_bottom:
                # Sách Daily luôn ở cuối trang: kéo thật nhanh xuống cuối (không chờ giữa các lần vuốt), chờ shop hết trôi rồi tìm.
                for _ in range(BOTTOM_SWIPES):
                    bot.swipe_percent(*BOTTOM_SWIPE, duration=BOTTOM_SWIPE_DURATION, delay=0)
                bot.sleep(BOTTOM_SETTLE)
                at_bottom = True
                continue
            if bot.find(WEEKLY_HEADER, screen=screen) is not None:
                # Đã tới tiêu đề Weekly Sale mà không có sách VIP phía trên: coi như đã xong hôm nay.
                bot.record(f"{LABEL}: reached Weekly Sale without a Daily VIP item, marked done")
                bot.mark_daily_done(DAY_KEY)
                day = False
                continue
        if at_bottom:
            # Đã ở cuối trang nhưng chưa thấy tiêu đề Weekly Sale (shop còn trôi / ảnh chưa tải): chụp lại vài lần, không bao giờ cuộn lên.
            settle += 1
            if settle > SETTLE_TRIES * 2:
                break
            bot.sleep(1)
            continue
        bot.swipe_percent(*SWIPE, duration=SWIPE_DURATION, delay=1)   # chưa thấy sách Monthly: cuộn xuống từng bước nhỏ
        scrolled += 1
    if month or day:
        bot.record(f"{LABEL}: VIP not found / not bought (monthly left {month}, daily left {day})")
    for _ in range(2):   # Alliance Shop -> Liên minh -> thành
        bot.back(delay=1)


# ---- Luật của việc (bảng bot/worker/priority.py: "run": JOB) -------------------------------------------------------
def _enabled(settings: dict) -> bool:
    """Ô tích "Alliance VIP" ở tab Daily Activities; thiếu = tích (mặc định)."""
    return settings.get(LABEL, True) is not False


def _needs(ctx) -> tuple[bool, bool]:
    return not ctx.is_daily_done(MONTH_KEY), not ctx.is_daily_done(DAY_KEY)


@save_errors("daily_alliance_vip")   # lỗi thì lưu `daily_alliance_vip_error` vào DB
def _run(ctx, settings: dict):
    month, day = _needs(ctx)
    if month or day:
        ctx.log(f"Daily Activities: {LABEL} (monthly {month}, daily {day})")
        buy_vip(ctx, month, day)


JOB = {"run": _run, "enabled": _enabled, "done": lambda ctx, settings: not any(_needs(ctx))}
