"""Sweep red tabs and claim safe rewards on Back to Territory."""
import cv2
import numpy as np

from .common import (GiftTask, ClaimReport, claim_fixed_controls, claim_sparkle,
                     close_congratulations, find, find_all, return_home)

KEY = "gift_back_to_territory"
PAGE = "BackToTerritory/title"
DOT = "ValuableEvent/notification_dot"
CONGRATULATIONS = "LoginGifts/congratulations"
TOP = (0, 7, 100, 19)
LOWER = (0, 20, 100, 88)
SPARKLE_REWARDS = (0, 45, 100, 82)
INNER_NAV = (0, 41, 100, 61)
REWARD_LIST = (0, 58, 100, 96)
MAX_SWIPES = 8
FIXED_CLAIMS = (
    "GeneralVault/button_daily_free",
    "SuccessivePurchaseBenefits/button_daily_free_text",
    "SuccessivePurchaseBenefits/button_daily_free",
    "Common/button_claimable", "Common/button_claimable_alt",
    "LimitedOffer/button_free", "SpeedupSprint/button_free",
    "SuperBlazonSale/button_free", "CityGrowthPlan/button_claim_all",
)


def _dots(bot, screen):
    return find_all(bot, DOT, screen, threshold=0.65, region=TOP)


def _tab_signature(screen, dot):
    """Position-independent perceptual fingerprint for one carousel tab."""
    x, _ = dot
    left, right = max(0, x - 45), min(screen.shape[1], x + 20)
    patch = cv2.cvtColor(screen[42:125, left:right], cv2.COLOR_BGR2GRAY)
    tiny = cv2.resize(patch, (17, 8), interpolation=cv2.INTER_AREA)
    return np.packbits(tiny[:, 1:] > tiny[:, :-1]).tobytes()


def _claim_visible_login_rewards(bot, max_taps=12) -> ClaimReport:
    """Claim every visible green Claim button, not just the first instance."""
    attempted = verified = 0
    for _ in range(max_taps):
        bot.check()
        before = bot.screenshot()
        positions = find_all(bot, "BackToTerritory/button_claim", before,
                             threshold=0.82, region=REWARD_LIST)
        if not positions:
            break
        position = positions[0]
        attempted += 1
        bot.record("Gift Claims: tap fixed claim BackToTerritory/button_claim")
        bot.tap(*position, delay=1)
        if close_congratulations(bot):
            verified += 1
            continue
        after = bot.screenshot()
        remaining = find_all(bot, "BackToTerritory/button_claim", after,
                             threshold=0.82, region=REWARD_LIST)
        if not any((x - position[0]) ** 2 + (y - position[1]) ** 2 <= 32 ** 2
                   for x, y in remaining):
            verified += 1
            bot.record("Gift Claims: verified Back to Territory Claim disappeared")
            continue
        bot.log("Gift Claims: Back to Territory Claim vẫn còn; dừng để tránh bấm lặp")
        break
    return ClaimReport(attempted, verified)


def _inner_dots(screen):
    """Detect the smaller red badges on Day and Daily Login/Stamina tabs."""
    height, width = screen.shape[:2]
    x0, y0, x1, y1 = INNER_NAV
    left, top = int(width * x0 / 100), int(height * y0 / 100)
    right, bottom = int(width * x1 / 100), int(height * y1 / 100)
    hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
    area = hsv[top:bottom, left:right]
    red = (cv2.inRange(area, np.array((0, 110, 35)), np.array((12, 255, 235))) |
           cv2.inRange(area, np.array((170, 110, 35)), np.array((179, 255, 235))))
    _, _, stats, centers = cv2.connectedComponentsWithStats(red)
    scale = width / 396
    points = []
    for index in range(1, len(stats)):
        _, _, box_width, box_height, pixels = stats[index]
        if not (6 * scale <= box_width <= 18 * scale
                and 6 * scale <= box_height <= 18 * scale
                and 35 * scale * scale <= pixels <= 180 * scale * scale):
            continue
        cx, cy = centers[index]
        points.append((round(left + cx), round(top + cy)))
    return sorted(points, key=lambda point: (point[1], point[0]))


