"""Claim every available row in Refining Weekly Card.

Only the user-marked green reward frame is searched and scrolled. A clean
post-claim pass is ``DONE_1`` for the current 120-second window; durable DONE
requires a later full pass where every recognized row is yellow Continue.
"""
import cv2

from ...common import (GiftTask, close_congratulations, find_all,
                       return_home, select_carousel_tab)
from ...lobby import open_named
from ...screens import GiftScreen
from ...valuable_event.named_flow import (ExactFlow, SLOW_SWIPE_DURATION,
                                          STEP_DELAY, region_hamming_distance)

KEY = "gift_refining_weekly_card"
PAGE = "SuperValueReturn/title"
TAB = "SuperValueReturn/RefiningWeeklyCard/tab"
CLAIM = "SuperValueReturn/RefiningWeeklyCard/button_claim"
CONTINUE = "SuperValueReturn/RefiningWeeklyCard/button_continue"

# The user-marked green frame in the 396x704 reference screenshot is roughly
# x=10..380, y=474..689. Keep both search and every touch inside that frame.
REWARD_REGION = (2, 67, 98, 98)
SCAN_SWIPE = (50, 93, 50, 73)
RETURN_TOP_SWIPE = (50, 73, 50, 93)
MAX_CLAIMS_PER_VIEW = 12
CLAIM_THRESHOLD = 0.76
CONTINUE_THRESHOLD = 0.76
EDGE_CONFIRMATIONS = 2
SAME_DISTANCE = 24
GREEN_MIN_RATIO = 0.25
YELLOW_MIN_RATIO = 0.30

# Outcomes consumed by the parent Super Value Return zone. DONE_1 is not
# persisted and defers this task only for the current 120-second invocation.
DONE = "done"
DONE_1 = "done_1"
PENDING = "pending"

# Metadata for the zone registry. Completion belongs to claim_opened();
# Continue is deliberately absent from the generic DONE markers.
FLOW = ExactFlow(claims=(CLAIM,), scroll_claims=True)


