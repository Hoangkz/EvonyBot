"""
run.py — Daily Activities "City VIP": nhận VIP ở thành.

Luật chạy (JOB, bảng bot/worker/priority.py), KHÔNG có ô tích (luôn bật khi chạy Daily Activities):
- chỉ làm khi giờ MÁY TÍNH nằm trong [WINDOW_START, WINDOW_END) giờ (0h đến 1h), ngoài khung giờ nhiệm vụ coi như xong / không cần làm;
- chỉ làm khi máy đã có route công trình trong DB (`ctx.city_map`, do worker quét khi rảnh); chưa có thì không làm;
- nhận xong lưu DONE_KEY (xong hôm nay, tới lần reset server).
Nhận VIP = Server Gift: kéo tường vào giữa màn, bấm hộp quà trên đầu tường, màn Server Gift bấm Claim All (xem claim_vip).
"""
from datetime import datetime

from ....city.city_map import ensure_city, goto
from ...event.city_building import WALLS
from ...event.kings_path.patrol.constants import MENU_PATROL
from ...result import save_errors
from .constants import (
    CLAIM_ALL,
    CLAIM_ALL_FALLBACK,
    CLAIM_ALL_WAIT,
    CLAIM_WAIT,
    DONE_KEY,
    GIFT_AREA,
    GIFT_BOXES,
    GIFT_FIND_CHECKS,
    GIFT_OPEN_CHECKS,
    GIFT_THRESHOLD,
    GIFT_TRIES,
    KEY,
    LABEL,
    MENU_WAIT,
    SERVER_GIFT_TITLE,
    WINDOW_END,
    WINDOW_START,
)


def in_window(now: datetime | None = None) -> bool:
    """Giờ máy tính nằm trong khung giờ được phép nhận VIP."""
    return WINDOW_START <= (now or datetime.now()).hour < WINDOW_END


def _find_gift(bot, around=None, screen=None):
    """Tâm hộp quà trên đầu tường (thử mọi ảnh trong GIFT_BOXES, hộp quà có hiệu ứng nên điểm khớp dao động), hoặc None. `around` =
    vị trí Tường thành trên màn: chỉ tìm trong vùng phía trên tường (GIFT_AREA) để không khớp nhầm icon khác."""
    screen = bot.screenshot() if screen is None else screen
    region = None
    if around is not None:
        height, width = screen.shape[:2]
        (dx0, dy0), (dx1, dy1) = GIFT_AREA
        region = (max(0, (around[0] + dx0) / width * 100), max(0, (around[1] + dy0) / height * 100),
                  min(100, (around[0] + dx1) / width * 100), min(100, (around[1] + dy1) / height * 100))
    return next((pos for path in GIFT_BOXES
                 if (pos := bot.find(path, screen=screen, threshold=GIFT_THRESHOLD, region=region)) is not None), None)


def claim_vip(bot) -> bool:
    """Nhận quà Server Gift ở hộp quà trên đầu Tường thành. Cần route trong DB (`bot.city_map`).
    1. Kéo tường vào giữa màn (city_map.goto). Thấy hộp quà thì bỏ qua bước 2.
    2. Chưa thấy hộp quà: bấm tường 1 cái, chờ menu (Patrol) hiện, bấm lại đúng chỗ đó cho menu đóng, rồi tìm hộp quà.
    3. Bấm hộp quà, chờ 1 giây, chưa ra màn Server Gift thì chờ thêm tối đa GIFT_OPEN_CHECKS lần (1 giây / lần); vẫn chưa ra thì bấm lại
       hộp quà, tối đa GIFT_TRIES lần.
    4. Màn Server Gift: bấm Claim All. True nếu đã bấm (nhiệm vụ xong)."""
    if not bot.city_map:
        return False
    ensure_city(bot, LABEL)
    walls = goto(bot, LABEL, WALLS, bot.city_map)
    if walls is None:
        bot.record(f"{LABEL}: Walls not reached")
        return False
    box = _find_gift(bot, walls)
    if box is None:
        bot.log(f"{LABEL}: no gift box yet, tap the Walls to centre it")
        bot.tap(*walls)
        bot.wait_for(MENU_PATROL, timeout=MENU_WAIT)
        bot.tap(*walls, delay=1)   # bấm lại đúng chỗ: menu đóng, thấy rõ hộp quà
        for _ in range(GIFT_FIND_CHECKS):
            box = _find_gift(bot, walls)
            if box is not None:
                break
            bot.sleep(1)
    if box is None:
        bot.record(f"{LABEL}: gift box not found above the Walls")
        return False
    for attempt in range(GIFT_TRIES):
        bot.tap(*box)
        for _ in range(1 + GIFT_OPEN_CHECKS):
            bot.sleep(1)
            if bot.find(SERVER_GIFT_TITLE) is not None:
                return _claim_all(bot)
        bot.log(f"{LABEL}: Server Gift not shown after {1 + GIFT_OPEN_CHECKS}s (try {attempt + 1}/{GIFT_TRIES})")
        box = _find_gift(bot, walls) or box
    bot.record(f"{LABEL}: Server Gift screen not opened after {GIFT_TRIES} tries")
    return False


def _claim_all(bot) -> bool:
    """Màn Server Gift: bấm Claim All và LƯU DB ngay (không chờ popup / Back mới lưu), rồi chờ và Back về thành. True (xong)."""
    button = bot.wait_for(CLAIM_ALL, timeout=CLAIM_ALL_WAIT) or CLAIM_ALL_FALLBACK
    bot.tap(*button)
    bot.mark_daily_done(DONE_KEY)
    bot.record(f"{LABEL}: Claim All tapped, saved")
    bot.sleep(CLAIM_WAIT)
    bot.back(delay=1)
    return True


def _enabled(settings: dict) -> bool:
    """Không có ô tích: luôn bật, cứ tới khung giờ (và có route trong DB) là đi nhận."""
    return True


def _done(ctx, settings: dict) -> bool:
    """Không cần làm lúc này: đã nhận hôm nay, hoặc ngoài khung giờ, hoặc máy chưa có route công trình trong DB."""
    return ctx.is_daily_done(DONE_KEY) or not in_window() or not ctx.city_map


@save_errors(KEY)   # lỗi thì lưu `daily_city_vip_error` vào DB
def _run(ctx, settings: dict):
    if _done(ctx, settings):
        return
    ctx.log(f"Daily Activities: {LABEL}")
    claim_vip(ctx)   # tự lưu DONE_KEY ngay khi bấm Claim All


JOB = {"run": _run, "enabled": _enabled, "done": _done}
