"""Claim every available reward in Garuda Trial > Garuda's Treasure."""

import cv2

from ...common import ClaimReport, close_congratulations, find, find_all
from ...screens import GiftScreen
from ..policy import EventPolicy, run_opened_event

KEY = "gift_garuda_trial"
FOLDER = "EventCenter/GarudaTrial"

TREASURE = f"{FOLDER}/button_garudas_treasure"
ACTIVE_CLAIM = f"{FOLDER}/button_claim_active"
INACTIVE_CLAIM = f"{FOLDER}/button_claim_inactive"
CLAIMED = f"{FOLDER}/status_claimed"

# Khung xanh người dùng đánh dấu trên ảnh 396x704: x=14..380,
# y=294..669.  Mọi tìm kiếm trạng thái và thao tác lướt danh sách đều nằm
# trong khung này; không chạm ba tab ở phía trên hoặc footer phía dưới.
CONTENT_REGION = (4, 42, 96, 95)
CLAIM_REGION = (68, 42, 96, 95)
TREASURE_REGION = (0, 8, 100, 45)
SCAN_SWIPE = (50, 90, 50, 48)
NO_REWARD_SWIPES_TO_DONE = 2
UI_SETTLE_SECONDS = 1.5
SWIPE_DURATION_SECONDS = 1.0
GREEN_RATIO_MIN = 0.22

POLICY = EventPolicy(
    "Garuda Trial",
    key=KEY,
    screen=GiftScreen.GARUDA_TRIAL,
)


def _green_ratio(screen, center) -> float:
    """Measure the green ribbon around a Claim candidate."""
    scale = screen.shape[1] / 396
    width, height = max(1, round(70 * scale)), max(1, round(28 * scale))
    left = max(0, center[0] - width // 2)
    top = max(0, center[1] - height // 2)
    crop = screen[top:min(screen.shape[0], top + height),
                  left:min(screen.shape[1], left + width)]
    if crop.size == 0:
        return 0.0
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    green = ((hsv[..., 0] >= 35) & (hsv[..., 0] <= 95) &
             (hsv[..., 1] >= 55) & (hsv[..., 2] >= 40))
    return float(green.mean())


def _claim_states(bot, screen):
    """Return active green Claims separately from gray Claim/Claimed rows."""
    # On live 21513 frames, the supplied Claimed crop scores 0.704..0.774
    # against an ordinary gray Claim because the shorter word is shared.
    # The exact gray Claim crop scores 0.932..0.997 there.  Require the strong
    # exact state and let it own any nearby weaker Claimed-shaped candidate.
    inactive = find_all(bot, INACTIVE_CLAIM, screen, threshold=0.88,
                        region=CLAIM_REGION)
    claimed_candidates = find_all(bot, CLAIMED, screen, threshold=0.82,
                                  region=CLAIM_REGION)
    claimed = [
        point for point in claimed_candidates
        if all(abs(point[0] - gray[0]) > 45 or abs(point[1] - gray[1]) > 22
               for gray in inactive)
    ]
    gray = inactive + claimed
    candidates = find_all(bot, ACTIVE_CLAIM, screen, threshold=0.68,
                          region=CLAIM_REGION)
    active = [
        point for point in candidates
        if _green_ratio(screen, point) >= GREEN_RATIO_MIN
        and all(abs(point[0] - old[0]) > 45 or abs(point[1] - old[1]) > 22
                for old in gray)
    ]
    return active, inactive, claimed


def _open_treasure(bot) -> bool:
    """Open the exact Garuda's Treasure entry, allowing UI repaint latency."""
    for attempt in range(3):
        bot.check()
        screen = bot.screenshot()
        entry = find(bot, TREASURE, screen, threshold=0.70,
                     region=TREASURE_REGION)
        if entry is not None:
            bot.record("Gift Claims: Garuda Trial mở Garuda's Treasure")
            bot.tap(*entry, delay=UI_SETTLE_SECONDS)
            return True
        if attempt < 2:
            bot.sleep(UI_SETTLE_SECONDS)
    return False


def claim_opened(bot):
    """Claim green buttons until two consecutive reward-free swipes.

    A recognized green Claim is never converted into PENDING: it is retried
    until its green state disappears (or the worker interrupts at its normal
    deadline, after which the next Event Center window resumes the task).
    """
    if not _open_treasure(bot):
        bot.record("Gift Claims: Garuda Trial không còn thấy Garuda's Treasure "
                   "sau 3 lần kiểm tra; DONE")
        return ClaimReport(0, 1), True

    attempted = verified = 0
    clean_swipes = 0
    while clean_swipes < NO_REWARD_SWIPES_TO_DONE:
        bot.check()
        screen = bot.screenshot()
        active, inactive, claimed = _claim_states(bot, screen)
        if active:
            claim = active[0]
            attempted += 1
            clean_swipes = 0
            bot.record("Gift Claims: Garuda Trial tap Claim xanh tại "
                       f"{claim} (lần {attempted})")
            bot.tap(*claim, delay=UI_SETTLE_SECONDS)
            close_congratulations(bot, attempts=2)
            after = bot.screenshot()
            remaining, _, _ = _claim_states(bot, after)
            if any(abs(point[0] - claim[0]) <= 35 and
                   abs(point[1] - claim[1]) <= 28
                   for point in remaining):
                bot.record("Gift Claims: Garuda Trial Claim xanh vẫn còn; "
                           "tiếp tục bấm, không để PENDING")
            else:
                verified += 1
                bot.record("Gift Claims: Garuda Trial đã nhận xong một Claim")
            continue

        bot.record("Gift Claims: Garuda Trial khung hiện tại không có Claim "
                   f"xanh (Claim xám={len(inactive)}, Claimed={len(claimed)}); "
                   "lướt kiểm tra tiếp")
        bot.swipe_percent(*SCAN_SWIPE, duration=SWIPE_DURATION_SECONDS,
                          delay=UI_SETTLE_SECONDS)
        clean_swipes += 1
        bot.record("Gift Claims: Garuda Trial không nhận thêm quà sau lượt "
                   f"lướt {clean_swipes}/{NO_REWARD_SWIPES_TO_DONE}")

    bot.record("Gift Claims: Garuda Trial đã lướt 2 lượt liên tiếp không còn "
               "Claim xanh; DONE")
    return ClaimReport(attempted, max(verified, 1)), True


def run(bot):
    return run_opened_event(bot, POLICY)
