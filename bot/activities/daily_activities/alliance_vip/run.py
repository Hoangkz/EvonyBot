"""Daily Activities / Alliance VIP Shop.

Tribute và 100 VIP Points được tìm trước, sau đó tới tài nguyên, Chips và
Truce được bật trong UI. Mỗi popup luôn chọn MAX bằng đầu thanh bên trái dấu
``+``. Một vật phẩm chỉ được ghi DONE sau khi chụp lại và nút giá đã xám;
khi mọi checkbox đã DONE sẽ ghi thêm ``ALL_DONE_KEY`` theo ngày.
"""
import cv2
import numpy as np

from ....common import click_images, delay, exit_images, find_first, go_home
from ....context.templates import TEMPLATE_DIR
from ...result import save_errors
from .catalog import ITEMS, SETTINGS_KEY, normalized
from .constants import (
    ALL_DONE_KEY,
    ALLIANCE_NAV,
    BUY_DY,
    BUY_BUTTON_BOX,
    BUY_MIN_SATURATION,
    BUY_WAIT,
    BOTTOM_CONFIRMATIONS,
    BOTTOM_SIGNATURE_DISTANCE,
    CONFIRM_BUTTON,
    CONFIRM_CHECKS,
    DAILY_HEADER,
    DAY_KEY,
    LABEL,
    ITEM_THRESHOLD,
    LOCKED_ITEM_THRESHOLD,
    MONTH_KEY,
    MAX_CROP_HALF_HEIGHT,
    MAX_CROP_LEFT,
    MAX_SELECTED,
    MAX_SELECT_TRIES,
    MAX_SLIDER,
    NAV_MAX_STEPS,
    PLUS,
    POPUP_TEMPLATE_THRESHOLD,
    POPUP_CHECKS,
    PRICE_BOX,
    PRICE_DY,
    PRICE_MIN_SATURATION,
    SCAN_SETTLE,
    SCROLLS,
    SHOP_ROW,
    SHOP_TITLE,
    SWIPE,
    SWIPE_DURATION,
    TOP_SETTLE,
    TOP_SWIPE,
    TOP_SWIPE_DURATION,
    TOP_SWIPES,
    TRIBUTE_DAY_KEY,
    TRIBUTE_MONTH_KEY,
    WEEKLY_HEADER,
)

_ON_SHOP, _TAP, _BACK, _SCROLL, _OUT = "on_shop", "tap", "back", "scroll", "out_alliance"
_ALLIANCE_BUTTON, _ALLIANCE_SCROLL, _OUT_ALLIANCE = ALLIANCE_NAV


