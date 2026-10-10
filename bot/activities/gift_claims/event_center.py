"""Scroll Event Center and process every red-dot row safely."""
import cv2
import numpy as np

from .common import (ClaimReport, GiftTask, claim_fixed_controls,
                     claim_sparkle, find, find_all, open_event_center,
                     return_home)
from .screens import GiftScreen, identify

KEY = "gift_event_center_limited"
PAGE = "EventCenter/title"
DOT = "EventCenter/notification_dot"
CONGRATULATIONS = "LoginGifts/congratulations"
MAX_SCROLLS = 8
LOWER = (0, 18, 100, 88)
FIXED_CLAIMS = (
    "Common/button_claim_text",
    "GeneralVault/button_daily_free",
    "SuccessivePurchaseBenefits/button_daily_free_text",
    "SuccessivePurchaseBenefits/button_daily_free",
    "Common/button_claimable", "Common/button_claimable_alt",
    "SpeedupSprint/button_free", "SuperBlazonSale/button_free",
    "LimitedOffer/button_free", "EmpireDepot/button_claimable",
    "LuckyRaffle/button_claimable", "CityGrowthPlan/button_claim_all",
)


def run(bot):
    screen = open_event_center(bot)
    if screen is None:
        return False
    return run_opened(bot)


def _row_dots(bot, screen):
    return [dot for dot in find_all(bot, DOT, screen, threshold=0.65,
                                    region=(10, 25, 25, 98))
            if dot[1] >= 180]


def _row_signature(screen, y):
    top, bottom = max(0, y - 32), min(screen.shape[0], y + 32)
    patch = cv2.cvtColor(screen[top:bottom, :], cv2.COLOR_BGR2GRAY)
    tiny = cv2.resize(patch, (25, 8), interpolation=cv2.INTER_AREA)
    # Difference hash is stable across small animation/brightness changes.
    return np.packbits(tiny[:, 1:] > tiny[:, :-1]).tobytes()


def _close_congratulations(bot):
    screen = bot.screenshot()
    if find(bot, CONGRATULATIONS, screen, threshold=0.78,
            region=(0, 38, 100, 62)) is not None:
        bot.back(delay=0.8)
        return True
    return False


def _back_to_list(bot):
    for _ in range(4):
        screen = bot.screenshot()
        if find(bot, PAGE, screen, threshold=0.72,
                region=(0, 0, 100, 13)) is not None:
            return True
        bot.back(delay=1)
    return False


def _process_opened_event(bot):
    opened = bot.screenshot()
    name = identify(bot, opened)
    if name == GiftScreen.BACCHUS_TAVERN:
        bot.record("Gift Claims: Bacchus Tavern - nhận diện và bỏ qua")
        return ClaimReport()
    report = claim_fixed_controls(bot, FIXED_CLAIMS, max_taps=6,
                                  initial_wait_attempts=2, region=LOWER)
    if report.acted:
        return report
    report = claim_sparkle(bot, region=LOWER)
    if report.claimed:
        bot.record("Gift Claims: Event Center nhận quà sparkle (Congratulations)")
    return report


def _verify_clean(bot) -> bool:
    # Return to the top, then scan the complete vertical list once more.
    for _ in range(MAX_SCROLLS):
        bot.check()
        bot.swipe_percent(50, 32, 50, 86, duration=0.5, delay=0.7)
    for step in range(MAX_SCROLLS + 1):
        bot.check()
        if _row_dots(bot, bot.screenshot()):
            return False
        if step < MAX_SCROLLS:
            bot.swipe_percent(50, 86, 50, 32, duration=0.5, delay=0.7)
    return True


def run_opened(bot, handled=None):
    """Open visible red rows, scroll down, and verify the whole list."""
    screen = bot.screenshot()
    if find(bot, PAGE, screen, threshold=0.72,
            region=(0, 0, 100, 13)) is None:
        return_home(bot)
        return False

    visited = handled if handled is not None else set()
    opened_count = 0
    for scroll in range(MAX_SCROLLS + 1):
        bot.check()
        while True:
            bot.check()
            screen = bot.screenshot()
            candidate = None
            for _, y in _row_dots(bot, screen):
                signature = _row_signature(screen, y)
                if signature not in visited:
                    candidate = y, signature
                    break
            if candidate is None:
                break
            y, signature = candidate
            bot.tap_percent(52, y * 100 / screen.shape[0], delay=2)
            _process_opened_event(bot)
            opened_count += 1
            if not _back_to_list(bot):
                bot.log("Gift Claims: Event Center không quay lại được danh sách")
                return_home(bot)
                return False
            visited.add(signature)
        if scroll < MAX_SCROLLS:
            bot.swipe_percent(50, 86, 50, 32, duration=0.5, delay=1)

    clean = _verify_clean(bot)
    bot.record(f"Gift Claims: Event Center đã mở {opened_count} dòng đỏ; "
               + ("DONE, danh sách hết đỏ" if clean
                  else "chưa DONE, danh sách vẫn còn đỏ"))
    return_home(bot)
    return clean


TASK = GiftTask(KEY, "Event Center Limited", run)
