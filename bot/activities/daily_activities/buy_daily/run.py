"""run.py — Daily Activities "General": mua Stamina + Hammer (bắt đầu từ màn chính, bấm góc trên bên phải).

This is a direct, bounded port of ``Data.BuyStamina`` and
``Data.BuyHammer`` from the C# project.  Both flows use the existing
``Images/DailyActivites/ActivitiesBuyDaily`` templates; adaptive position caching makes repeated
matches use a small region while retaining a full-screen fallback.
"""
import re

import cv2
import numpy as np

from ....ocr._digits import read as read_digits
from ...result import TaskResult
from ..constants import HAMMER_DONE, STAMINA_REACHED
from ....common import click_images, delay, exit_images, find_first, go_home

BUY = "DailyActivites/ActivitiesBuyDaily"
FEATURES_ICON = "OpenBox/Setup/chucnang.png"   # ảnh dùng chung với OpenBox
OPEN_FEATURES = "open_features"
FEATURES_BUTTON = (88.5, 5)   # % màn hình: góc trên bên phải của màn chính
OPEN_WAIT = 10                # tối đa chừng này lần chờ 1s để màn đổi sau khi bấm
CHANGED_DIFF = 3.0            # chênh lệch điểm ảnh trung bình coi là "đã chuyển màn"
TAP = "tap"
BACK = "back"
MAX_STEPS = 100
COST_CROP = (170, 440, 75, 24)   # vùng số kim cương trên nút xanh của popup (màn 396x704); icon kim cương dịch trái theo độ dài số
COST_FONT = "BuyCost"            # mẫu chữ số Images/OCR/BuyCost (số trên nút xanh, đã lọc màu kem)
HAMMER_SOLD_OUT = f"{BUY}/HammerSoldOut.png"   # nút giá xám của dòng Hammer ("Daily Limit: 0 / 10"): hết lượt hôm nay
SOLD_OUT_THRESHOLD = 0.97   # nút giá còn lượt (cam) khớp 0,88 với mẫu xám: phải đặt cao hơn
PLUS_WAIT = 0.5                  # giây giữa hai lần bấm "+" / "-"
# Giá Stamina (không giới hạn số lượng): (số lượng của bậc, giá kim cương mỗi cái), đo trên popup thật (tests/.../screens/06..24)
# khi hôm nay đã mua đúng 1 cái (người dùng xác nhận): cái 1-10: 200, 11-16: 400, 17-19: 800, 20-22: 1600, 23-25: 3200, 26-31: 6400. Chỉ mua tới cái 20;
# các bậc sau chỉ để phân biệt được số đã mua khi giá đang 800 / 1600.
STAMINA_TIERS = ((10, 200), (6, 400), (3, 800), (3, 1600), (3, 3200), (6, 6400))
# Mốc người dùng chọn (tab UI): tổng số cái mua trong ngày.
STAMINA_MILESTONES = (10, 16, 20)
STAMINA_LIMIT = 25   # số cái đã mua tối đa bot còn phân biệt được (stamina_done)

def run(bot, stamina_quantity: int, hammers: bool) -> TaskResult:
    """General: một nhiệm vụ mua cả hai món đã chọn — Stamina tới mốc `stamina_quantity` (0/10/16/20, 0 = không mua) rồi
    Hammer (`hammers`). done=True khi mọi món cần mua đã mua xong. `outcomes`: kết quả từng món (key = dấu "xong hôm nay"
    của món đó, worker ghi lại: Stamina kèm mốc đã đạt, Hammer)."""
    outcomes = []
    if stamina_quantity > 0:
        ok = bool(buy_stamina(bot, stamina_quantity))
        outcomes.append(TaskResult(done=ok, reached=stamina_quantity, label="Stamina",
                                   key=f"{STAMINA_REACHED} {stamina_quantity}"))
    if hammers:
        outcomes.append(TaskResult(done=bool(buy_all_hammers(bot)), label="Hammer", key=HAMMER_DONE))
    return TaskResult(done=all(o.done for o in outcomes), outcomes=tuple(outcomes))


def _positions(bot):
    cache = getattr(bot, "_daily_image_positions", None)
    if cache is None:
        cache = {}
        bot._daily_image_positions = cache
    return cache


