"""Claim every available row in Refining Weekly Card.

Only the green reward-list frame is searched and scrolled. ``Go`` and
``Continue`` are ordinary row states; neither proves that every claim in the
list has been collected.
"""
import cv2

from ...common import (GiftTask, close_congratulations, find, return_home,
                       select_carousel_tab)
from ...lobby import open_named
from ...screens import GiftScreen
from ...valuable_event.named_flow import ExactFlow, SLOW_SWIPE_DURATION, STEP_DELAY

KEY = "gift_refining_weekly_card"
PAGE = "SuperValueReturn/title"
TAB = "RefiningWeeklyCard/tab"
CLAIM = "RefiningWeeklyCard/button_claim"

# The user-marked green frame in the 396x704 reference screenshot is roughly
# x=10..380, y=474..689. Keep both search and every touch inside that frame.
REWARD_REGION = (2, 67, 98, 98)
SCAN_SWIPE = (50, 93, 50, 73)
RETURN_TOP_SWIPE = (50, 73, 50, 93)
MAX_SCROLLS = 8
MAX_FULL_PASSES = 3
MAX_CLAIMS_PER_VIEW = 6
CLAIM_THRESHOLD = 0.76
EDGE_CONFIRMATIONS = 2

# Metadata for the zone registry. Completion belongs to claim_opened(); Go and
# Continue are deliberately absent from the DONE markers.
FLOW = ExactFlow(claims=(CLAIM,), scroll_claims=True)


def _reward_crop(screen):
    height, width = screen.shape[:2]
    x0, y0, x1, y1 = REWARD_REGION
    return screen[round(height * y0 / 100):round(height * y1 / 100),
                  round(width * x0 / 100):round(width * x1 / 100)]


def _same_list_position(before, after) -> bool:
    """Compare only the green reward frame, ignoring animation above it."""
    old = _reward_crop(before)
    new = _reward_crop(after)
    return (old.shape == new.shape and
            float(cv2.absdiff(old, new).mean()) < 0.5)


def _swipe_to_top(bot) -> None:
    unchanged = 0
    for _ in range(MAX_SCROLLS):
        before = bot.screenshot()
        bot.swipe_percent(*RETURN_TOP_SWIPE,
                          duration=SLOW_SWIPE_DURATION, delay=STEP_DELAY)
        after = bot.screenshot()
        unchanged = unchanged + 1 if _same_list_position(before, after) else 0
        if unchanged >= EDGE_CONFIRMATIONS:
            break


def _claim_current_view(bot) -> tuple[bool, bool]:
    """Return (claimed_something, stuck_claim) for one list position."""
    claimed = False
    for tap_number in range(1, MAX_CLAIMS_PER_VIEW + 1):
        bot.check()
        screen = bot.screenshot()
        pos = find(bot, CLAIM, screen, threshold=CLAIM_THRESHOLD,
                   region=REWARD_REGION)
        if pos is None:
            return claimed, False
        claimed = True
        bot.record("Gift Claims: Refining Weekly Card thấy Claim trong khung "
                   f"xanh; tap ({tap_number}/{MAX_CLAIMS_PER_VIEW})")
        bot.tap(*pos, delay=STEP_DELAY)
        close_congratulations(bot, attempts=2)

    # Never turn an unresponsive Claim into DONE merely because the local tap
    # guard was reached.
    remains = find(bot, CLAIM, bot.screenshot(), threshold=CLAIM_THRESHOLD,
                   region=REWARD_REGION) is not None
    return claimed, remains


def _scan_full_list(bot) -> tuple[bool, bool]:
    """Scan top-to-bottom once; return (saw_claim, stuck_claim)."""
    saw_claim = False
    unchanged = 0
    for position in range(MAX_SCROLLS + 1):
        bot.record("Gift Claims: Refining Weekly Card quét vùng xanh "
                   f"vị trí {position + 1}/{MAX_SCROLLS + 1}")
        claimed, stuck = _claim_current_view(bot)
        saw_claim = saw_claim or claimed
        if stuck:
            return saw_claim, True
        if position >= MAX_SCROLLS:
            break

        before = bot.screenshot()
        bot.swipe_percent(*SCAN_SWIPE,
                          duration=SLOW_SWIPE_DURATION, delay=STEP_DELAY)
        after = bot.screenshot()
        unchanged = unchanged + 1 if _same_list_position(before, after) else 0
        if unchanged >= EDGE_CONFIRMATIONS:
            break
    return saw_claim, False


def claim_opened(bot) -> bool:
    """Claim the list and prove DONE with one complete Claim-free pass."""
    for pass_number in range(1, MAX_FULL_PASSES + 1):
        bot.record("Gift Claims: Refining Weekly Card bắt đầu lượt quét đầy đủ "
                   f"{pass_number}/{MAX_FULL_PASSES}")
        _swipe_to_top(bot)
        saw_claim, stuck = _scan_full_list(bot)
        if stuck:
            bot.record("Gift Claims: Refining Weekly Card vẫn còn Claim không "
                       "bấm được; giữ PENDING")
            return False
        if not saw_claim:
            bot.record("Gift Claims: Refining Weekly Card đã lướt hết khung "
                       "xanh và không còn Claim; DONE")
            return True
        bot.record("Gift Claims: Refining Weekly Card vừa nhận được quà; chụp "
                   "lại và quét toàn bộ lần nữa trước khi kết luận DONE")
        bot.sleep(STEP_DELAY)

    bot.record("Gift Claims: Refining Weekly Card chưa có một lượt quét sạch "
               "Claim; giữ PENDING")
    return False


def run(bot):
    if not open_named(bot, GiftScreen.SUPER_VALUE_RETURN):
        return False
    if not select_carousel_tab(bot, PAGE, TAB):
        return_home(bot)
        return False
    completed = claim_opened(bot)
    return_home(bot)
    return completed


TASK = GiftTask(KEY, "Refining Weekly Card", run)