def _open_shop(bot) -> bool:
    """Màn chính -> Liên minh -> Alliance Shop. True nếu tới màn Alliance Shop."""
    targets = [
        # Popup mua vẫn để lộ title phía sau; phải đóng nó trước khi quét shop.
        (PLUS, _BACK),
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
    if box.size == 0:
        return False
    saturation = float(cv2.cvtColor(box, cv2.COLOR_BGR2HSV)[..., 1].mean())
    bot.record(f"{LABEL}: độ bão hòa nút giá {saturation:.0f}")
    return saturation >= PRICE_MIN_SATURATION


def _shop_to_top(bot) -> None:
    """Đưa danh sách về đầu để Tribute/VIP luôn được tìm trước."""
    for _ in range(TOP_SWIPES):
        bot.swipe_percent(*TOP_SWIPE, duration=TOP_SWIPE_DURATION, delay=0)
    bot.sleep(TOP_SETTLE)


def _shop_scroll_signature(screen) -> np.ndarray:
    """Stable edge dHash for the scrolling shop body.

    Price glows and item artwork animate even at the real bottom, so raw pixel
    difference can report movement forever.  Blurred structural edges in the
    left/centre list body preserve row movement while suppressing that glow.
    """
    height, width = screen.shape[:2]
    patch = screen[int(height * .10):int(height * .95),
                   int(width * .03):int(width * .76)]
    gray = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(cv2.GaussianBlur(gray, (5, 5), 0), 45, 120)
    tiny = cv2.resize(edges, (33, 24), interpolation=cv2.INTER_AREA)
    return np.packbits(tiny[:, 1:] > tiny[:, :-1])


def _shop_scroll_distance(before, after) -> int:
    old = _shop_scroll_signature(before)
    new = _shop_scroll_signature(after)
    return int(np.unpackbits(np.bitwise_xor(old, new)).sum())


def _buy_button_active(bot, screen, center) -> bool:
    """Only press the popup Buy button when its colour is still saturated."""
    w, h = BUY_BUTTON_BOX
    box = bot.crop(screen, center[0] - w // 2, center[1] - h // 2, w, h)
    if box.size == 0:
        return False
    saturation = float(cv2.cvtColor(box, cv2.COLOR_BGR2HSV)[..., 1].mean())
    bot.record(f"{LABEL}: Buy button saturation {saturation:.0f}")
    return saturation >= BUY_MIN_SATURATION


def _find_item(bot, screen, template: str,
               y_range: tuple[int, int] | None = None):
    """Tìm icon thường trước, rồi tìm theo viền khi giữa icon bị phủ ổ khóa.

    Mask chỉ bỏ phần trung tâm; khung màu và các góc đặc trưng vẫn phải đạt
    ngưỡng cao nên không dùng một ảnh ổ khóa chung để đoán vật phẩm.
    """
    tpl = bot._template(template)
    h, w = tpl.shape[:2]
    default_top, default_bottom = int(screen.shape[0] * .08), int(screen.shape[0] * .94)
    top, bottom = y_range or (default_top, default_bottom)
    top, bottom = max(default_top, top), min(default_bottom, bottom)
    area = screen[top:bottom]
    if h > area.shape[0] or w > area.shape[1]:
        return None, 0.0, False
    normal = cv2.matchTemplate(area, tpl, cv2.TM_CCOEFF_NORMED)
    _, score, _, (normal_x, normal_y) = cv2.minMaxLoc(normal)
    if score >= ITEM_THRESHOLD:
        return (normal_x + w // 2, normal_y + top + h // 2), float(score), False
    mask = np.full((h, w), 255, dtype=np.uint8)
    mask[int(h * .22):int(h * .78), int(w * .22):int(w * .78)] = 0
    result = cv2.matchTemplate(area, tpl, cv2.TM_CCORR_NORMED, mask=mask)
    result = np.nan_to_num(result, nan=-1.0, posinf=-1.0, neginf=-1.0)
    _, masked_score, _, (x, y) = cv2.minMaxLoc(result)
    if masked_score < LOCKED_ITEM_THRESHOLD:
        return None, max(float(score), float(masked_score)), True
    return (x + w // 2, y + top + h // 2), float(masked_score), True


def _select_max(bot, plus: tuple[int, int]) -> bool:
    """Bấm đầu thanh tại x≈plus.x-35 và chỉ thành công khi thấy thanh MAX."""
    for attempt in range(1, MAX_SELECT_TRIES + 1):
        screen = bot.screenshot()
        if bot.find(MAX_SELECTED, threshold=POPUP_TEMPLATE_THRESHOLD,
                    screen=screen) is not None:
            bot.record(f"{LABEL}: số lượng đã ở MAX")
            return True
        left = max(0, plus[0] - MAX_CROP_LEFT)
        top = max(0, plus[1] - MAX_CROP_HALF_HEIGHT)
        crop = bot.crop(screen, left, top, MAX_CROP_LEFT,
                        MAX_CROP_HALF_HEIGHT * 2)
        slider = bot.find(MAX_SLIDER, threshold=POPUP_TEMPLATE_THRESHOLD,
                          screen=crop)
        if slider is None:
            bot.record(f"{LABEL}: chưa thấy đầu thanh MAX trong crop (lần {attempt}/{MAX_SELECT_TRIES})")
            bot.sleep(1)
            continue
        bot.tap(left + slider[0], top + slider[1], delay=1)
        if bot.find(MAX_SELECTED, threshold=POPUP_TEMPLATE_THRESHOLD) is not None:
            bot.record(f"{LABEL}: đã chọn MAX")
            return True
        bot.record(f"{LABEL}: chưa xác nhận được MAX; bấm lại ({attempt}/{MAX_SELECT_TRIES})")
    return False


def _buy(bot, icon, name: str) -> bool:
    """Mở popup, chọn MAX bằng thanh trượt, mua và xác nhận.

    True chỉ nghĩa là giao dịch đã đóng; DONE vẫn phải chụp lại và thấy nút
    giá xám. Không thấy popup tuyệt đối không tự đánh dấu DONE.
    """
    bot.tap(icon[0], icon[1] + PRICE_DY)
    plus = None
    for _ in range(1 + POPUP_CHECKS):
        bot.sleep(1)
        plus = bot.find(PLUS, threshold=POPUP_TEMPLATE_THRESHOLD)
        if plus is not None:
            break
    if plus is None:
        bot.record(f"{LABEL}: {name} không hiện popup mua; giữ PENDING")
        return False
    if not _select_max(bot, plus):
        bot.record(f"{LABEL}: {name} chưa chọn được MAX; giữ PENDING")
        bot.back(delay=1)
        return False
    buy = (bot.window_size()[0] // 2, plus[1] + BUY_DY)
    if not _buy_button_active(bot, bot.screenshot(), buy):
        bot.record(f"{LABEL}: {name} Buy button is gray; do not tap")
        bot.back(delay=1)
        return True
    bot.tap(*buy)
    # Bấm mua chỉ mở hộp xác nhận: phải bấm Confirm mới mua thật (chỉ khi đó mới lưu DB).
    confirm = None
    for _ in range(CONFIRM_CHECKS):
        bot.sleep(1)
        confirm = bot.find(CONFIRM_BUTTON)
        if confirm is not None:
            break
    if confirm is None:
        if bot.find(PLUS, threshold=POPUP_TEMPLATE_THRESHOLD) is not None:
            bot.record(f"{LABEL}: {name} no confirm dialog and buy popup still open, back, not bought")
            bot.back(delay=1)
            return False
        bot.record(f"{LABEL}: {name} no confirm dialog but popup closed, assume bought")
        return True
    bot.tap(*confirm, delay=BUY_WAIT)
    if (bot.find(PLUS, threshold=POPUP_TEMPLATE_THRESHOLD) is not None or
            bot.find(CONFIRM_BUTTON) is not None):
        bot.record(f"{LABEL}: {name} still showing buy dialog after Confirm, back, not saved")
        bot.back(delay=1)
        return False
    bot.record(f"{LABEL}: đã mua {name} và xác nhận")
    return True


# ---- Luật của việc (bảng bot/worker/priority.py: "run": JOB) -------------------------------------------------------
def _enabled(settings: dict) -> bool:
    """Ô tích "Alliance VIP" ở tab Daily Activities; thiếu = tích (mặc định)."""
    return settings.get(LABEL, True) is not False


def _item_done_key(key: str) -> str:
    return f"Alliance VIP: {key}"


def _selection(settings: dict) -> dict[str, int]:
    return normalized(settings.get(SETTINGS_KEY), legacy_defaults=True)


def _priority_keys(item_key: str) -> tuple[str, str]:
    if item_key == "tribute":
        return TRIBUTE_MONTH_KEY, TRIBUTE_DAY_KEY
    if item_key == "vip_points":
        return MONTH_KEY, DAY_KEY
    raise KeyError(item_key)


def _sync_priority_item_done(ctx, item_key: str) -> None:
    month_key, day_key = _priority_keys(item_key)
    if ctx.is_daily_done(month_key) and ctx.is_daily_done(day_key):
        key = _item_done_key(item_key)
        if not ctx.is_daily_done(key):
            ctx.mark_daily_done(key)
            ctx.record(f"{LABEL}: {item_key} đã DONE ở cả Monthly Card và Daily Sale")


def _catalog_done(ctx, settings: dict) -> bool:
    """Khóa tổng duy nhất để scheduler bỏ qua toàn bộ việc trong ngày."""
    return ctx.is_daily_done(ALL_DONE_KEY)


def _all_selected_items_done(ctx, settings: dict) -> bool:
    """Mọi checkbox đã có khóa riêng (VIP cần đủ Monthly + Daily)."""
    selected = _selection(settings)
    for item in ITEMS:
        if selected[item.key] <= 0:
            continue
        if item.key in {"tribute", "vip_points"}:
            month_key, day_key = _priority_keys(item.key)
            if not (ctx.is_daily_done(month_key) and ctx.is_daily_done(day_key)):
                return False
        elif not ctx.is_daily_done(_item_done_key(item.key)):
            return False
    return True


def _visible_section_ranges(ctx, screen, daily_reached: bool,
                            weekly_reached: bool):
    top, bottom = int(screen.shape[0] * .08), int(screen.shape[0] * .94)
    daily = ctx.find(DAILY_HEADER, screen=screen)
    weekly = ctx.find(WEEKLY_HEADER, screen=screen)
    ranges = {"monthly": None, "daily": None}
    if daily is not None:
        ranges["monthly"] = (top, daily[1])
        ranges["daily"] = (daily[1], weekly[1] if weekly is not None else bottom)
    elif weekly is not None:
        ranges["daily"] = (top, weekly[1])
    elif daily_reached and not weekly_reached:
        ranges["daily"] = (top, bottom)
    else:
        ranges["monthly"] = (top, bottom)
    return (ranges, daily is not None or daily_reached,
            weekly is not None or weekly_reached)


def _mark_visible_done(ctx, item_key: str, done_key: str, label: str) -> None:
    ctx.mark_daily_done(done_key)
    ctx.record(f"{LABEL}: {label} nút giá xám; ghi DONE vào DB")
    if item_key in {"tribute", "vip_points"}:
        _sync_priority_item_done(ctx, item_key)


def _run_shop_session(ctx, settings: dict,
                      priority_filter: set[str] | None = None) -> None:
    """Mở shop đúng một lần, xử lý mọi món nhìn thấy rồi mới cuộn/thoát."""
    selected = _selection(settings)
    enabled = [item for item in ITEMS if selected[item.key] > 0]
    if not enabled:
        return
    available = [item for item in enabled if (TEMPLATE_DIR / item.template).is_file()]
    missing = [item for item in enabled if item not in available]
    if missing:
        ctx.record(f"{LABEL}: thiếu ảnh chuẩn Alliance Shop cho: " +
                   ", ".join(item.label for item in missing))
    if not available or not _open_shop(ctx):
        return
    _shop_to_top(ctx)

    item_by_key = {item.key: item for item in available}
    attempted: set[str] = set()  # mỗi vị trí Monthly/Daily chỉ mua một lần/lượt
    best_scores: dict[str, float] = {}
    daily_reached = False
    weekly_reached = False
    stagnant_swipes = 0
    for step in range(SCROLLS + 1):
        # Xử lý hết mọi vật phẩm trong cùng khung; popup đóng xong chụp lại,
        # tuyệt đối không Back ra Alliance Shop rồi vào lại.
        for _ in range(len(ITEMS) + 4):
            ctx.check()
            screen = ctx.screenshot()
            ranges, daily_reached, weekly_reached = _visible_section_ranges(
                ctx, screen, daily_reached, weekly_reached)
            candidates: list[tuple[object, str, str, tuple[int, int] | None]] = []

            # Luôn ưu tiên Tribute rồi VIP, mỗi loại ở cả Monthly và Daily.
            for section, index in (("monthly", 0), ("daily", 1)):
                for key in ("tribute", "vip_points"):
                    item = item_by_key.get(key)
                    if item is None:
                        continue
                    done_key = _priority_keys(key)[index]
                    if priority_filter is not None and done_key not in priority_filter:
                        continue
                    if not ctx.is_daily_done(done_key) and ranges[section] is not None:
                        candidates.append((item, done_key,
                                           f"{item.label} / {section.title()}",
                                           ranges[section]))

            # Sau hai món ưu tiên, thấy món nào khác trong khung thì làm ngay.
            if priority_filter is None:
                for item in available:
                    if item.key in {"tribute", "vip_points"}:
                        continue
                    done_key = _item_done_key(item.key)
                    if not ctx.is_daily_done(done_key):
                        candidates.append((item, done_key, item.label, None))

            handled = False
            for item, done_key, display, y_range in candidates:
                icon, score, locked_match = _find_item(
                    ctx, screen, item.template, y_range=y_range)
                best_scores[done_key] = max(best_scores.get(done_key, 0.0), score)
                if icon is None:
                    continue
                ctx.record(f"{LABEL}: thấy {display}, điểm {score:.3f}" +
                           (" (so viền)" if locked_match else ""))
                if not _price_green(ctx, screen, icon):
                    _mark_visible_done(ctx, item.key, done_key, display)
                    handled = True
                    break
                if done_key in attempted:
                    continue
                attempted.add(done_key)
                if _buy(ctx, icon, display):
                    ctx.sleep(1)
                    after = ctx.screenshot()
                    if not _price_green(ctx, after, icon):
                        _mark_visible_done(ctx, item.key, done_key, display)
                    else:
                        ctx.record(f"{LABEL}: {display} vẫn còn màu; giữ PENDING và làm món kế tiếp")
                handled = True
                break
            if not handled:
                break

        if priority_filter is None and _all_selected_items_done(ctx, settings):
            ctx.record(f"{LABEL}: mọi vật phẩm đã tích đã DONE ngay trong phiên shop hiện tại")
            break
        if priority_filter is not None and all(ctx.is_daily_done(key) for key in priority_filter):
            break
        if step >= SCROLLS:
            ctx.record(f"{LABEL}: đã đủ {SCROLLS} lượt lướt nhưng chưa có "
                       "3 xác nhận đáy liên tiếp; dừng theo trần an toàn")
            break
        ctx.record(f"{LABEL}: đã xử lý hết khung {step + 1}/{SCROLLS + 1}; vuốt chậm 1s rồi dừng 1s để quét")
        before_scroll = screen
        ctx.swipe_percent(*SWIPE, duration=SWIPE_DURATION, delay=SCAN_SETTLE)
        after_scroll = ctx.screenshot()
        distance = _shop_scroll_distance(before_scroll, after_scroll)
        stable = distance <= BOTTOM_SIGNATURE_DISTANCE
        if stable and weekly_reached:
            stagnant_swipes += 1
        else:
            stagnant_swipes = 0
        ctx.record(f"{LABEL}: kiểm tra đáy bằng dải cấu trúc: khoảng cách "
                   f"{distance}, Weekly={'đã thấy' if weekly_reached else 'chưa thấy'}, "
                   f"ổn định={stagnant_swipes}/{BOTTOM_CONFIRMATIONS}")
        if stable and not weekly_reached:
            ctx.record(f"{LABEL}: khung chưa dịch chuyển nhưng chưa thấy mốc "
                       "Weekly Sale; tiếp tục lướt, chưa được kết luận đáy")
        if stagnant_swipes >= BOTTOM_CONFIRMATIONS:
            ctx.record(f"{LABEL}: đã thấy Weekly Sale và vùng danh sách không "
                       f"dịch chuyển {BOTTOM_CONFIRMATIONS} lần; xác nhận đã tới cuối")
            break

    for key in ("tribute", "vip_points"):
        if key in item_by_key:
            _sync_priority_item_done(ctx, key)
    for _ in range(2):
        ctx.back(delay=1)
    pending_labels = []
    for item in available:
        if item.key in {"tribute", "vip_points"}:
            for section, done_key in zip(("Monthly", "Daily"), _priority_keys(item.key)):
                if (priority_filter is None or done_key in priority_filter) and not ctx.is_daily_done(done_key):
                    pending_labels.append(f"{item.label}/{section} ({best_scores.get(done_key, 0):.3f})")
        elif priority_filter is None and not ctx.is_daily_done(_item_done_key(item.key)):
            done_key = _item_done_key(item.key)
            pending_labels.append(f"{item.label} ({best_scores.get(done_key, 0):.3f})")
    if pending_labels:
        ctx.record(f"{LABEL}: kết thúc một lượt shop, còn PENDING: " + ", ".join(pending_labels))


def buy_vip(bot, month: bool, day: bool) -> None:
    """API cũ: kiểm tra VIP Monthly/Daily trong cùng một lần vào shop."""
    settings = {SETTINGS_KEY: {item.key: item.key == "vip_points" for item in ITEMS}}
    wanted = ({MONTH_KEY} if month else set()) | ({DAY_KEY} if day else set())
    if wanted:
        _run_shop_session(bot, settings, priority_filter=wanted)


@save_errors("daily_alliance_vip")   # lỗi thì lưu `daily_alliance_vip_error` vào DB
def _run(ctx, settings: dict):
    ctx.log(f"Daily Activities: {LABEL} — một lần vào shop, xử lý liên tục từ trên xuống")
    _run_shop_session(ctx, settings)
    if _all_selected_items_done(ctx, settings):
        ctx.mark_daily_done(ALL_DONE_KEY)
        ctx.record(f"{LABEL}: tất cả vật phẩm đã tích đều DONE; ghi hoàn tất hôm nay vào DB")


JOB = {"run": _run, "enabled": _enabled, "done": _catalog_done}