def _find(bot, screen, targets):
    return find_first(bot, screen, targets, position_cache=_positions(bot), fallback_full=True)


def _common_targets():
    return ([(path, BACK) for path in exit_images()]
            + [(path, TAP) for path in click_images()])


def stamina_price(n: int) -> int:
    """Giá kim cương của cái Stamina thứ `n` trong ngày (1, 2, ...)."""
    start = 0
    for count, price in STAMINA_TIERS:
        start += count
        if n <= start:
            return price
    return STAMINA_TIERS[-1][1]


def stamina_total(done: int, count: int) -> int:
    """Tổng kim cương để mua thêm `count` cái khi hôm nay đã mua `done` cái."""
    return sum(stamina_price(n) for n in range(done + 1, done + count + 1))


def stamina_done(costs: list[int], limit: int = STAMINA_LIMIT) -> list[int]:
    """Số cái đã mua hôm nay khớp với Cost đọc được: costs[i] = Cost khi ô số lượng là i + 1.
    Trả mọi giá trị khớp (nhiều hơn 1 = chưa phân biệt được, đọc thêm một mức số lượng)."""
    return [done for done in range(limit)
            if all(stamina_total(done, i + 1) == cost for i, cost in enumerate(costs))]


def read_cost(bot, screen=None) -> int | None:
    """Số kim cương trên nút xanh của popup mua (read_number); None nếu không đọc được. Chữ số màu kem (R cao hơn B),
    icon kim cương xanh trắng (B cao hơn R): chỉ giữ điểm ảnh màu kem nên icon không lẫn vào số."""
    screen = bot.screenshot() if screen is None else screen
    x, y, w, h = COST_CROP
    crop = bot.crop(screen, x, y, w, h).astype(int)
    blue, green, red = crop[..., 0], crop[..., 1], crop[..., 2]
    mask = ((red > 150) & (green > 150) & (red - blue > 25)).astype(np.uint8) * 255
    digits = re.sub(r"\D", "", read_digits(mask, COST_FONT) or "")
    return int(digits) if digits and int(digits) > 0 else None


def _close_popup(bot):
    bot.back(delay=1)