def _button_crop(bot, screen, center, template_name):
    template = bot._template(template_name)
    scale = screen.shape[1] / 396
    width = max(1, round(template.shape[1] * scale))
    height = max(1, round(template.shape[0] * scale))
    left = max(0, center[0] - width // 2)
    top = max(0, center[1] - height // 2)
    return screen[top:min(screen.shape[0], top + height),
                  left:min(screen.shape[1], left + width)]


def _colour_ratios(crop) -> tuple[float, float]:
    """Return green and yellow/orange band ratios for a button crop."""
    if crop.size == 0:
        return 0.0, 0.0
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    green = ((hsv[..., 0] >= 35) & (hsv[..., 0] <= 90) &
             (hsv[..., 1] >= 60) & (hsv[..., 2] >= 50))
    yellow = ((hsv[..., 0] >= 5) & (hsv[..., 0] <= 35) &
              (hsv[..., 1] >= 60) & (hsv[..., 2] >= 50))
    return float(green.mean()), float(yellow.mean())


def _is_green_claim(bot, screen, center) -> bool:
    green, _ = _colour_ratios(_button_crop(bot, screen, center, CLAIM))
    return green >= GREEN_MIN_RATIO


def _is_yellow_continue(bot, screen, center) -> bool:
    _, yellow = _colour_ratios(_button_crop(bot, screen, center, CONTINUE))
    return yellow >= YELLOW_MIN_RATIO


def _green_claims(bot, screen) -> list[tuple[int, int]]:
    return [point for point in find_all(
        bot, CLAIM, screen, threshold=CLAIM_THRESHOLD, region=REWARD_REGION)
            if _is_green_claim(bot, screen, point)]


def _yellow_continues(bot, screen) -> list[tuple[int, int]]:
    return [point for point in find_all(
        bot, CONTINUE, screen, threshold=CONTINUE_THRESHOLD,
        region=REWARD_REGION)
            if _is_yellow_continue(bot, screen, point)]


def _swipe(bot, gesture) -> int:
    before = bot.screenshot()
    bot.swipe_percent(*gesture,
                      duration=SLOW_SWIPE_DURATION, delay=STEP_DELAY)
    after = bot.screenshot()
    return region_hamming_distance(before, after, REWARD_REGION)


def _swipe_to_top(bot) -> None:
    unchanged = 0
    while unchanged < EDGE_CONFIRMATIONS:
        bot.check()
        distance = _swipe(bot, RETURN_TOP_SWIPE)
        unchanged = unchanged + 1 if distance <= SAME_DISTANCE else 0
        bot.record("Gift Claims: Refining Weekly Card về đầu vùng xanh, "
                   f"Hamming {distance}/{SAME_DISTANCE}, không đổi "
                   f"{unchanged}/{EDGE_CONFIRMATIONS}")


def _claim_current_view(bot) -> tuple[bool, bool, bool]:
    """Return claimed, stuck, saw_yellow_continue."""
    claimed = False
    blocked: list[tuple[int, int]] = []
    for _ in range(MAX_CLAIMS_PER_VIEW):
        bot.check()
        screen = bot.screenshot()
        green_claims = _green_claims(bot, screen)
        candidates = [point for point in green_claims
                      if all((point[0] - old[0]) ** 2 +
                             (point[1] - old[1]) ** 2 > 30 ** 2
                             for old in blocked)]
        if not candidates:
            final = bot.screenshot()
            return (claimed, bool(green_claims),
                    bool(_yellow_continues(bot, final)))
        pos = candidates[0]
        claimed = True
        bot.record("Gift Claims: Refining Weekly Card thấy Claim có dải xanh; tap nhận")
        bot.tap(*pos, delay=STEP_DELAY)
        close_congratulations(bot, attempts=2)
        after = bot.screenshot()
        if any((point[0] - pos[0]) ** 2 + (point[1] - pos[1]) ** 2 <= 30 ** 2
               for point in _green_claims(bot, after)):
            blocked.append(pos)

    remains = bool(_green_claims(bot, bot.screenshot()))
    return claimed, remains, False


def _scan_full_list(bot) -> tuple[bool, bool, bool]:
    """Scan one full pass; return claimed, stuck, saw_continue."""
    _swipe_to_top(bot)
    saw_claim = saw_continue = False
    unchanged = 0
    position = 0
    while True:
        bot.check()
        position += 1
        bot.record(f"Gift Claims: Refining Weekly Card quét vùng xanh vị trí {position}")
        claimed, stuck, continues = _claim_current_view(bot)
        saw_claim = saw_claim or claimed
        saw_continue = saw_continue or continues
        if stuck:
            return saw_claim, True, saw_continue
        if claimed:
            unchanged = 0

        distance = _swipe(bot, SCAN_SWIPE)
        unchanged = unchanged + 1 if distance <= SAME_DISTANCE else 0
        bot.record("Gift Claims: Refining Weekly Card quét xuống đáy vùng xanh, "
                   f"Hamming {distance}/{SAME_DISTANCE}, không đổi "
                   f"{unchanged}/{EDGE_CONFIRMATIONS}")
        if unchanged < EDGE_CONFIRMATIONS:
            continue

        # Re-read the final viewport after the second no-movement swipe.
        claimed, stuck, continues = _claim_current_view(bot)
        saw_claim = saw_claim or claimed
        saw_continue = saw_continue or continues
        if stuck:
            return saw_claim, True, saw_continue
        if claimed:
            unchanged = 0
            continue
        return saw_claim, False, saw_continue


def claim_opened(bot) -> str:
    """Return DONE, DONE_1 or PENDING for an already selected card tab."""
    while True:
        bot.check()
        saw_claim, stuck, saw_continue = _scan_full_list(bot)
        if stuck:
            bot.record("Gift Claims: Refining Weekly Card vẫn còn Claim không "
                       "bấm được; giữ PENDING")
            return PENDING
        if saw_claim:
            bot.record("Gift Claims: Refining Weekly Card vừa nhận hết Claim xanh; "
                       "quay lại biên đầu để kiểm tra trạng thái sau nhận")
            continue
        if saw_continue:
            bot.record("Gift Claims: Refining Weekly Card không còn Claim và "
                       "toàn bộ trạng thái nhận diện được là Continue dải vàng; "
                       "DONE")
            return DONE
        bot.record("Gift Claims: Refining Weekly Card không còn Claim nhưng chưa "
                   "thấy toàn bộ Continue dải vàng; DONE_1, chuyển nhiệm vụ khác "
                   "và kiểm tra lại ở chu kỳ 120s sau")
        return DONE_1


def run(bot):
    if not open_named(bot, GiftScreen.SUPER_VALUE_RETURN):
        return False
    if not select_carousel_tab(bot, PAGE, TAB):
        return_home(bot)
        return False
    completed = claim_opened(bot) == DONE
    return_home(bot)
    return completed


TASK = GiftTask(KEY, "Refining Weekly Card", run)
