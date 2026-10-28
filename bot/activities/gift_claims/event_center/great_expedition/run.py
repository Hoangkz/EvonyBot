"""Exact Gift Claims flow for Event Center > Great Expedition.

Every tap is anchored to a supplied image.  The only colour inspection is the
red/available state of the dice costs after the ``Roll x5`` button itself has
been found, so map artwork can never be interpreted as a disabled roll.
"""
from __future__ import annotations

import cv2
import numpy as np

from ...common import (ClaimReport, GiftTask, REFERENCE_WIDTH,
                       close_congratulations, find, find_all,
                       open_event_center_event)
from ...screens import GiftScreen
from ..policy import EventPolicy, run_opened_event

KEY = "gift_great_expedition"
POLICY = EventPolicy("Great Expedition", key=KEY,
                     screen=GiftScreen.GREAT_EXPEDITION)

# The green frames supplied by the user.  Swipes never leave these interiors.
QUEST_CONTENT_REGION = (5, 34, 96, 85)
QUEST_CLAIM_REGION = (65, 34, 96, 85)
CHEST_QUEST_CONTENT_REGION = (5, 25, 96, 88)
# The first green map-chest Claim is centred at y=175 on a 704 px frame.
# Starting at 25% means y=176 and loses that control by one pixel.
CHEST_QUEST_CLAIM_REGION = (65, 22, 96, 88)
MAP_CHEST_LEFT_REGION = (0, 18, 30, 48)
ROLL_REGION = (2, 88, 98, 100)

SETTLE_SECONDS = 1.0
ROLL_SETTLE_SECONDS = 2.0
SCROLL_DURATION_SECONDS = 1.0
CONTENT_SAME_DISTANCE = 10
EDGE_CONFIRMATIONS = 2
MAX_PANEL_SWIPES = 15
MAX_CLAIMS_PER_VIEW = 12
MAX_TAPS_PER_GREEN_CLAIM = 3
MAX_ROLLS_PER_WINDOW = 80
# Median of all 15 supplied Expedition Trial frames.  It scores 0.803..0.973
# on the real chest and at most 0.221 against every reward-grid false match.
TRIAL_CHEST_THRESHOLD = 0.75

MAIN_TITLE = "EventCenter/GreatExpedition/title"
SKIP_ANIMATION = "EventCenter/GreatExpedition/checkbox_skip_animation"
ROLL_ONCE = "EventCenter/GreatExpedition/button_roll_once"
ROLL_X5 = "EventCenter/GreatExpedition/button_roll_x5"
X5_AUTO_ROLLING = "EventCenter/GreatExpedition/status_x5_auto_rolling"
X5_AUTO_ROLLING_SECONDS = 5.0
MAP_CHEST = "EventCenter/GreatExpedition/button_map_chest"
MAP_CHEST_RED_DOT = "EventCenter/GreatExpedition/status_map_chest_red_dot"
MAP_CHEST_RED_DOT_THRESHOLD = 0.85
CHALLENGE_QUEST = "EventCenter/GreatExpedition/button_challenge_quest"
CHALLENGE_QUEST_CLOSE = (
    "EventCenter/GreatExpedition/button_challenge_quest_close")
QUEST_TITLE = "EventCenter/GreatExpedition/title_how_to_earn_scores"
QUEST_CLAIM = "EventCenter/GreatExpedition/button_quest_claim"
QUEST_CLAIMED = "EventCenter/GreatExpedition/status_quest_claimed"
CHEST_QUEST_TAB = "EventCenter/GreatExpedition/tab_chest_quests"
CHEST_QUEST_CLAIM = "EventCenter/GreatExpedition/button_chest_claim"
CHEST_QUEST_CLAIMED = "EventCenter/GreatExpedition/status_chest_claimed"
TRIAL_TAB = "EventCenter/GreatExpedition/tab_expedition_trial"
MAIN_TAB = "EventCenter/GreatExpedition/tab_great_expedition"
TRIAL_MARKER = "EventCenter/GreatExpedition/marker_upgrade"
TRIAL_CHEST = "EventCenter/GreatExpedition/button_trial_chest_median"
TRIAL_CHEST_REGION = (3, 25, 23, 37)
TRIAL_UPGRADE_CONGRATULATIONS = (
    "EventCenter/GreatExpedition/popup_trial_upgrade_congratulations")


def _wait_for(bot, template: str, *, attempts: int = 4,
              threshold: float = 0.72, region=(0, 0, 100, 100),
              delay: float = SETTLE_SECONDS):
    for attempt in range(attempts):
        bot.check()
        pos = find(bot, template, bot.screenshot(), threshold=threshold,
                   region=region)
        if pos is not None:
            return pos
        if attempt + 1 < attempts:
            bot.sleep(delay)
    return None