def _buy_in_popup(bot, screen, target: int) -> bool:
    """Popup mua Stamina đang mở ở số lượng 1. Không mua lại cái đã mua hôm nay:
    1. OCR Cost (số lượng 1) -> các khả năng số cái đã mua (stamina_done); lấy nhỏ nhất `k`.
    2. k >= target: đã đủ -> đóng popup, không mua.
    3. Bấm "+" lên (target - k) cái, OCR lại Cost -> biết chính xác số đã mua.
    4. Thực tế đã mua nhiều hơn k -> bấm "-" lùi số bước dư, rồi bấm nút mua.
    Không đọc được Cost: không mua (tránh tốn kim cương)."""
    cost = read_cost(bot, screen)
    candidates = stamina_done([cost]) if cost is not None else []
    if not candidates:
        bot.log(f"Daily General: cannot read Stamina cost ({cost}), not buying")
        _close_popup(bot)
        return False
    done = min(candidates)
    if done >= target:
        bot.log(f"Daily General: already bought {done} Stamina today (target {target})")
        _close_popup(bot)
        return True
    count = target - done
    plus = bot.find(f"{BUY}/plus.png", screen=screen)
    if plus is None:
        bot.log("Daily General: Stamina '+' not found")
        _close_popup(bot)
        return False
    _positions(bot)[f"{BUY}/plus.png"] = plus
    if count > 1:
        for _ in range(count - 1):
            bot.tap(*plus, delay=PLUS_WAIT)
        total = read_cost(bot)
        exact = [k for k in candidates if stamina_total(k, count) == total]
        if not exact:
            bot.log(f"Daily General: Stamina cost {total} for {count} does not match, not buying")
            _close_popup(bot)
            return False
        extra = exact[0] - done   # thực tế đã mua nhiều hơn -> lùi lại
        if extra > 0:
            minus = (screen.shape[1] - plus[0], plus[1])   # "-" đối xứng với "+"
            for _ in range(extra):
                bot.tap(*minus, delay=PLUS_WAIT)
            done, count = exact[0], count - extra
            if count <= 0:
                bot.log(f"Daily General: already bought {done} Stamina today (target {target})")
                _close_popup(bot)
                return True
    bot.tap(screen.shape[1] // 2, plus[1] + 110, delay=5)
    bot.log(f"Daily General: Buy Stamina x{count} ({done} bought before, {stamina_total(done, count)} gems)")
    return True


def open_features(bot) -> bool:
    """Ở màn chính: bấm góc trên bên phải, chờ 1s xem đã chuyển màn chưa, chưa thì chờ thêm 1s (tối đa OPEN_WAIT lần).
    True khi màn đã đổi."""
    before = bot.screenshot()
    bot.tap_percent(*FEATURES_BUTTON)
    for _ in range(OPEN_WAIT):
        bot.sleep(1)
        after = bot.screenshot()
        if float(cv2.absdiff(before, after).mean()) >= CHANGED_DIFF:
            return True
    bot.log("Daily General: screen did not change after opening features")
    return False


def buy_stamina(bot, target: int) -> bool:
    """Mua Stamina tới mốc `target` cái trong ngày (10 / 16 / 20), chỉ mua phần chưa mua."""
    target = max(1, int(target))
    targets = [
        (f"{BUY}/buystamina.png", "buy"),
        (f"{BUY}/stamina.png", "stamina"),
        (f"{BUY}/checkWar.png", "war_selected"),
        (f"{BUY}/war.png", TAP),
        (f"{BUY}/item.png", TAP),
        *_common_targets(),
        (FEATURES_ICON, OPEN_FEATURES),
    ]
    war_scrolls = 0
    open_features(bot)

    for _ in range(MAX_STEPS):
        bot.check()
        screen = bot.screenshot()
        action, pos = _find(bot, screen, targets)

        if action == "buy":
            return _buy_in_popup(bot, screen, target)
        if action == "stamina":
            bot.tap(334, pos[1], delay=2)
        elif action == "war_selected":
            bot.swipe_percent(50, 80, 50, 60, delay=2)
            war_scrolls += 1
            if war_scrolls > 4:
                bot.back(delay=2)
                war_scrolls = 0
        elif action == OPEN_FEATURES:
            bot.tap_percent(88.5, 5, delay=2)
        elif action == TAP:
            bot.tap(*pos, delay=2)
        elif action == BACK:
            bot.back(delay=2)
        else:
            go_home(bot, screen)
            delay(bot, 2)

    bot.log("Daily General: Buy Stamina stopped after too many unrecognized steps")
    return False


def buy_all_hammers(bot) -> bool:
    """Buy the hammer offer found in the Special section."""
    targets = [
        (f"{BUY}/bua.png", "hammer"),
        (f"{BUY}/checkSpecial.png", "special_selected"),
        (f"{BUY}/special.png", TAP),
        (f"{BUY}/item.png", TAP),
        *_common_targets(),
        (FEATURES_ICON, OPEN_FEATURES),
    ]
    special_checks = 0
    open_features(bot)

    for _ in range(MAX_STEPS):
        bot.check()
        screen = bot.screenshot()
        action, pos = _find(bot, screen, targets)

        if action == "hammer":
            plus_path = f"{BUY}/plus.png"
            plus = bot.find(plus_path, screen=screen)
            if plus is None:
                bot.tap_percent(87.5, 35, delay=2)
                continue
            _positions(bot)[plus_path] = plus
            # C# taps left of Plus to choose the maximum/all quantity.
            bot.tap(plus[0] - 20, plus[1] + 2)
            bot.tap(screen.shape[1] // 2, plus[1] + 110, delay=5)
            return True
        if action == "special_selected":
            if bot.find(HAMMER_SOLD_OUT, threshold=SOLD_OUT_THRESHOLD, screen=screen) is not None:
                bot.log("Daily General: hammers already bought today")
                return True
            bot.tap(*pos)
            special_checks += 1
            bot.tap_percent(87.5, 35, delay=2)
            if special_checks > 5:
                bot.log("Daily General: hammer offer not found")
                return False
        elif action == OPEN_FEATURES:
            bot.tap_percent(88.5, 5, delay=2)
        elif action == TAP:
            bot.tap(*pos, delay=2)
        elif action == BACK:
            bot.back(delay=2)
        else:
            go_home(bot, screen)
            delay(bot, 2)

    bot.log("Daily General: Buy All Hammers stopped after too many unrecognized steps")
    return False



