"""
run.py — Daily Activities "Offering": phần làm nhiệm vụ sau Go (after_go) (Đền thờ (Shrine) -> Offer).
Mở dòng Activity + bấm Go: ../common.py (open_task_or_finish, daily_job).
"""
from ....ocr import read_offer_cost
from ....ocr.read_offer_cost import CROP as COST_CROP
from ...event.city_building import SHRINE
from ...event.kings_path.building import open_building
from ...result import done as report_done
from ..common import Task
from .constants import (
    BACKS_AFTER_OFFER,
    FOLDER,
    KEY,
    LABEL,
    MENU_OFFER,
    OFFER_GEMS_DEFAULT,
    OFFER_GEMS_KEY,
    OFFER_GEMS_WAIT,
    OFFER_PRICE_TIERS,
    OFFER_SCREEN,
    POPUP_CLOSE,
    POPUP_MINUS,
    POPUP_MINUS_REGION,
    PLUS_WAIT,
    POPUP_OFFER,
    POPUP_PLUS,
    POPUP_PLUS_REGION,
    POPUP_TITLE,
    POPUP_WAIT,
)


def offer_price(n: int) -> int:
    """Giá kim cương của lượt Offer Gems thứ `n` trong ngày (1, 2, ...)."""
    return next(price for start, price in reversed(OFFER_PRICE_TIERS) if n >= start)


def offer_total(done: int, count: int) -> int:
    """Tổng kim cương để offer thêm `count` lượt khi hôm nay đã offer `done` lượt."""
    return sum(offer_price(n) for n in range(done + 1, done + count + 1))


def offers_done(costs: list[int], limit: int = 100) -> list[int]:
    """Số lượt đã offer hôm nay khớp với Cost đọc được: costs[i] = Cost khi ô số lượng là i + 1.
    Trả mọi giá trị khớp (nhiều hơn 1 = chưa phân biệt được, đọc thêm một mức số lượng)."""
    return [done for done in range(limit)
            if all(offer_total(done, i + 1) == cost for i, cost in enumerate(costs))]


def mark_done(bot, times: int):
    """Báo xong hôm nay với số lượng `times` (result.reached = times; worker so với số đang chọn ở tab UI)."""
    report_done(bot, times, label=LABEL, key=KEY)


def offer_times(bot) -> int:
    """Số lần Offer Gems người dùng chọn ở tab Daily Activities (ô "Offer Gems")."""
    daily = (getattr(bot, "settings", None) or {}).get("Daily Activities", {})
    try:
        return max(0, int(daily.get(OFFER_GEMS_KEY, OFFER_GEMS_DEFAULT)))
    except (TypeError, ValueError):
        return OFFER_GEMS_DEFAULT


def after_go(bot) -> bool:
    """Phiên bản mới, sau khi open_task bấm Go (hai phiên bản giống nhau từ đây): Đền thờ ở giữa ->
    open_building (nhận ra / tự học ảnh công trình, menu "Offer") -> màn Offer -> bấm "Offer Gems" ->
    popup (_offer_in_popup: chỉ mua phần còn thiếu so với số lần đã offer hôm nay). True nếu xong (0 lần:
    không bấm gì). Bấm Offer xong -> Back BACKS_AFTER_OFFER lần về thành."""
    times = offer_times(bot)
    if not open_building(bot, LABEL, SHRINE, MENU_OFFER, OFFER_SCREEN):
        return False
    if times <= 0:
        bot.log(f"{LABEL}: Offer Gems 0 times, skipped")
        report_done(bot, label=LABEL, key=KEY)   # không báo reached: reached 0 là "dòng Offer không còn Go"
        return True
    button = bot.find(OFFER_SCREEN)
    if button is None:
        bot.record(f"{LABEL}: Offer Gems button not found")
        return False
    bot.tap(*button, delay=1)
    if bot.wait_for(POPUP_TITLE, timeout=POPUP_WAIT) is None:
        bot.record(f"{LABEL}: Offer Gems popup not shown")
        return False
    return _offer_in_popup(bot, times)


def read_cost(bot, screen=None) -> int | None:
    """Số kim cương ở ô "Cost" của popup Offer Gems (bot/ocr/read_offer_cost.py), hoặc None."""
    screen = bot.screenshot() if screen is None else screen
    return read_offer_cost(bot.crop(screen, *COST_CROP))


def _offer_in_popup(bot, times: int) -> bool:
    """Popup Offer Gems đang mở ở số lượng 1. Không mua lại lượt đã offer hôm nay:
    1. OCR Cost (số lượng 1) -> các khả năng số lượt đã làm (offers_done); lấy nhỏ nhất `k`.
    2. k >= times: đã đủ -> đóng popup, không mua.
    3. Bấm "+" lên mức tối đa có thể (times - k), OCR lại Cost -> biết chính xác số đã làm.
    4. Vượt quá (thực tế đã làm nhiều hơn k) -> bấm "-" lùi số bước dư, rồi Offer.
    Không đọc được Cost: không mua (tránh tốn kim cương), ghi lịch sử."""
    cost = read_cost(bot)
    candidates = offers_done([cost]) if cost is not None else []
    if not candidates:
        bot.record(f"{LABEL}: cannot read Offer Gems cost ({cost}), not offering")
        _close_popup(bot)
        return False
    done = min(candidates)
    if done >= times:
        bot.record(f"{LABEL}: already offered {done} time(s) today (target {times})")
        _close_popup(bot)
        mark_done(bot, times)
        return True
    count = times - done
    if count > 1:
        plus = bot.find(POPUP_PLUS, region=POPUP_PLUS_REGION)
        if plus is None:
            bot.record(f"{LABEL}: Offer Gems '+' not found")
            _close_popup(bot)
            return False
        for _ in range(count - 1):
            bot.tap(*plus, delay=PLUS_WAIT)
        total = read_cost(bot)
        exact = [k for k in candidates if offer_total(k, count) == total]
        if not exact:
            bot.record(f"{LABEL}: Offer Gems cost {total} for {count} does not match, not offering")
            _close_popup(bot)
            return False
        extra = exact[0] - done   # thực tế đã làm nhiều hơn -> lùi lại
        if extra > 0:
            minus = bot.find(POPUP_MINUS, region=POPUP_MINUS_REGION)
            if minus is None:
                bot.record(f"{LABEL}: Offer Gems '-' not found")
                _close_popup(bot)
                return False
            for _ in range(extra):
                bot.tap(*minus, delay=PLUS_WAIT)
            done, count = exact[0], count - extra
            if count <= 0:
                bot.record(f"{LABEL}: already offered {done} time(s) today (target {times})")
                _close_popup(bot)
                mark_done(bot, times)
                return True
    offer = bot.find(POPUP_OFFER)
    if offer is None:
        bot.record(f"{LABEL}: Offer button not found in popup")
        _close_popup(bot)
        return False
    bot.tap(*offer, delay=OFFER_GEMS_WAIT)
    bot.record(f"{LABEL}: Offer Gems x{count} ({done} done before, "
               f"{offer_total(done, count)} gems)")
    mark_done(bot, times)
    for _ in range(BACKS_AFTER_OFFER):
        bot.back(delay=1)
    return True


def _close_popup(bot):
    close = bot.find(POPUP_CLOSE)
    if close is not None:
        bot.tap(*close, delay=1)
    else:
        bot.back(delay=1)

TASK = Task(LABEL, FOLDER, key=KEY)