def _main_open(bot, screen=None) -> bool:
    screen = bot.screenshot() if screen is None else screen
    return find(bot, MAIN_TITLE, screen, threshold=0.72,
                region=(0, 0, 100, 13)) is not None


def _map_open(bot, screen=None) -> bool:
    """The Roll x5 control distinguishes the map from Expedition Trial."""
    screen = bot.screenshot() if screen is None else screen
    return find(bot, ROLL_X5, screen, threshold=0.72,
                region=ROLL_REGION) is not None


def _open_main_board(bot) -> bool:
    """Open the supplied Great Expedition tab before using the Free roll."""
    if _map_open(bot):
        return True
    tab = _wait_for(bot, MAIN_TAB, attempts=4, threshold=0.90,
                    region=(3, 8, 33, 20))
    if tab is None:
        bot.record("Gift Claims: Great Expedition không thấy tab Great "
                   "Expedition; giữ PENDING")
        return False
    bot.record("Gift Claims: Great Expedition mở tab Great Expedition")
    bot.tap(*tab, delay=SETTLE_SECONDS)
    if _wait_for(bot, ROLL_X5, attempts=5, threshold=0.72,
                 region=ROLL_REGION) is not None:
        return True
    bot.record("Gift Claims: Great Expedition chưa thấy bàn Roll sau khi mở "
               "tab; giữ PENDING")
    return False


def _trial_open(bot, screen=None) -> bool:
    screen = bot.screenshot() if screen is None else screen
    return find(bot, TRIAL_MARKER, screen, threshold=0.85,
                region=(45, 35, 80, 48)) is not None


def _open_trial(bot) -> bool:
    """Open Expedition Trial from its stable text-only tab template."""
    if _trial_open(bot):
        return True
    tab = _wait_for(bot, TRIAL_TAB, attempts=4, threshold=0.88,
                    region=(30, 8, 68, 20))
    if tab is None:
        bot.record("Gift Claims: Great Expedition không thấy tab Expedition "
                   "Trial; giữ PENDING")
        return False
    bot.record("Gift Claims: Great Expedition mở tab Expedition Trial")
    bot.tap(*tab, delay=SETTLE_SECONDS)
    if _wait_for(bot, TRIAL_MARKER, attempts=5, threshold=0.85,
                 region=(45, 35, 80, 48)) is not None:
        return True
    bot.record("Gift Claims: Great Expedition chưa xác nhận Expedition Trial; "
               "giữ PENDING")
    return False


def _quest_panel_open(bot, screen=None) -> bool:
    screen = bot.screenshot() if screen is None else screen
    return find(bot, QUEST_TITLE, screen, threshold=0.72,
                region=(0, 10, 100, 28)) is not None


def _close_challenge_quest(bot) -> bool:
    """Tap the modal's red X; Android Back exits the event completely."""
    close = _wait_for(bot, CHALLENGE_QUEST_CLOSE, attempts=4, threshold=0.82,
                      region=(85, 10, 100, 25))
    if close is None:
        bot.record("Gift Claims: Great Expedition không thấy X của Challenge "
                   "Quest; giữ PENDING")
        return False
    bot.record("Gift Claims: Great Expedition đóng Challenge Quest bằng X")
    bot.tap(*close, delay=SETTLE_SECONDS)
    if _wait_for(bot, TRIAL_MARKER, attempts=5, threshold=0.85,
                 region=(45, 35, 80, 48)) is not None:
        return True
    bot.record("Gift Claims: Great Expedition đóng Challenge Quest nhưng chưa "
               "về Expedition Trial; giữ PENDING")
    return False


def _chest_quest_panel_open(bot, screen=None) -> bool:
    screen = bot.screenshot() if screen is None else screen
    # The selected gold Quests tab can score 0.53 against the supplied dark
    # crop while still being the same control; this probe is only used after
    # the exact map chest was tapped, within the small modal header region.
    return find(bot, CHEST_QUEST_TAB, screen, threshold=0.50,
                region=(0, 5, 100, 60)) is not None


def _content_signature(screen, region) -> bytes:
    height, width = screen.shape[:2]
    x0, y0, x1, y1 = region
    patch = screen[int(height * y0 / 100):int(height * y1 / 100),
                   int(width * x0 / 100):int(width * x1 / 100)]
    if patch.size == 0:
        return b""
    gray = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
    tiny = cv2.resize(gray, (33, 16), interpolation=cv2.INTER_AREA)
    return np.packbits(tiny[:, 1:] > tiny[:, :-1]).tobytes()