def _claim_current_inner_tab(bot) -> int:
    """Sweep the vertical reward list for one selected Day/category tab."""
    fixed = claim_fixed_controls(bot, FIXED_CLAIMS, region=LOWER,
                                 initial_wait_attempts=1)
    claimed = fixed.verified
    if fixed.claimed:
        bot.record(f"Gift Claims: Back to Territory nhận {fixed.verified} nút quà cố định")

    # More than one login row can expose an identical green Claim button.
    for step in range(6):
        report = _claim_visible_login_rewards(bot)
        claimed += report.verified
        if step < 5:
            bot.swipe_percent(50, 84, 50, 62, duration=0.45, delay=0.7)

    # Restore the list top before looking for the next red Day/category tab.
    for _ in range(5):
        bot.swipe_percent(50, 62, 50, 84, duration=0.35, delay=0.35)

    # Multiple Day cards can glow at once. A false sparkle is tapped at most
    # once because the loop continues only after Congratulations is verified.
    for _ in range(7):
        bot.check()
        screen = bot.screenshot()
        if find(bot, PAGE, screen, threshold=0.72,
                region=(0, 0, 100, 13)) is None:
            break
        sparkle = claim_sparkle(bot, region=SPARKLE_REWARDS)
        if not sparkle.acted:
            break
        if not sparkle.claimed:
            bot.log("Gift Claims: Back to Territory sparkle không sinh quà; dừng tab này")
            break
        claimed += sparkle.verified
        bot.record("Gift Claims: Back to Territory nhận quà sparkle (Congratulations)")
    if claimed == 0:
        bot.log("Gift Claims: Back to Territory chưa có phần thưởng nhận được")
    return claimed


def claim_opened(bot) -> int:
    """Process the selected page, then every red tab below the top carousel."""
    claimed = _claim_current_inner_tab(bot)
    attempted = []
    for _ in range(14):
        bot.check()
        screen = bot.screenshot()
        dot = next((point for point in _inner_dots(screen)
                    if all(abs(point[0] - old[0]) > 14 or
                           abs(point[1] - old[1]) > 14 for old in attempted)), None)
        if dot is None:
            break
        attempted.append(dot)
        target = (max(0, dot[0] - 25), min(screen.shape[0] - 1, dot[1] + 15))
        bot.record(f"Gift Claims: mở tab đỏ bên dưới Back to Territory {dot}")
        bot.tap(*target, delay=1.2)
        claimed += _claim_current_inner_tab(bot)
    return claimed


def _verify_clean(bot) -> bool:
    for direction in (-1, 1):
        for step in range(MAX_SWIPES + 1):
            bot.check()
            if _dots(bot, bot.screenshot()):
                return False
            if step < MAX_SWIPES:
                if direction < 0:
                    bot.swipe_percent(85, 14, 20, 14, duration=0.5, delay=1)
                else:
                    bot.swipe_percent(20, 14, 85, 14, duration=0.5, delay=1)
    return True


def run_opened(bot, handled=None) -> bool:
    """Open each red top tab, process below it, then recheck the top."""
    if find(bot, PAGE, bot.screenshot(), threshold=0.72,
            region=(0, 0, 100, 13)) is None:
        return False
    attempted = handled if handled is not None else set()
    for direction in (-1, 1):
        for step in range(MAX_SWIPES + 1):
            while True:
                bot.check()
                screen = bot.screenshot()
                candidate = next(((dot, _tab_signature(screen, dot))
                                  for dot in _dots(bot, screen)
                                  if _tab_signature(screen, dot) not in attempted), None)
                if candidate is None:
                    break
                dot, signature = candidate
                bot.tap(max(0, dot[0] - 25), min(screen.shape[0] - 1, dot[1] + 16),
                        delay=1.5)
                claim_opened(bot)
                # If the two-minute slice interrupts claim_opened, this tab is
                # intentionally not remembered and will resume next time.
                attempted.add(signature)
            if step < MAX_SWIPES:
                if direction < 0:
                    bot.swipe_percent(85, 14, 20, 14, duration=0.5, delay=1)
                else:
                    bot.swipe_percent(20, 14, 85, 14, duration=0.5, delay=1)
    clean = _verify_clean(bot)
    bot.record("Gift Claims: Back to Territory - "
               + ("DONE, phần trên hết đỏ" if clean
                  else "chưa DONE, phần trên vẫn còn đỏ"))
    return clean


def run(bot):
    # Entered by the generic zone-2 dispatcher.
    return False


TASK = GiftTask(KEY, "Back to Territory", run)
