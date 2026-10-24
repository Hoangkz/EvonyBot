"""Daily Activities / Alliance VIP Shop.

Tribute và 100 VIP Points được tìm trước, sau đó tới tài nguyên, Chips và
Truce được bật trong UI. Mỗi popup luôn chọn MAX bằng đầu thanh bên trái dấu
``+``. Một vật phẩm được ghi DONE khi nút giá xám hoặc vừa mua xong (Confirm);
việc xong hôm nay khi mọi món đang tích đều có khóa DONE riêng.
"""
import cv2
import numpy as np

from ....common import no_alliance
from ....common import click_images, delay, exit_images, find_first, go_home
from ....context.templates import TEMPLATE_DIR
from ...result import save_errors
from .catalog import ITEMS, SETTINGS_KEY, normalized
from .constants import (
    ALLIANCE_NAV,
    BUY_DY,
    BUY_BUTTON_BOX,
    BUY_MIN_SATURATION,
    BUY_WAIT,
    CONFIRM_BUTTON,
    DAILY_HEADER,
    DAY_KEY,
    FAST_SWIPE,
    FAST_SWIPE_DURATION,
    FAST_SWIPES,
    LABEL,
    ITEM_THRESHOLD,
    LOCKED_ITEM_THRESHOLD,
    MAX_BAR_STILL_DIFF,
    MAX_BAR_WIDTH,
    MAX_CROP_HALF_HEIGHT,
    MAX_CROP_LEFT,
    MAX_SELECTED,
    MAX_SELECT_TRIES,
    MAX_SLIDER,
    NAV_MAX_STEPS,
    PLUS,
    POPUP_TEMPLATE_THRESHOLD,
    PRICE_BOX,
    PRICE_DY,
    PRICE_MIN_SATURATION,
    SCAN_SETTLE,
    SCROLLS,
    SHOP_ROW,
    SHOP_TITLE,
    SWIPE,
    SWIPE_DURATION,
    SWIPE_UP,
    TRIBUTE_DAY_KEY,
    UNFOCUS_TAP,
    TRUCE_COLOR_SATURATION_MIN,
    TRUCE_COLOR_VALUE_MIN,
    WAIT_INTERVAL,
    WAIT_TIMEOUT,
    WEEKLY_HEADER,
)

_ON_SHOP, _TAP, _BACK, _SCROLL, _OUT, _OPEN = "on_shop", "tap", "back", "scroll", "out_alliance", "open_alliance"
_ROW = "shop_row"
_BOUGHT, _NO_POINTS, _PENDING = "bought", "no_points", "pending"   # kết quả _buy
_ALLIANCE_BUTTON, _ALLIANCE_SCROLL, _OUT_ALLIANCE = ALLIANCE_NAV
PRIORITY_KEYS = ("tribute", "vip_points")   # có tích một trong hai thì cuộn nhanh xuống Daily Sale
_TRUCE_ITEMS = tuple(item for item in ITEMS
                     if item.key.startswith("truce_agreement_"))


