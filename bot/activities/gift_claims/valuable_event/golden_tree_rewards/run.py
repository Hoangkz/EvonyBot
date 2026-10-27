"""Golden Tree Rewards: tích Skip animation, chưa chọn quà mục tiêu (ô dấu +) thì chọn vàng, rồi bấm các nút tốn xu còn đủ xu."""
import cv2

from ...common import GiftTask, find
from ...screens import GiftScreen
from ..named_flow import ExactFlow, LOWER_CONTENT, STEP_DELAY, run_carousel_exact
from ..wheel_of_dragon_war.run import ensure_skip_animation

KEY = "gift_golden_tree_rewards"
FOLDER = "ValuableEvent/GoldenTreeRewards/"
PAGE = FOLDER + "page_header"            # dòng "Golden Bough Coins used:" (bị popup che thì không thấy)
SLOT_PLUS = FOLDER + "slot_plus"         # ô quà mục tiêu còn dấu + = chưa chọn quà
POPUP = FOLDER + "popup_title"           # chữ "Click to select a reward!" của popup Rewards
GOLD = FOLDER + "reward_gold"            # ô vàng 1M trong popup
CONFIRM = FOLDER + "button_confirm"
# Đo trên màn 396x704: đúng chỗ 1.00, chỗ khác <= 0.58.
THRESHOLD = 0.8
WAITS = 5                                # chờ popup mở / về lại trang: tối đa chừng này lần, mỗi lần 1s
# Ô Skip animation dưới bên phải (màn 396x704): đã tích có ~94 điểm xanh trong SKIP_BOX, popup che thì 0.
SKIP_TAP = (291, 573)
SKIP_BOX = (279, 562, 304, 584)
ATTEMPTS = 3                             # chờ WAITS lần không thấy thì làm lại từ đầu, tối đa chừng này lượt
# Ba nút dưới cùng (màn 396x704) theo thứ tự ưu tiên lớn xuống bé: (giá xu, x tâm). Icon nút ở y BUTTON_Y (~88%); số giá nằm
# ngay dưới ở DIGIT_Y (~91-93%). Số đỏ = không đủ xu: đo lúc 0 xu, số "1" 24 điểm đỏ, "5" 32, "10" 86.
BUTTONS = ((10, 325), (5, 199), (1, 73))
BUTTON_Y = 620
DIGIT_Y = (640, 657)
DIGIT_HALF = 12                          # px: lấy số trong khoảng x tâm +- chừng này (không lấy đồng xu bên trái)
RED_MIN = 10                             # số có từ chừng này điểm đỏ = số đỏ
MAX_SPENDS = 30                          # bấm nút tốn xu tối đa chừng này lần mỗi lần chạy
# Bấm nút tốn xu -> popup chữ "Congratulations!" (ảnh chung của activity Event / Crazy Eggs, ngưỡng 0.9), đóng bằng Back.
CONGRATULATIONS = "Event/congratulations.png"
CONGRATS_THRESHOLD = 0.9
POPUP_WAITS = {1: 3}                     # số lần chờ popup theo giá nút: nút 1 xu chờ 3 lần, nút khác WAITS lần


def _see(bot, name, screen=None):
    return find(bot, name, screen, threshold=THRESHOLD, region=LOWER_CONTENT)


def _wait(bot, check, waits: int = WAITS) -> bool:
    """Mỗi 1s chụp kiểm tra `check(screen)`, tối đa `waits` lần."""
    for _ in range(waits):
        bot.sleep(STEP_DELAY)
        if check(bot.screenshot()):
            return True
    return False


def _page_ready(bot, screen) -> bool:
    """Đang ở trang Golden Tree Rewards (không popup che) và quà mục tiêu đã chọn (không còn dấu +)."""
    return _see(bot, PAGE, screen) is not None and _see(bot, SLOT_PLUS, screen) is None


def select_reward(bot) -> bool:
    """Ô quà mục tiêu còn dấu + thì bấm, chờ popup Rewards (1s x WAITS), bấm ô vàng, nghỉ 1s, bấm Confirm rồi chờ về trang
    (1s x WAITS). Chờ WAITS lần không thấy (hoặc popup thiếu ô vàng / Confirm: Back đóng popup) thì làm lại từ đầu, tối đa
    ATTEMPTS lượt. True khi ở trang và không còn dấu +."""
    for attempt in range(1, ATTEMPTS + 1):
        bot.check()
        screen = bot.screenshot()
        plus = _see(bot, SLOT_PLUS, screen)
        if plus is None:
            if _page_ready(bot, screen):
                bot.record("Gift Claims: Golden Tree Rewards đã chọn quà")
                return True
            bot.record("Gift Claims: Golden Tree Rewards không thấy trang event; giữ PENDING")
            return False
        bot.record(f"Gift Claims: Golden Tree Rewards chưa chọn quà; bấm ô dấu + (lượt {attempt}/{ATTEMPTS})")
        bot.tap(*plus)
        if not _wait(bot, lambda s: _see(bot, POPUP, s) is not None):
            bot.record(f"Gift Claims: bấm dấu + {WAITS}s vẫn chưa mở popup Rewards; làm lại từ đầu")
            continue
        gold = _see(bot, GOLD)
        if gold is None:
            bot.record("Gift Claims: popup Rewards không thấy ô vàng; Back đóng popup, làm lại từ đầu")
            bot.back(delay=STEP_DELAY)
            continue
        bot.record("Gift Claims: Golden Tree Rewards chọn vàng")
        bot.tap(*gold)
        bot.sleep(STEP_DELAY)
        confirm = _see(bot, CONFIRM)
        if confirm is None:
            bot.record("Gift Claims: popup Rewards không thấy Confirm; Back đóng popup, làm lại từ đầu")
            bot.back(delay=STEP_DELAY)
            continue
        bot.tap(*confirm)
        if _wait(bot, lambda s: _page_ready(bot, s)):
            bot.record("Gift Claims: Golden Tree Rewards đã chọn vàng")
            return True
        bot.record(f"Gift Claims: bấm Confirm {WAITS}s vẫn chưa về trang (hoặc còn dấu +); làm lại từ đầu")
    bot.record(f"Gift Claims: Golden Tree Rewards {ATTEMPTS} lượt chưa chọn được quà; giữ PENDING")
    return False