def _content_moved(before, after, region) -> tuple[bool, int]:
    old = np.frombuffer(_content_signature(before, region), dtype=np.uint8)
    new = np.frombuffer(_content_signature(after, region), dtype=np.uint8)
    if old.shape != new.shape:
        return True, CONTENT_SAME_DISTANCE + 1
    distance = int(np.unpackbits(np.bitwise_xor(old, new)).sum())
    return distance > CONTENT_SAME_DISTANCE, distance


def _button_colour_ratios(screen, center) -> tuple[float, float]:
    """Return saturated-green and low-saturation ratios around one control."""
    scale = screen.shape[1] / REFERENCE_WIDTH
    width, height = max(1, round(78 * scale)), max(1, round(30 * scale))
    left = max(0, center[0] - width // 2)
    top = max(0, center[1] - height // 2)
    crop = screen[top:min(screen.shape[0], top + height),
                  left:min(screen.shape[1], left + width)]
    if crop.size == 0:
        return 0.0, 1.0
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    green = ((hsv[..., 0] >= 35) & (hsv[..., 0] <= 90) &
             (hsv[..., 1] >= 60) & (hsv[..., 2] >= 50))
    gray = ((hsv[..., 1] <= 70) & (hsv[..., 2] >= 50))
    return float(green.mean()), float(gray.mean())


def _active_claims(bot, screen, template: str, region):
    """Find only green Claim controls; the Claim prefix in Claimed is unsafe."""
    candidates = find_all(bot, template, screen, threshold=0.72, region=region)
    return [point for point in candidates
            if ((ratios := _button_colour_ratios(screen, point))[0] >= 0.20
                and ratios[1] < 0.65)]


def _claimed_near(bot, screen, claim, template: str, region) -> bool:
    claimed = find_all(bot, template, screen, threshold=0.78, region=region)
    return any(abs(point[0] - claim[0]) <= 50 and
               abs(point[1] - claim[1]) <= 30 for point in claimed)


def _green_claim_near(bot, screen, claim, template: str, region):
    """Re-find the same green Claim row after a tap, if it is still active."""
    nearby = [point for point in _active_claims(bot, screen, template, region)
              if abs(point[0] - claim[0]) <= 50
              and abs(point[1] - claim[1]) <= 30]
    return min(nearby, key=lambda point: (point[0] - claim[0]) ** 2 +
               (point[1] - claim[1]) ** 2) if nearby else None


def _close_trial_upgrade_congratulations(bot, screen) -> bool:
    """Verify and close Trial's level-up popup caused by a real Claim tap."""
    if find(bot, TRIAL_UPGRADE_CONGRATULATIONS, screen, threshold=0.72,
            region=(0, 20, 100, 50)) is None:
        return False
    bot.record("Gift Claims: Great Expedition Claim -> nâng cấp Trial")
    bot.back(delay=SETTLE_SECONDS)
    return True


def _wait_claimed_near(bot, claim, template: str, region) -> bool:
    """Require the tapped row itself to turn gray before counting a Claim."""
    for attempt in range(5):
        screen = bot.screenshot()
        if _claimed_near(bot, screen, claim, template, region):
            return True
        if attempt < 4:
            bot.sleep(SETTLE_SECONDS)
    return False


def _claim_green_until_resolved(bot, *, label: str, claim, claim_template: str,
                                claimed_template: str, claim_region) -> tuple[int, bool]:
    """Tap one green Claim up to three times, requiring gray/popup proof."""
    target = claim
    for tap_number in range(1, MAX_TAPS_PER_GREEN_CLAIM + 1):
        screen = bot.screenshot()
        current = _green_claim_near(bot, screen, target, claim_template,
                                    claim_region)
        if current is None:
            # Do not count a vanished control without a recognised Claimed
            # state or reward popup: a rerender may otherwise hide a failed tap.
            if _claimed_near(bot, screen, target, claimed_template, claim_region):
                return tap_number - 1, True
            return tap_number - 1, False
        target = current
        bot.record(f"Gift Claims: Great Expedition {label} tap Claim "
                   f"{tap_number}/{MAX_TAPS_PER_GREEN_CLAIM} tại {target}")
        bot.tap(*target, delay=SETTLE_SECONDS)
        after = bot.screenshot()
        if _claimed_near(bot, after, target, claimed_template, claim_region):
            return tap_number, True
        if _close_trial_upgrade_congratulations(bot, after):
            return tap_number, True
        if close_congratulations(bot, attempts=2, region=(0, 20, 100, 62)):
            return tap_number, True
        if _wait_claimed_near(bot, target, claimed_template, claim_region):
            return tap_number, True
        if tap_number < MAX_TAPS_PER_GREEN_CLAIM:
            bot.record("Gift Claims: Great Expedition Claim vẫn xanh; "
                       "tìm lại và bấm thêm")
    return MAX_TAPS_PER_GREEN_CLAIM, False


def _panel_to_top(bot, *, label: str, content_region) -> bool:
    """Prove the panel's top edge before the Claim-free sweep begins."""
    unchanged = 0
    for swipe in range(1, MAX_PANEL_SWIPES + 1):
        bot.check()
        before = bot.screenshot()
        bot.swipe_percent(50, 40, 50, 80, duration=SCROLL_DURATION_SECONDS,
                          delay=SETTLE_SECONDS)
        after = bot.screenshot()
        moved, distance = _content_moved(before, after, content_region)
        unchanged = 0 if moved else unchanged + 1
        bot.record(f"Gift Claims: Great Expedition {label} về đầu vùng xanh "
                   f"{swipe}; Hamming {distance}/{CONTENT_SAME_DISTANCE}, "
                   f"biên {unchanged}/{EDGE_CONFIRMATIONS}")
        if unchanged >= EDGE_CONFIRMATIONS:
            return True
    return False


def _scan_panel(bot, *, label: str, title_open, content_region, claim_region,
                claim_template: str, claimed_template: str) -> tuple[ClaimReport, bool]:
    """Claim a whole green panel and prove a clean, stationary bottom edge."""
    if not title_open(bot):
        bot.record(f"Gift Claims: Great Expedition chưa vào đúng {label}; giữ PENDING")
        return ClaimReport(), False
    if not _panel_to_top(bot, label=label, content_region=content_region):
        bot.record(f"Gift Claims: Great Expedition {label} chưa xác nhận được "
                   "đầu vùng xanh; giữ PENDING")
        return ClaimReport(), False

    attempted = verified = 0
    bottom_checks = 0
    for position in range(1, MAX_PANEL_SWIPES + 2):
        blocked: list[tuple[int, int]] = []
        for _ in range(MAX_CLAIMS_PER_VIEW):
            bot.check()
            screen = bot.screenshot()
            claim = next((point for point in _active_claims(
                bot, screen, claim_template, claim_region)
                if all((point[0] - old[0]) ** 2 +
                       (point[1] - old[1]) ** 2 > 30 ** 2
                       for old in blocked)), None)
            if claim is None:
                break
            blocked.append(claim)
            taps, resolved = _claim_green_until_resolved(
                bot, label=label, claim=claim, claim_template=claim_template,
                claimed_template=claimed_template, claim_region=claim_region)
            attempted += taps
            if resolved:
                verified += 1
                continue
            bot.record("Gift Claims: Great Expedition Claim vẫn xanh sau 3 lần "
                       "bấm; giữ PENDING")
            return ClaimReport(attempted, verified), False

        if position > MAX_PANEL_SWIPES:
            bot.record(f"Gift Claims: Great Expedition {label} vượt giới hạn "
                       "an toàn khi tìm đáy; giữ PENDING")
            return ClaimReport(attempted, verified), False
        before = bot.screenshot()
        bot.swipe_percent(50, 80, 50, 40, duration=SCROLL_DURATION_SECONDS,
                          delay=SETTLE_SECONDS)
        after = bot.screenshot()
        moved, distance = _content_moved(before, after, content_region)
        bottom_checks = 0 if moved else bottom_checks + 1
        bot.record(f"Gift Claims: Great Expedition {label} quét vùng xanh "
                   f"{position}; Hamming {distance}/{CONTENT_SAME_DISTANCE}, "
                   f"đáy {bottom_checks}/{EDGE_CONFIRMATIONS}")
        if bottom_checks < EDGE_CONFIRMATIONS:
            continue
        remaining = _active_claims(bot, after, claim_template, claim_region)
        if remaining:
            bot.record(f"Gift Claims: Great Expedition {label} vẫn còn Claim "
                       "ở đáy; giữ PENDING")
            return ClaimReport(attempted, verified), False
        bot.record(f"Gift Claims: Great Expedition {label} đã lướt hết vùng "
                   "xanh, không còn Claim")
        return ClaimReport(attempted, max(verified, 1)), True
    return ClaimReport(attempted, verified), False


def _find_map_chest(bot, screen=None, *, left_only=False):
    screen = bot.screenshot() if screen is None else screen
    return find(bot, MAP_CHEST, screen, threshold=0.64,
                region=MAP_CHEST_LEFT_REGION if left_only else (0, 8, 100, 88))


def _find_actionable_map_chest(bot, screen=None):
    """Return the left map chest only while its user-supplied red badge shows."""
    screen = bot.screenshot() if screen is None else screen
    chest = _find_map_chest(bot, screen, left_only=True)
    if chest is None:
        return None
    height, width = screen.shape[:2]
    scale = width / REFERENCE_WIDTH
    # Screenshot_20261028-215612: chest centre (56, 225), badge centre
    # (72, 211).  Search a compact region relative to the verified chest, so
    # unrelated top-tab notification dots cannot launch its Quests panel.
    left = chest[0] + round(3 * scale)
    top = chest[1] - round(37 * scale)
    right = chest[0] + round(40 * scale)
    bottom = chest[1] + round(3 * scale)
    region = (max(0, left * 100 / width), max(0, top * 100 / height),
              min(100, right * 100 / width), min(100, bottom * 100 / height))
    badge = find(bot, MAP_CHEST_RED_DOT, screen,
                 threshold=MAP_CHEST_RED_DOT_THRESHOLD, region=region)
    if badge is None:
        bot.log("Gift Claims: Great Expedition rương map không có chấm đỏ; "
                "bỏ qua Quests")
        return None
    bot.log(f"Gift Claims: Great Expedition thấy chấm đỏ rương map tại "
            f"{badge}")
    return chest


def _claim_map_chest(bot, *, label: str) -> tuple[ClaimReport, bool]:
    """Tap the supplied map chest until it disappears from the same region."""
    chest = _find_map_chest(bot, left_only=True)
    if chest is None:
        bot.record(f"Gift Claims: Great Expedition {label} không còn rương "
                   "bên trái; phần rương DONE")
        return ClaimReport(0, 1), True
    attempted = 0
    while chest is not None:
        bot.check()
        attempted += 1
        bot.record(f"Gift Claims: Great Expedition {label} tap rương {chest}")
        bot.tap(*chest, delay=SETTLE_SECONDS)
        close_congratulations(bot, attempts=2)
        chest = _find_map_chest(bot, left_only=True)
    bot.record(f"Gift Claims: Great Expedition {label} rương đã biến mất")
    return ClaimReport(attempted, 1), True


def _claim_trial_chest(bot) -> tuple[ClaimReport, bool]:
    """Finish when the calibrated upper-left Expedition Trial chest is absent."""
    if not _open_trial(bot):
        return ClaimReport(), False
    chest = _wait_for(bot, TRIAL_CHEST, attempts=4,
                      threshold=TRIAL_CHEST_THRESHOLD,
                      region=TRIAL_CHEST_REGION)
    if chest is None:
        bot.record("Gift Claims: Great Expedition Expedition Trial không còn "
                   "rương vàng phía trên trái; DONE")
        return ClaimReport(0, 1), True

    attempted = 0
    while chest is not None:
        bot.check()
        attempted += 1
        bot.record(f"Gift Claims: Great Expedition thấy rương Trial tại {chest}; "
                   f"tap lần {attempted}")
        bot.tap(*chest, delay=SETTLE_SECONDS)
        # A received chest must disappear, or produce the standard
        # Congratulations state; keep retrying this exact chest until it does.
        if close_congratulations(bot, attempts=3):
            bot.record("Gift Claims: Great Expedition rương Trial -> Congratulations")
        chest = _wait_for(bot, TRIAL_CHEST, attempts=4,
                          threshold=TRIAL_CHEST_THRESHOLD,
                          region=TRIAL_CHEST_REGION)
        if chest is not None:
            bot.record("Gift Claims: Great Expedition rương Trial vẫn còn; "
                       "bấm lại, không chuyển PENDING")
    bot.record("Gift Claims: Great Expedition rương Trial đã biến mất")
    return ClaimReport(attempted, 1), True


def _run_case_one(bot, *, force_trial: bool = False) -> tuple[ClaimReport, bool] | None:
    """Claim Challenge Quest, then finish only from the Trial chest state."""
    if force_trial and not _open_trial(bot):
        return ClaimReport(), False
    screen = bot.screenshot()
    if _quest_panel_open(bot, screen):
        opened = True
    else:
        challenge = find(bot, CHALLENGE_QUEST, screen, threshold=0.72,
                         region=(0, 8, 100, 92))
        if challenge is None:
            if force_trial:
                bot.record("Gift Claims: Great Expedition chưa thấy Challenge "
                           "Quest trong Expedition Trial; giữ PENDING")
                return ClaimReport(), False
            return None
        bot.record("Gift Claims: Great Expedition thấy Challenge Quest; tap")
        bot.tap(*challenge, delay=SETTLE_SECONDS)
        opened = _wait_for(bot, QUEST_TITLE, attempts=5, threshold=0.72,
                           region=(0, 10, 100, 28)) is not None
    if not opened:
        bot.record("Gift Claims: Great Expedition chưa thấy How to Earn Scores; "
                   "giữ PENDING")
        return ClaimReport(), False

    report, cleared = _scan_panel(
        bot, label="Challenge Quest", title_open=_quest_panel_open,
        content_region=QUEST_CONTENT_REGION, claim_region=QUEST_CLAIM_REGION,
        claim_template=QUEST_CLAIM, claimed_template=QUEST_CLAIMED)
    if not cleared:
        return report, False
    if not _close_challenge_quest(bot):
        return report, False
    # The map chest only launches its own Quests panel.  The terminal chest
    # belongs to Expedition Trial and is checked after Challenge Quest clears.
    chest, chest_done = _claim_trial_chest(bot)
    return ClaimReport(report.attempted + chest.attempted,
                       report.verified + chest.verified), chest_done


def _roll_cost_red(screen, center: tuple[int, int], *, offset_x: int) -> bool:
    """Read red state of one anchored 1/5 die price, never map artwork."""
    scale = screen.shape[1] / REFERENCE_WIDTH
    # Screenshot_20261028-214134 places the x5 price 18 px right of its text
    # anchor.  The x1 price is centred under its different caption, so its
    # separately measured offset is 2 px.  Both remain derived from the
    # detected x5 template rather than an absolute screen coordinate.
    x = round(center[0] + offset_x * scale)
    y = round(center[1] + 28 * scale)
    half_w, half_h = max(5, round(14 * scale)), max(5, round(11 * scale))
    crop = screen[max(0, y - half_h):min(screen.shape[0], y + half_h),
                  max(0, x - half_w):min(screen.shape[1], x + half_w)]
    if crop.size == 0:
        return True
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    red = (((hsv[..., 0] <= 12) | (hsv[..., 0] >= 170)) &
           (hsv[..., 1] >= 110) & (hsv[..., 2] >= 70))
    # The narrow red ``1`` uses as few as eight saturated pixels on the
    # supplied 393 px live frame; a 3% area threshold would miss it.
    return int(red.sum()) >= max(5, round(crop.shape[0] * crop.shape[1] * .012))


def _roll_controls(bot, screen):
    """Find x5 and derive the adjacent x1 target from that verified control."""
    x5 = find(bot, ROLL_X5, screen, threshold=0.72, region=ROLL_REGION)
    if x5 is None:
        return None
    scale = screen.shape[1] / REFERENCE_WIDTH
    x1 = (round(x5[0] + 183 * scale), x5[1])
    return (x5, x1, _roll_cost_red(screen, x5, offset_x=18),
            _roll_cost_red(screen, x1, offset_x=2))


def _x5_auto_rolling(bot, screen, x5=None) -> bool:
    """Read the supplied Auto-Rolling label only in the left dice control."""
    height, width = screen.shape[:2]
    if x5 is None:
        region = (0, 88, 54, 100)
    else:
        scale = width / REFERENCE_WIDTH
        left = max(0, x5[0] - round(110 * scale))
        right = min(width, x5[0] + round(115 * scale))
        top = max(0, x5[1] - round(25 * scale))
        bottom = min(height, x5[1] + round(25 * scale))
        region = (left * 100 / width, top * 100 / height,
                  right * 100 / width, bottom * 100 / height)
    return find(bot, X5_AUTO_ROLLING, screen, threshold=0.82,
                region=region) is not None


def _skip_animation_enabled(screen, label: tuple[int, int]) -> bool:
    """Read the green tick immediately right of the detected Skip label."""
    scale = screen.shape[1] / REFERENCE_WIDTH
    left = round(label[0] + 37 * scale)
    right = round(label[0] + 62 * scale)
    top = round(label[1] - 12 * scale)
    bottom = round(label[1] + 12 * scale)
    crop = screen[max(0, top):min(screen.shape[0], bottom),
                  max(0, left):min(screen.shape[1], right)]
    if crop.size == 0:
        return False
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    green = ((hsv[..., 0] >= 35) & (hsv[..., 0] <= 90) &
             (hsv[..., 1] >= 100) & (hsv[..., 2] >= 100))
    return int(green.sum()) >= max(6, round(crop.size / 3 / 50))


def _claim_chest_quests(bot) -> tuple[ClaimReport, bool]:
    """Open the map chest's Quests tab and exhaust only green Claims."""
    tab = None
    # A roll-result overlay can swallow the initial chest tap.  Re-find the
    # same supplied chest after the animation instead of interpreting that
    # transient frame as a missing Quests tab or tapping a stale coordinate.
    for attempt in range(4):
        tab = _wait_for(bot, CHEST_QUEST_TAB, attempts=3, threshold=0.50,
                        region=(0, 5, 100, 60))
        if tab is not None:
            break
        chest = _find_map_chest(bot)
        if chest is None:
            if attempt < 3:
                bot.sleep(SETTLE_SECONDS)
            continue
        bot.record("Gift Claims: Great Expedition rương map vẫn hiện sau "
                   "animation; tìm lại đúng ảnh và tap lại")
        bot.tap(*chest, delay=ROLL_SETTLE_SECONDS)
    if tab is None:
        bot.record("Gift Claims: Great Expedition bấm rương nhưng chưa thấy "
                   "tab Quests; giữ PENDING")
        return ClaimReport(), False
    bot.record("Gift Claims: Great Expedition mở Quests của rương")
    bot.tap(*tab, delay=SETTLE_SECONDS)
    report, cleared = _scan_panel(
        bot, label="rương map/Quests", title_open=_chest_quest_panel_open,
        content_region=CHEST_QUEST_CONTENT_REGION,
        claim_region=CHEST_QUEST_CLAIM_REGION,
        claim_template=CHEST_QUEST_CLAIM,
        claimed_template=CHEST_QUEST_CLAIMED)
    if not cleared:
        return report, False
    bot.back(delay=SETTLE_SECONDS)
    if not _main_open(bot):
        bot.record("Gift Claims: Great Expedition Back từ Quests rương chưa về "
                   "trang chính; giữ PENDING")
        return report, False
    return report, True


def _run_case_two(bot) -> tuple[ClaimReport, str]:
    """Spend x5 then x1; a persistent map chest is only one Quests launcher."""
    attempted = verified = 0
    map_chest_handled = False
    roll = 0
    while roll < MAX_ROLLS_PER_WINDOW:
        bot.check()
        screen = bot.screenshot()
        controls = _roll_controls(bot, screen)
        if controls is None:
            if _x5_auto_rolling(bot, screen):
                bot.record("Gift Claims: Great Expedition x5 đang Auto-Rolling; "
                           "đợi 5s rồi quét lại")
                bot.sleep(X5_AUTO_ROLLING_SECONDS)
                continue
            bot.record("Gift Claims: Great Expedition không tìm thấy Roll x5; "
                       "giữ PENDING")
            return ClaimReport(attempted, verified), "pending"
        x5, x1, x5_red, x1_red = controls
        if x5_red and x1_red:
            chest = (None if map_chest_handled else
                     _find_actionable_map_chest(bot, screen))
            if chest is not None:
                bot.record("Gift Claims: Great Expedition x5/x1 đã đỏ nhưng "
                           f"còn rương map tại {chest}")
                bot.tap(*chest, delay=SETTLE_SECONDS)
                report, done = _claim_chest_quests(bot)
                attempted += report.attempted
                verified += report.verified
                if not done:
                    return ClaimReport(attempted, verified), "pending"
                map_chest_handled = True
                continue
            bot.record("Gift Claims: Great Expedition OCR giá x5 và x1 đều đỏ; "
                       "sang Challenge Quest ở Expedition Trial")
            return ClaimReport(attempted, verified), "case_one"

        if not x5_red:
            if _x5_auto_rolling(bot, screen, x5):
                bot.record("Gift Claims: Great Expedition x5 đang Auto-Rolling; "
                           "đợi 5s rồi quét lại")
                bot.sleep(X5_AUTO_ROLLING_SECONDS)
                continue
            target, label, delay = x5, "Roll x5", X5_AUTO_ROLLING_SECONDS
        else:
            target, label, delay = x1, "Roll Once", ROLL_SETTLE_SECONDS
        roll += 1
        bot.record(f"Gift Claims: Great Expedition {label} (lần {roll}); "
                   f"chờ {delay:g}s")
        bot.tap(*target, delay=delay)
        attempted += 1
        # A new roll may reveal a fresh map chest; permit its Quests panel once
        # more even if the old permanent launcher is still visible.
        map_chest_handled = False
        after = bot.screenshot()
        if (_quest_panel_open(bot, after) or find(
                bot, CHALLENGE_QUEST, after, threshold=0.72,
                region=(0, 8, 100, 92)) is not None):
            return ClaimReport(attempted, verified), "case_one"
        chest = _find_actionable_map_chest(bot, after)
        if chest is not None:
            bot.record(f"Gift Claims: Great Expedition thấy rương map tại {chest}")
            bot.tap(*chest, delay=SETTLE_SECONDS)
            report, done = _claim_chest_quests(bot)
            attempted += report.attempted
            verified += report.verified
            if not done:
                return ClaimReport(attempted, verified), "pending"
            map_chest_handled = True
    bot.record("Gift Claims: Great Expedition đạt giới hạn an toàn số lần Roll; "
               "giữ PENDING")
    return ClaimReport(attempted, verified), "pending"


def _enable_skip_and_roll_free(bot) -> ClaimReport:
    """Use the supplied Skip animation and Roll Once Free controls once."""
    attempted = 0
    skip_screen = bot.screenshot()
    skip = find(bot, SKIP_ANIMATION, skip_screen, threshold=0.72,
                region=(45, 75, 95, 95))
    if skip is not None:
        if _skip_animation_enabled(skip_screen, skip):
            bot.record("Gift Claims: Great Expedition Skip animation đã bật")
        else:
            bot.record("Gift Claims: Great Expedition tap Skip animation")
            bot.tap(*skip, delay=SETTLE_SECONDS)
            attempted += 1
    else:
        bot.record("Gift Claims: Great Expedition không thấy Skip animation; "
                   "tiếp tục kiểm tra Roll Once")
    # ``Roll Once`` without Free still scores ~0.75 because both captions
    # share their first line.  Only the supplied two-line Free state is safe
    # to consume before reading the x5/x1 priority branch.
    free = _wait_for(bot, ROLL_ONCE, attempts=3, threshold=0.85,
                     region=ROLL_REGION)
    if free is None:
        bot.record("Gift Claims: Great Expedition không còn Roll Once Free")
        return ClaimReport(attempted, 0)
    bot.record("Gift Claims: Great Expedition tap Roll Once Free, chờ 2s")
    bot.tap(*free, delay=ROLL_SETTLE_SECONDS)
    return ClaimReport(attempted + 1, 0)


def claim_opened(bot) -> tuple[ClaimReport, bool]:
    """Run the specified Quest/x5/x1 loop until its final Quest pass is clean."""
    if not _main_open(bot):
        bot.record("Gift Claims: Great Expedition chưa xác nhận title; giữ PENDING")
        return ClaimReport(), False

    # Screenshot_20261028-215142: enter the main Great Expedition board before
    # Screenshot_20261028-213612 (the one free roll).  The Trial chest is not
    # a terminal gate for the Quest/x5/x1 flow below.
    if not _open_main_board(bot):
        return ClaimReport(), False
    free = _enable_skip_and_roll_free(bot)
    total = ClaimReport(free.attempted, free.verified)
    # A chest can create dice/quests.  Completion therefore needs a final
    # Challenge Quest pass after x5 and x1 are both red and no chest remains.
    # Only attempt the first branch once per state transition: its launcher
    # remains visible after a clean pass, so reopening it immediately would
    # starve the x5/x1 branch forever.
    initial_case_one = True
    for _cycle in range(1, MAX_ROLLS_PER_WINDOW + 1):
        bot.check()
        if initial_case_one:
            first = _run_case_one(bot, force_trial=False)
            if first is not None:
                report, done = first
                total = ClaimReport(total.attempted + report.attempted,
                                    total.verified + report.verified)
                if done:
                    # Case 1 has exhausted its Claim panel and its left-side
                    # chest is absent (or disappeared after a verified tap).
                    # That is an explicit terminal state in the supplied flow.
                    return ClaimReport(total.attempted,
                                       max(total.verified, 1)), True
                return total, False
            initial_case_one = False

        screen = bot.screenshot()
        if not _main_open(bot, screen):
            bot.record("Gift Claims: Great Expedition không ở trang chính sau "
                       "khi Roll; giữ PENDING")
            return total, False
        report, state = _run_case_two(bot)
        total = ClaimReport(total.attempted + report.attempted,
                            total.verified + report.verified)
        if state == "pending":
            return total, False
        # Case 2 is complete: map-chest Quests are clear and x5/x1 are red.
        # Complete Challenge Quest in Expedition Trial, then inspect its chest.
        final = _run_case_one(bot, force_trial=True)
        if final is None:
            bot.record("Gift Claims: Great Expedition đã hết Roll nhưng chưa "
                       "thấy Challenge Quest để quét xác nhận; giữ PENDING")
            return total, False
        final_report, final_done = final
        total = ClaimReport(total.attempted + final_report.attempted,
                            total.verified + final_report.verified)
        if not final_done:
            return total, False
        bot.record("Gift Claims: Great Expedition hết Claim Challenge Quest; "
                   "rương Expedition Trial đã hết; DONE")
        return ClaimReport(total.attempted, max(total.verified, 1)), True
    bot.record("Gift Claims: Great Expedition chưa chốt được trạng thái cuối; "
               "giữ PENDING")
    return total, False


def run(bot):
    return run_opened_event(bot, POLICY)


def run_standalone(bot):
    """Compatibility entry point for a direct Great Expedition test run."""
    if not open_event_center_event(bot, "EventCenter/GreatExpedition/list_row",
                                   MAIN_TITLE):
        return False
    _report, done = claim_opened(bot)
    if done:
        bot.back(delay=SETTLE_SECONDS)
    return done


TASK = GiftTask(KEY, "Great Expedition", run_standalone)