def _hue_histogram(image) -> np.ndarray | None:
    """Histogram màu nền, bỏ pixel xám/trắng của chim và ổ khóa."""
    if image is None or image.size == 0:
        return None
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask = ((hsv[..., 1] >= TRUCE_COLOR_SATURATION_MIN) &
            (hsv[..., 2] >= TRUCE_COLOR_VALUE_MIN)).astype(np.uint8) * 255
    if cv2.countNonZero(mask) < max(20, image.shape[0] * image.shape[1] // 20):
        return None
    histogram = cv2.calcHist([hsv], [0], mask, [36], [0, 180])
    return cv2.normalize(histogram, None, alpha=1.0,
                         norm_type=cv2.NORM_L1)


def _truce_color_matches(bot, screen, center, template: str) -> bool:
    """Luôn phân loại 8h/24h/3d theo màu gần nhất."""
    expected = next((item for item in _TRUCE_ITEMS
                     if item.template == template), None)
    if expected is None:
        return True
    tpl = bot._template(template)
    height, width = tpl.shape[:2]
    candidate = bot.crop(screen, center[0] - width // 2,
                         center[1] - height // 2, width, height)
    candidate_hist = _hue_histogram(candidate)
    distances = []
    for item in _TRUCE_ITEMS:
        reference = bot._template(item.template)
        reference_hist = _hue_histogram(reference)
        if candidate_hist is not None and reference_hist is not None:
            distance = float(cv2.compareHist(
                candidate_hist, reference_hist, cv2.HISTCMP_BHATTACHARYYA))
        else:
            # Hiếm gặp khi glow/ổ khóa che gần hết màu. Vẫn phải
            # chọn một loại thay vì PENDING: so full-colour sau resize.
            resized = cv2.resize(candidate, (reference.shape[1],
                                             reference.shape[0]))
            similarity = float(cv2.matchTemplate(
                resized, reference, cv2.TM_CCOEFF_NORMED)[0, 0])
            distance = 1.0 - similarity
        distances.append((distance, item))
    distances.sort(key=lambda pair: pair[0])
    best_distance, best_item = distances[0]
    runner_up = distances[1][0]
    margin = runner_up - best_distance
    accepted = best_item.key == expected.key
    bot.record(f"{LABEL}: dải màu Truce nhận {best_item.label}, "
               f"yêu cầu {expected.label}, khoảng cách {best_distance:.3f}, "
               f"chênh {margin:.3f} -> "
               f"{'đúng loại' if accepted else 'không phải loại này'}")
    return accepted


def _wait(bot, template: str, threshold: float | None = None):
    """Chờ màn đích sau khi chuyển màn: 1 giây kiểm tra một lần, tối đa 6 lần. Trả tâm ảnh hoặc None."""
    if threshold is None:
        return bot.wait_for(template, timeout=WAIT_TIMEOUT, interval=WAIT_INTERVAL)
    return bot.wait_for(template, timeout=WAIT_TIMEOUT, threshold=threshold, interval=WAIT_INTERVAL)


def _open_shop(bot) -> bool:
    """Màn chính -> Liên minh -> Alliance Shop. True nếu tới màn Alliance Shop."""
    targets = [
        # Popup mua vẫn để lộ title phía sau; phải đóng nó trước khi quét shop.
        (PLUS, _BACK),
        (SHOP_TITLE, _ON_SHOP),
        (_OUT_ALLIANCE, _OUT),
        (SHOP_ROW, _ROW),
        (_ALLIANCE_SCROLL, _SCROLL),
        *[(path, _BACK) for path in exit_images()],
        *[(path, _TAP) for path in click_images()],
        (_ALLIANCE_BUTTON, _OPEN),
    ]
    for _ in range(NAV_MAX_STEPS):
        screen = bot.screenshot()
        if no_alliance.check(bot, screen):
            return False
        action, pos = find_first(bot, screen, targets, top_left={_OUT})
        if action == _ON_SHOP:
            return True
        if action == _ROW:
            bot.tap(*pos)
            if _wait(bot, SHOP_TITLE) is not None:
                return True
        elif action == _TAP:
            bot.tap(*pos)
            delay(bot, 2)
        elif action == _OPEN:
            bot.tap(*pos)
            if no_alliance.wait_menu(bot):
                return False
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
        center = (normal_x + w // 2, normal_y + top + h // 2)
        if _truce_color_matches(bot, screen, center, template):
            return center, float(score), False
    mask = np.full((h, w), 255, dtype=np.uint8)
    mask[int(h * .22):int(h * .78), int(w * .22):int(w * .78)] = 0
    result = cv2.matchTemplate(area, tpl, cv2.TM_CCORR_NORMED, mask=mask)
    result = np.nan_to_num(result, nan=-1.0, posinf=-1.0, neginf=-1.0)
    _, masked_score, _, (x, y) = cv2.minMaxLoc(result)
    if masked_score < LOCKED_ITEM_THRESHOLD:
        return None, max(float(score), float(masked_score)), True
    center = (x + w // 2, y + top + h // 2)
    if not _truce_color_matches(bot, screen, center, template):
        return None, max(float(score), float(masked_score)), True
    return center, float(masked_score), True


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
        bar = (max(0, plus[0] - MAX_BAR_WIDTH), top, MAX_BAR_WIDTH, MAX_CROP_HALF_HEIGHT * 2)
        before = bot.crop(screen, *bar)
        bot.tap(left + slider[0], top + slider[1], delay=1)
        after = bot.screenshot()
        if bot.find(MAX_SELECTED, threshold=POPUP_TEMPLATE_THRESHOLD, screen=after) is not None:
            bot.record(f"{LABEL}: đã chọn MAX")
            return True
        # Chỉ còn 1 lượt (VD 1 / 1): thanh không kéo được, không bao giờ hiện thanh MAX xanh.
        # Bấm 2 lần mà thanh không đổi chút nào thì coi như số lượng đã tối đa.
        if attempt >= 2 and cv2.absdiff(before, bot.crop(after, *bar)).mean() < MAX_BAR_STILL_DIFF:
            bot.record(f"{LABEL}: thanh số lượng không kéo được (chỉ còn 1 lượt); coi như đã MAX")
            return True
        bot.record(f"{LABEL}: chưa xác nhận được MAX; bấm lại ({attempt}/{MAX_SELECT_TRIES})")
    return False


def _buy(bot, icon, name: str) -> str:
    """Mở popup, chọn MAX bằng thanh trượt, mua và xác nhận.

    Trả _BOUGHT (đã Confirm: ghi DONE món này), _NO_POINTS (nút Buy xám = không đủ điểm: dừng cả phiên)
    hoặc _PENDING (không thấy popup / chưa mua được: không đánh dấu, lần sau làm lại).
    """
    bot.tap(icon[0], icon[1] + PRICE_DY)
    plus = _wait(bot, PLUS, POPUP_TEMPLATE_THRESHOLD)
    if plus is None:
        bot.record(f"{LABEL}: {name} không hiện popup mua; giữ PENDING")
        return _PENDING
    # Popup vừa hiện còn đang phóng to: chờ 1 giây rồi tìm lại dấu + (vị trí lúc đang mở bị lệch, bấm thanh MAX hụt).
    bot.sleep(1)
    plus = bot.find(PLUS, threshold=POPUP_TEMPLATE_THRESHOLD) or plus
    if not _select_max(bot, plus):
        bot.record(f"{LABEL}: {name} chưa chọn được MAX; giữ PENDING")
        bot.back(delay=1)
        return _PENDING
    buy = (bot.window_size()[0] // 2, plus[1] + BUY_DY)
    if not _buy_button_active(bot, bot.screenshot(), buy):
        bot.record(f"{LABEL}: {name} nút Buy xám = không đủ Alliance Points; dừng mua")
        bot.back(delay=1)
        return _NO_POINTS
    bot.tap(*buy)
    # Bấm mua chỉ mở hộp xác nhận: phải bấm Confirm mới mua thật (chỉ khi đó mới lưu DB).
    confirm = _wait(bot, CONFIRM_BUTTON)
    if confirm is None:
        if bot.find(PLUS, threshold=POPUP_TEMPLATE_THRESHOLD) is not None:
            bot.record(f"{LABEL}: {name} no confirm dialog and buy popup still open, back, not bought")
            bot.back(delay=1)
            return _PENDING
        bot.record(f"{LABEL}: {name} no confirm dialog but popup closed, assume bought")
        return _BOUGHT
    bot.tap(*confirm, delay=BUY_WAIT)
    if (bot.find(PLUS, threshold=POPUP_TEMPLATE_THRESHOLD) is not None or
            bot.find(CONFIRM_BUTTON) is not None):
        bot.record(f"{LABEL}: {name} still showing buy dialog after Confirm, back, not saved")
        bot.back(delay=1)
        return _PENDING
    bot.record(f"{LABEL}: đã mua {name} và xác nhận")
    return _BOUGHT


# ---- Luật của việc (bảng bot/worker/priority.py: "run": JOB) -------------------------------------------------------
def _enabled(settings: dict) -> bool:
    """Ô tích "Alliance VIP" ở tab Daily Activities; thiếu = tích (mặc định)."""
    return settings.get(LABEL, True) is not False


def _item_done_key(key: str) -> str:
    return f"Alliance VIP: {key}"


def _selection(settings: dict) -> dict[str, int]:
    return normalized(settings.get(SETTINGS_KEY), legacy_defaults=True)


def _done_key(item_key: str) -> str:
    """Dấu "xong hôm nay" của một món: VIP/Tribute chỉ mua ở Daily Sale nên dùng khóa Daily của chúng."""
    if item_key == "tribute":
        return TRIBUTE_DAY_KEY
    if item_key == "vip_points":
        return DAY_KEY
    return _item_done_key(item_key)


def _catalog_done(ctx, settings: dict) -> bool:
    """Xong hôm nay khi mọi món ĐANG tích đã có khóa riêng: tích thêm món mới (VD Tribute sau khi mua VIP) thì làm tiếp."""
    return _all_selected_items_done(ctx, settings)


def _all_selected_items_done(ctx, settings: dict) -> bool:
    """Mọi checkbox đã có khóa riêng."""
    selected = _selection(settings)
    return all(ctx.is_daily_done(_done_key(item.key)) for item in ITEMS if selected[item.key] > 0)


def _visible_section_ranges(ctx, screen, daily_reached: bool,
                            weekly_reached: bool):
    """Vùng y được mua trên khung: chỉ từ tiêu đề Daily Sale trở xuống, không mua Monthly ở trên.

    "daily" = giữa Daily Sale và Weekly Sale (VIP/Tribute), "below" = từ Daily Sale tới đáy (mọi món khác);
    "daily_y" / "weekly_y" = y của tiêu đề đang thấy (None = không thấy).
    """
    top, bottom = int(screen.shape[0] * .08), int(screen.shape[0] * .94)
    daily = ctx.find(DAILY_HEADER, screen=screen)
    weekly = ctx.find(WEEKLY_HEADER, screen=screen)
    daily_reached = daily is not None or weekly is not None or daily_reached
    weekly_reached = weekly is not None or weekly_reached
    ranges = {"daily": None, "below": None,
              "daily_y": daily[1] if daily is not None else None,
              "weekly_y": weekly[1] if weekly is not None else None}
    if daily_reached:
        start = daily[1] if daily is not None else top
        ranges["below"] = (start, bottom)
        if weekly is not None:
            ranges["daily"] = (start, weekly[1])
        elif not weekly_reached:
            ranges["daily"] = (start, bottom)
    return ranges, daily_reached, weekly_reached


def _swipe(ctx, swipe, duration: float) -> None:
    """Bấm tiêu đề shop (50%, 3%) trước khi cuộn: lỡ bấm trúng vật phẩm (hiện ô mô tả) thì shop không cuộn được.

    Chỉ bấm khi đang thấy màn Alliance Shop (tiêu đề shop); màn khác thì không bấm chỗ đó.
    """
    if ctx.find(SHOP_TITLE) is not None:
        ctx.tap_percent(*UNFOCUS_TAP)
    ctx.swipe_percent(*swipe, duration=duration, delay=SCAN_SETTLE)


def _bottom_reached(ctx, screen, ranges: dict, weekly_reached: bool) -> bool:
    """Giới hạn cuộn xuống: thấy Truce nằm dưới tiêu đề Weekly Sale (hàng cuối danh sách)."""
    weekly_y = ranges.get("weekly_y")
    if weekly_y is None and not weekly_reached:
        return False
    for item in _TRUCE_ITEMS:
        if not (TEMPLATE_DIR / item.template).is_file():
            continue
        pos = ctx.find(item.template, threshold=ITEM_THRESHOLD, screen=screen)
        if pos is not None and (weekly_y is None or pos[1] > weekly_y):
            return True
    return False


def _fast_scroll(ctx, items) -> None:
    """Cuộn thật nhanh xuống cho tới khi thấy VIP/Tribute ở Daily Sale (tối đa FAST_SWIPES lần)."""
    for attempt in range(1, FAST_SWIPES + 1):
        _swipe(ctx, FAST_SWIPE, FAST_SWIPE_DURATION)
        screen = ctx.screenshot()
        ranges, _, _ = _visible_section_ranges(ctx, screen, True, False)
        if ranges["daily"] is None:
            continue
        for item in items:
            if _find_item(ctx, screen, item.template, y_range=ranges["daily"])[0] is not None:
                ctx.record(f"{LABEL}: cuộn nhanh {attempt} lần thì thấy {item.label}")
                return
    ctx.record(f"{LABEL}: cuộn nhanh {FAST_SWIPES} lần chưa thấy VIP/Tribute; quét tiếp từ đây")


def _mark_visible_done(ctx, done_key: str, label: str) -> None:
    ctx.mark_daily_done(done_key)
    ctx.record(f"{LABEL}: {label} nút giá xám; ghi DONE vào DB")


def _run_shop_session(ctx, settings: dict,
                      priority_filter: set[str] | None = None) -> None:
    """Mở shop đúng một lần, xử lý mọi món nhìn thấy rồi mới cuộn/thoát.

    Có tích VIP/Tribute: cuộn nhanh xuống tới chúng, mua, rồi cuộn chậm xuống tới Truce cuối danh sách và cuộn chậm
    lên tới tiêu đề Daily Sale, mua từng món đã tích. Không tích: cuộn chậm từ đầu xuống tới Truce cuối danh sách.
    Mua đủ thì dừng ngay.
    """
    selected = _selection(settings)
    enabled = [item for item in ITEMS if selected[item.key] > 0]
    if not enabled:
        return
    available = [item for item in enabled if (TEMPLATE_DIR / item.template).is_file()]
    missing = [item for item in enabled if item not in available]
    if missing:
        ctx.record(f"{LABEL}: thiếu ảnh chuẩn Alliance Shop cho: " +
                   ", ".join(item.label for item in missing))
    if priority_filter is not None:
        available = [item for item in available if _done_key(item.key) in priority_filter]
    available = [item for item in available if not ctx.is_daily_done(_done_key(item.key))]
    if not available or not _open_shop(ctx):
        return

    priority = [item for item in available if item.key in PRIORITY_KEYS]
    daily_reached = False
    if priority:
        _fast_scroll(ctx, priority)
        daily_reached = True
    attempted: set[str] = set()  # mỗi món chỉ thử mua một lần/lượt
    best_scores: dict[str, float] = {}
    weekly_reached = False
    going_down = True
    for step in range(SCROLLS + 1):
        # Xử lý hết mọi vật phẩm trong cùng khung; popup đóng xong chụp lại,
        # tuyệt đối không Back ra Alliance Shop rồi vào lại.
        for _ in range(len(ITEMS) + 4):
            ctx.check()
            screen = ctx.screenshot()
            # Cuộn lên thì đang ở trên Weekly Sale khi không thấy tiêu đề này.
            ranges, daily_reached, weekly_reached = _visible_section_ranges(
                ctx, screen, daily_reached, weekly_reached and going_down)
            # Tribute, VIP trước (chỉ giữa Daily Sale và Weekly Sale), rồi tới món khác từ Daily Sale trở xuống.
            candidates = []
            for item in sorted(available, key=lambda item: item.key not in PRIORITY_KEYS):
                done_key = _done_key(item.key)
                y_range = ranges["daily" if item.key in PRIORITY_KEYS else "below"]
                if y_range is not None and not ctx.is_daily_done(done_key):
                    candidates.append((item, done_key, y_range))

            handled = False
            no_points = False
            for item, done_key, y_range in candidates:
                icon, score, locked_match = _find_item(
                    ctx, screen, item.template, y_range=y_range)
                best_scores[done_key] = max(best_scores.get(done_key, 0.0), score)
                if icon is None:
                    continue
                ctx.record(f"{LABEL}: thấy {item.label}, điểm {score:.3f}" +
                           (" (so viền)" if locked_match else ""))
                if not _price_green(ctx, screen, icon):
                    _mark_visible_done(ctx, done_key, item.label)
                    handled = True
                    break
                # So viền chỉ dùng để nhận món Sold Out / bị khoá (giá xám). Giá xanh mà chỉ khớp viền thì không mua:
                # món khác cùng màu khung (VD kiếm tím 15.000 khớp viền Truce 8h) không được chiếm lượt thử.
                if locked_match:
                    ctx.record(f"{LABEL}: {item.label} chỉ khớp viền mà giá xanh; bỏ qua")
                    continue
                if done_key in attempted:
                    continue
                attempted.add(done_key)
                result = _buy(ctx, icon, item.label)
                if result == _BOUGHT:
                    # Mua xong (đã Confirm) là xong món này, bỏ khỏi danh sách; không chờ nút giá xám.
                    ctx.mark_daily_done(done_key)
                    ctx.record(f"{LABEL}: {item.label} đã mua; ghi DONE vào DB")
                no_points = result == _NO_POINTS
                handled = True
                break
            if no_points or not handled:
                break

        if no_points:
            # Không đủ điểm: mọi món đã tích coi như hôm nay đã mua xong, thoát shop luôn.
            for item in available:
                ctx.mark_daily_done(_done_key(item.key))
            ctx.record(f"{LABEL}: không đủ Alliance Points; đánh dấu mọi món đã tích là xong hôm nay")
            break

        if all(ctx.is_daily_done(_done_key(item.key)) for item in available):
            ctx.record(f"{LABEL}: mọi vật phẩm đã tích đã DONE ngay trong phiên shop hiện tại")
            break
        if going_down and _bottom_reached(ctx, screen, ranges, weekly_reached):
            if not priority:
                ctx.record(f"{LABEL}: thấy Truce cuối danh sách; đã quét hết")
                break
            ctx.record(f"{LABEL}: thấy Truce cuối danh sách; cuộn chậm lên tới Daily Sale")
            going_down = False
        elif not going_down and ranges.get("daily_y") is not None:
            ctx.record(f"{LABEL}: cuộn lên tới tiêu đề Daily Sale; đã quét hết")
            break
        if step >= SCROLLS:
            ctx.record(f"{LABEL}: đã đủ {SCROLLS} lượt cuộn; dừng theo trần an toàn")
            break
        ctx.record(f"{LABEL}: đã xử lý hết khung {step + 1}/{SCROLLS + 1}; "
                   f"cuộn chậm {'xuống' if going_down else 'lên'}")
        _swipe(ctx, SWIPE if going_down else SWIPE_UP, SWIPE_DURATION)

    for _ in range(2):
        ctx.back(delay=1)
    pending_labels = [f"{item.label} ({best_scores.get(_done_key(item.key), 0):.3f})"
                      for item in available if not ctx.is_daily_done(_done_key(item.key))]
    if pending_labels:
        ctx.record(f"{LABEL}: kết thúc một lượt shop, còn PENDING: " + ", ".join(pending_labels))


def buy_vip(bot) -> None:
    """API cũ: mua 100 VIP Points ở Daily Sale trong một lần vào shop."""
    settings = {SETTINGS_KEY: {item.key: item.key == "vip_points" for item in ITEMS}}
    _run_shop_session(bot, settings, priority_filter={DAY_KEY})


@save_errors("daily_alliance_vip")   # lỗi thì lưu `daily_alliance_vip_error` vào DB
def _run(ctx, settings: dict):
    ctx.log(f"Daily Activities: {LABEL} — một lần vào shop, xử lý liên tục từ trên xuống")
    _run_shop_session(ctx, settings)


JOB = {"run": _run, "enabled": _enabled, "done": _catalog_done}