def _red(screen, x: int) -> bool:
    """Số giá dưới nút có tâm `x` màu đỏ (không đủ xu)."""
    scale = screen.shape[1] / 396
    top, bottom = round(DIGIT_Y[0] * scale), round(DIGIT_Y[1] * scale)
    left, right = round((x - DIGIT_HALF) * scale), round((x + DIGIT_HALF) * scale)
    hsv = cv2.cvtColor(screen[top:bottom, left:right], cv2.COLOR_BGR2HSV)
    red = ((hsv[..., 0] <= 10) | (hsv[..., 0] >= 170)) & (hsv[..., 1] > 120) & (hsv[..., 2] > 90)
    return int(red.sum()) >= RED_MIN * scale * scale


def affordable(screen) -> "tuple[int, int] | None":
    """(giá, x) của nút giá lớn nhất có số không đỏ, hoặc None khi cả ba số đều đỏ."""
    return next(((cost, x) for cost, x in BUTTONS if not _red(screen, x)), None)


def done_by_red_five_and_ten(screen) -> bool:
    """The user-defined terminal state: both 5- and 10-coin prices are red.

    The 1-coin control intentionally has no bearing on this event's Gift
    Claims result.  Check this before any Skip, reward-selection or coin tap
    so an already-terminal page is never changed.
    """
    buttons = dict(BUTTONS)
    return _red(screen, buttons[5]) and _red(screen, buttons[10])


def spend_coins(bot) -> bool:
    """Ở trang: bấm nút có số không đỏ, ưu tiên 10 -> 5 -> 1. Sau mỗi lần bấm, mỗi 1s kiểm tra popup "Congratulations!" đã ra
    chưa, tối đa POPUP_WAITS lần (nút 1 xu 3 lần, nút 5 / 10 WAITS lần). Ra popup thì Back đóng và chờ về trang (1s x WAITS);
    không ra thì thôi. Cả hai trường hợp đều quay lại bước tìm số không đỏ. True khi cả ba số đều đỏ (hết xu)."""
    for _ in range(MAX_SPENDS):
        bot.check()
        screen = bot.screenshot()
        if _see(bot, PAGE, screen) is None:
            bot.record("Gift Claims: Golden Tree Rewards không thấy trang event khi bấm nút tốn xu; giữ PENDING")
            return False
        hit = affordable(screen)
        if hit is None:
            bot.record("Gift Claims: Golden Tree Rewards số 1 / 5 / 10 đều đỏ (hết xu)")
            return True
        cost, x = hit
        scale = screen.shape[1] / 396
        bot.record(f"Gift Claims: Golden Tree Rewards bấm nút {cost} xu")
        bot.tap(round(x * scale), round(BUTTON_Y * scale))
        congrats = bot._template(CONGRATULATIONS)
        waits = POPUP_WAITS.get(cost, WAITS)
        if not _wait(bot, lambda s: bot.find(congrats, threshold=CONGRATS_THRESHOLD, screen=s) is not None, waits):
            bot.record(f"Gift Claims: bấm nút {cost} xu {waits}s chưa ra popup Congratulations; quay lại bước tìm")
            continue
        bot.record("Gift Claims: Golden Tree Rewards ra popup Congratulations; Back đóng popup")
        bot.back(delay=STEP_DELAY)
        if not _wait(bot, lambda s: _see(bot, PAGE, s) is not None):
            bot.record("Gift Claims: Back rồi chưa về trang Golden Tree Rewards; giữ PENDING")
            return False
    bot.record(f"Gift Claims: Golden Tree Rewards bấm {MAX_SPENDS} lần vẫn còn số không đỏ; giữ PENDING")
    return False


def claim(bot) -> bool:
    """Claim Golden Tree Rewards unless the two user-selected red prices end it.

    Seeing both 5 and 10 red is DONE immediately.  Otherwise keep the older
    selection/spend flow for a page that is not terminal yet.
    """
    screen = bot.screenshot()
    if _see(bot, PAGE, screen) is None:
        bot.record("Gift Claims: Golden Tree Rewards không thấy trang event; giữ PENDING")
        return False
    if done_by_red_five_and_ten(screen):
        bot.record("Gift Claims: Golden Tree Rewards nút 5 và 10 cùng đỏ; DONE")
        return True
    if not ensure_skip_animation(bot, SKIP_TAP, SKIP_BOX, "Golden Tree Rewards"):
        return False
    return select_reward(bot) and spend_coins(bot)


FLOW = ExactFlow(handler=claim)


def run(bot):
    return run_carousel_exact(
        bot,
        GiftScreen.VALUABLE_EVENT,
        "ValuableEvent/title",
        "ValuableEvent/GoldenTreeRewards/tab_icon",
        FLOW,
    )


TASK = GiftTask(KEY, "Golden Tree Rewards", run)
