"""Scroll Event Center and process every red-dot row safely."""
import cv2
import numpy as np

from . import (blessing_of_pallas, dwarfs_treasure, grace_of_star_trail,
               hypnos_dream, poseidons_day, precious_blazon_exchange,
               revelation_of_horus, sealed_imperial_treasury)
from ..common import (ClaimReport, GiftTask, TEXT_CLAIM_CONTROLS, back_if_close_x,
                     claim_fixed_controls, claim_sparkles,
                     close_congratulations, find, find_all,
                     open_event_center, return_home)
from ..screens import GiftScreen, identify

KEY = "gift_event_center_limited"
PAGE = "EventCenter/title"
DOT = "EventCenter/notification_dot"
CONGRATULATIONS = "LoginGifts/congratulations"
MAX_SCROLLS = 8
LOWER = (0, 18, 100, 88)
SPARKLE_SAFE = (5, 18, 90, 78)
INNER_TOP = (0, 7, 100, 15)
MAX_INNER_SWIPES = 4
CATEGORIES = (
    ("limited", 18),
    ("activities", 50),
    ("competition", 82),
)
CATEGORY_DONE_PREFIX = b"__category_done__\0"
FORCED_EVENT_PREFIX = b"__forced_event__\0"
EVENT_POLICIES = (
    blessing_of_pallas.POLICY,
    precious_blazon_exchange.POLICY,
    poseidons_day.POLICY,
    hypnos_dream.POLICY,
    grace_of_star_trail.POLICY,
    sealed_imperial_treasury.POLICY,
    dwarfs_treasure.POLICY,
    revelation_of_horus.POLICY,
)
POLICY_BY_SCREEN = {policy.screen: policy for policy in EVENT_POLICIES
                    if policy.screen is not None}
SPECIAL_NAVIGATION = {policy.screen: policy.navigation for policy in EVENT_POLICIES
                      if policy.screen is not None and policy.navigation is not None}
SKIPPED_SCREENS = {policy.screen: policy for policy in EVENT_POLICIES
                   if policy.screen is not None and policy.skip_reason is not None}
FIXED_CLAIMS = TEXT_CLAIM_CONTROLS
REWARD_NAVIGATION = grace_of_star_trail.POLICY.reward_navigation
FORCED_LIMITED_ROWS = (
    ("GraceOfStarTrail/list_row", FORCED_EVENT_PREFIX + b"grace_of_star_trail"),
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
    # Event artwork on the right is animated.  The icon/title on the left is
    # the stable row identity and must be the only part persisted across boss
    # resumes and full-list verification passes.
    right = max(1, int(screen.shape[1] * 0.68))
    patch = cv2.cvtColor(screen[top:bottom, :right], cv2.COLOR_BGR2GRAY)
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


def _inner_red_dots(screen):
    """Find small red badges on the opened event's top carousel."""
    height, width = screen.shape[:2]
    x0, y0, x1, y1 = INNER_TOP
    left, top = int(width * x0 / 100), int(height * y0 / 100)
    right, bottom = int(width * x1 / 100), int(height * y1 / 100)
    hsv = cv2.cvtColor(screen[top:bottom, left:right], cv2.COLOR_BGR2HSV)
    red = (cv2.inRange(hsv, np.array((0, 110, 35)), np.array((12, 255, 235))) |
           cv2.inRange(hsv, np.array((170, 110, 35)), np.array((179, 255, 235))))
    _, _, stats, centers = cv2.connectedComponentsWithStats(red)
    scale = width / 396
    points = []
    for index in range(1, len(stats)):
        _, _, box_width, box_height, pixels = stats[index]
        if not (8 * scale <= box_width <= 28 * scale
                and 8 * scale <= box_height <= 28 * scale
                and 60 * scale * scale <= pixels <= 450 * scale * scale
                and 0.55 <= box_width / box_height <= 1.8):
            continue
        cx, cy = centers[index]
        points.append((round(left + cx), round(top + cy)))
    return sorted(points, key=lambda point: point[0])


def _inner_tab_signature(screen, dot):
    x, _ = dot
    left, right = max(0, x - 45), min(screen.shape[1], x + 20)
    patch = cv2.cvtColor(screen[42:125, left:right], cv2.COLOR_BGR2GRAY)
    tiny = cv2.resize(patch, (17, 8), interpolation=cv2.INTER_AREA)
    return np.packbits(tiny[:, 1:] > tiny[:, :-1]).tobytes()


def _signature_seen(signature: bytes, attempted: set[bytes], max_distance=18) -> bool:
    """Match a carousel tab despite small animation/selection-state changes."""
    current = np.frombuffer(signature, dtype=np.uint8)
    for old_signature in attempted:
        old = np.frombuffer(old_signature, dtype=np.uint8)
        if old.shape != current.shape:
            continue
        distance = int(np.unpackbits(np.bitwise_xor(current, old)).sum())
        if distance <= max_distance:
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


def _tap_special_navigation(bot, *, attempts=4) -> ClaimReport:
    """Tap exact Event Center reward launchers, bounded to four checks.

    Rewards is shared by Precious Blazon Exchange and Hypnos' Dream. Dwarf's
    Treasure uses a full chest-plus-label crop so its centre is inside the
    clickable icon rather than on the label below it.
    """
    attempted_count = 0
    for attempt in range(attempts):
        bot.check()
        screen = bot.screenshot()
        screen_name = identify(bot, screen)
        control = SPECIAL_NAVIGATION.get(screen_name)
        if control is not None:
            label, template = control
            pos = find(bot, template, screen, threshold=0.68, region=LOWER)
            if pos is not None:
                bot.record(f"Gift Claims: Event Center tap {label} ({template})")
                bot.tap(*pos, delay=1)
                attempted_count += 1
                if close_congratulations(bot):
                    return ClaimReport(attempted_count, 1)
                after = bot.screenshot()
                after_name = identify(bot, after)
                # A direct Rewards/Daily Free claim can remove its red control
                # without showing the common Congratulations popup.
                if find(bot, template, after, threshold=0.68,
                        region=LOWER) is None:
                    bot.record(f"Gift Claims: verified {label} disappeared")
                    return ClaimReport(attempted_count, 1)
                # Navigation opened another view; let the ordinary Claim and
                # sparkle stages process that child instead of clicking again.
                if after_name != screen_name:
                    return ClaimReport(attempted_count, 0)
        if attempt + 1 < attempts:
            bot.sleep(0.6)
    if attempted_count:
        bot.log(f"Gift Claims: Rewards/Daily Free vẫn còn sau {attempted_count} lần; "
                "đánh dấu bỏ qua mục")
    else:
        bot.log("Gift Claims: không thấy Rewards/Daily Free chính xác sau 4 lần; bỏ qua")
    return ClaimReport(attempted_count, 0)


def _tap_reward_navigation(bot) -> ClaimReport:
    """Open Star Trail Gift, then tap the separate coin Claim control."""
    screen = bot.screenshot()
    for template in REWARD_NAVIGATION:
        pos = find(bot, template, screen, threshold=0.68, region=LOWER)
        if pos is None:
            continue
        bot.record(f"Gift Claims: Event Center tap Star Trail Gift ({template})")
        bot.tap(*pos, delay=1)
        if close_congratulations(bot):
            bot.record("Gift Claims: verified Star Trail Gift Congratulations")
            return ClaimReport(1, 1)
        attempted = 1
        for attempt in range(4):
            claim_screen = bot.screenshot()
            claim = find(bot, "GraceOfStarTrail/button_claim", claim_screen,
                         threshold=0.70, region=LOWER)
            if claim is not None:
                attempted += 1
                bot.record("Gift Claims: tap Grace of Star Trail coin Claim")
                bot.tap(*claim, delay=1)
                if close_congratulations(bot):
                    bot.record("Gift Claims: verified Star Trail coin Congratulations")
                    return ClaimReport(attempted, 1)
                after = bot.screenshot()
                if find(bot, "GraceOfStarTrail/button_claim", after,
                        threshold=0.70, region=LOWER) is None:
                    bot.record("Gift Claims: verified Star Trail coin Claim disappeared")
                    return ClaimReport(attempted, 1)
            if attempt < 3:
                bot.sleep(0.5)
        bot.log("Gift Claims: đã mở Star Trail Gift nhưng chưa thấy/nhận được coin Claim")
        return ClaimReport(attempted, 0)
    return ClaimReport()


def _process_current_event_content(bot):
    """Process one selected inner tab; return (claims, panel_was_closed)."""
    special = _tap_special_navigation(bot, attempts=4)
    reward_navigation = _tap_reward_navigation(bot)
    fixed = claim_fixed_controls(bot, FIXED_CLAIMS, max_taps=16,
                                 initial_wait_attempts=2, region=LOWER)
    if back_if_close_x(bot):
        return ClaimReport(special.attempted + reward_navigation.attempted +
                           fixed.attempted,
                           special.verified + reward_navigation.verified +
                           fixed.verified), True
    sparkle = claim_sparkles(bot, region=SPARKLE_SAFE, attempts=4)
    if sparkle.claimed:
        bot.record("Gift Claims: Event Center nhận quà sparkle (Congratulations)")
    return (ClaimReport(special.attempted + reward_navigation.attempted +
                        fixed.attempted + sparkle.attempted,
                        special.verified + reward_navigation.verified +
                        fixed.verified + sparkle.verified), False)


def _process_opened_event(bot):
    opened = bot.screenshot()
    name = identify(bot, opened)
    skipped = SKIPPED_SCREENS.get(name)
    if skipped is not None:
        bot.record(f"Gift Claims: {skipped.label} - {skipped.skip_reason}")
        return ClaimReport()
    if name in (GiftScreen.BACCHUS_TAVERN, GiftScreen.FOLLOW_US):
        bot.record(f"Gift Claims: {name.value} - nhận diện và bỏ qua")
        return ClaimReport()

    # Grace may keep its claim badge only on the nested Star Trail Gift icon,
    # without a reliable red dot on the Event Center list row. Open it once
    # per task and use the exact current icon crop before any generic red scan.
    if name == GiftScreen.GRACE_OF_STAR_TRAIL:
        report, _ = _process_current_event_content(bot)
        return report

    # Most Event Center rows have no nested carousel badge. Scanning the full
    # horizontal strip for every such row can consume the whole 120-second
    # window. A visible badge is the signal that this event needs the nested
    # sweep; otherwise process only its current reward content.
    if not _inner_red_dots(opened):
        report, _ = _process_current_event_content(bot)
        return report

    attempted = set()
    handled_positions = []
    total = ClaimReport()
    saw_red = False
    for direction in (-1, 1):
        for step in range(MAX_INNER_SWIPES + 1):
            while True:
                bot.check()
                screen = bot.screenshot()
                candidate = None
                for dot in _inner_red_dots(screen):
                    signature = _inner_tab_signature(screen, dot)
                    if _signature_seen(signature, attempted):
                        continue
                    if any(abs(dot[0] - old[0]) <= 14 and
                           abs(dot[1] - old[1]) <= 14
                           for old in handled_positions):
                        continue
                    candidate = dot, signature
                    break
                if candidate is None:
                    break
                saw_red = True
                dot, signature = candidate
                bot.record(f"Gift Claims: Event Center mở tab đỏ bên trong {dot}")
                bot.tap(max(0, dot[0] - 25), min(screen.shape[0] - 1, dot[1] + 15),
                        delay=1.2)
                report, closed = _process_current_event_content(bot)
                total = ClaimReport(total.attempted + report.attempted,
                                    total.verified + report.verified)
                attempted.add(signature)
                handled_positions.append(dot)
                if closed:
                    return total
                # Selecting a tab changes its artwork (and animated events can
                # change it again), so its original dHash alone is not a stable
                # "already handled" key.  Also remember the selected state at
                # the same badge position.  This prevents a persistent badge
                # from being opened again after its four bounded sparkle checks.
                after = bot.screenshot()
                for current_dot in _inner_red_dots(after):
                    if (abs(current_dot[0] - dot[0]) <= 14 and
                            abs(current_dot[1] - dot[1]) <= 14):
                        attempted.add(_inner_tab_signature(after, current_dot))
                        break
            if step < MAX_INNER_SWIPES:
                before_swipe = bot.screenshot()
                before_dots = _inner_red_dots(before_swipe)
                if direction < 0:
                    bot.swipe_percent(85, 11, 20, 11, duration=0.45, delay=0.7)
                else:
                    bot.swipe_percent(20, 11, 85, 11, duration=0.45, delay=0.7)
                # At either carousel boundary a swipe can be a no-op.  Without
                # this guard the same persistent badge is revisited once per
                # step merely because its animated pixels changed slightly.
                after_swipe = bot.screenshot()
                if _inner_red_dots(after_swipe) == before_dots:
                    bot.log("Gift Claims: carousel Event Center không di chuyển; "
                            "dừng quét hướng hiện tại")
                    break
                # Keep handled positions for the entire opened event.  A red
                # badge can wobble a few pixels or survive a partial carousel
                # swipe; after its four bounded checks it must not be reopened.

    if not saw_red:
        report, _ = _process_current_event_content(bot)
        total = ClaimReport(total.attempted + report.attempted,
                            total.verified + report.verified)
    return total


def _category_signature(category: str, signature: bytes) -> bytes:
    return category.encode("ascii") + b"\0" + signature


def _category_done_key(category: str) -> bytes:
    return CATEGORY_DONE_PREFIX + category.encode("ascii")


def _category_seen(category: str, signature: bytes, visited, max_distance=28) -> bool:
    prefix = category.encode("ascii") + b"\0"
    current = np.frombuffer(signature, dtype=np.uint8)
    for item in visited:
        if not item.startswith(prefix):
            continue
        old = np.frombuffer(item[len(prefix):], dtype=np.uint8)
        if old.shape != current.shape:
            continue
        distance = int(np.unpackbits(np.bitwise_xor(current, old)).sum())
        if distance <= max_distance:
            return True
    return False


def _activities_facebook_red(bot, screen) -> bool:
    """Activities is complete when its Facebook row still owns a red badge."""
    activity_icons = find_all(bot, "EventCenter/facebook_activity", screen,
                              threshold=0.72, region=(0, 13, 35, 35))
    activity_tab_red = any(abs(x - screen.shape[1] * 0.64) <=
                           24 * screen.shape[1] / 396
                           for x, _ in _inner_red_dots(screen))
    if activity_icons and activity_tab_red:
        return True

    # Fallback for layouts where the Facebook row is lower and its own badge
    # is fully visible rather than partly covered by the category header.
    icons = find_all(bot, "FollowUs/facebook_icon", screen, threshold=0.65,
                     region=(0, 15, 35, 98))
    if not icons:
        return False
    dots = find_all(bot, DOT, screen, threshold=0.62, region=(0, 15, 35, 98))
    scale = screen.shape[1] / 396
    return any(abs(dot[0] - icon[0]) <= 55 * scale and
               abs(dot[1] - icon[1]) <= 55 * scale
               for icon in icons for dot in dots)


def _select_category(bot, name: str, x_percent: int) -> bool:
    bot.record(f"Gift Claims: Event Center chọn nhóm {name}")
    bot.tap_percent(x_percent, 11, delay=1.2)
    for _ in range(4):
        screen = bot.screenshot()
        if find(bot, PAGE, screen, threshold=0.72,
                region=(0, 0, 100, 13)) is not None:
            return True
        bot.sleep(0.6)
    return False


def _list_signature(screen) -> bytes:
    """Stable list fingerprint excluding animated artwork on the right."""
    right = max(1, int(screen.shape[1] * 0.68))
    patch = cv2.cvtColor(screen[95:, :right], cv2.COLOR_BGR2GRAY)
    tiny = cv2.resize(patch, (32, 18), interpolation=cv2.INTER_AREA)
    return np.packbits(tiny[:, 1:] > tiny[:, :-1]).tobytes()


def _same_list_position(before: bytes, after: bytes, max_distance=18) -> bool:
    old = np.frombuffer(before, dtype=np.uint8)
    new = np.frombuffer(after, dtype=np.uint8)
    return old.shape == new.shape and int(
        np.unpackbits(np.bitwise_xor(old, new)).sum()) <= max_distance


def _verify_clean(bot, category: str, ignored=()) -> bool:
    # Return to the top, then scan the complete vertical list once more.
    for _ in range(MAX_SCROLLS):
        bot.check()
        before = _list_signature(bot.screenshot())
        bot.swipe_percent(50, 32, 50, 86, duration=0.5, delay=0.7)
        if _same_list_position(before, _list_signature(bot.screenshot())):
            break
    for step in range(MAX_SCROLLS + 1):
        bot.check()
        screen = bot.screenshot()
        if category == "activities" and _activities_facebook_red(bot, screen):
            bot.record("Gift Claims: Activities có Facebook kèm dấu đỏ; coi nhóm đã DONE")
            return True
        if any(not _category_seen(category, _row_signature(screen, y), ignored)
               for _, y in _row_dots(bot, screen)):
            return False
        if step < MAX_SCROLLS:
            before = _list_signature(screen)
            bot.swipe_percent(50, 86, 50, 32, duration=0.5, delay=0.7)
            if _same_list_position(before, _list_signature(bot.screenshot())):
                break
    return True


def _scan_category(bot, category: str, visited: set[bytes]) -> bool:
    """Process all claimable red rows in one Event Center category."""
    opened_count = 0
    for scroll in range(MAX_SCROLLS + 1):
        bot.check()
        while True:
            bot.check()
            screen = bot.screenshot()
            if category == "activities" and _activities_facebook_red(bot, screen):
                bot.record("Gift Claims: Activities thấy Facebook có dấu đỏ; "
                           "không mở Facebook và đánh dấu nhóm DONE")
                return True
            candidate = None
            if category == "limited":
                for template, key in FORCED_LIMITED_ROWS:
                    if key in visited:
                        continue
                    row = find(bot, template, screen, threshold=0.76,
                               region=(10, 15, 75, 98))
                    if isinstance(row, tuple) and len(row) == 2:
                        candidate = row[1], key
                        bot.record("Gift Claims: Event Center mở Grace of Star Trail "
                                   "để kiểm tra Star Trail Gift dù dòng ngoài không đỏ")
                        break
            for _, y in _row_dots(bot, screen):
                if candidate is not None:
                    break
                signature = _row_signature(screen, y)
                key = _category_signature(category, signature)
                if not _category_seen(category, signature, visited):
                    candidate = y, key
                    break
            if candidate is None:
                break
            y, key = candidate
            bot.tap_percent(52, y * 100 / screen.shape[0], delay=2)
            _process_opened_event(bot)
            opened_count += 1
            # The child row is complete at this point.  Checkpoint it before
            # the potentially slow Back/list reload so a two-minute timeout
            # there does not make the next boss-resume repeat this reward row.
            visited.add(key)
            if not _back_to_list(bot):
                bot.log(f"Gift Claims: Event Center/{category} không quay lại được danh sách")
                return False
        if scroll < MAX_SCROLLS:
            before = _list_signature(bot.screenshot())
            bot.swipe_percent(50, 86, 50, 32, duration=0.5, delay=1)
            if _same_list_position(before, _list_signature(bot.screenshot())):
                bot.log(f"Gift Claims: Event Center/{category} đã tới cuối danh sách")
                break

    clean = _verify_clean(bot, category, visited)
    has_checkpoint = any(item.startswith(category.encode("ascii") + b"\0")
                         for item in visited)
    if not clean and has_checkpoint:
        # The authoritative sweep already opened every visible red row.  Some
        # event badges remain red for purchases, locked rewards, or rotating
        # notices even after four failed claim/sparkle checks.  They are now
        # explicit bounded skips and must not block the combined DB task.
        bot.record(f"Gift Claims: Event Center/{category} còn badge đỏ dai dẳng "
                   "sau khi đã quét; đánh dấu skip/done")
        clean = True
    bot.record(f"Gift Claims: Event Center/{category} đã mở {opened_count} dòng đỏ; "
               + ("DONE, danh sách hết đỏ" if clean
                  else "chưa DONE, danh sách vẫn còn đỏ"))
    return clean


def run_opened(bot, handled=None):
    """Prioritize Limited, Activities, then Competition in Event Center."""
    screen = bot.screenshot()
    if find(bot, PAGE, screen, threshold=0.72,
            region=(0, 0, 100, 13)) is None:
        return_home(bot)
        return False

    visited = handled if handled is not None else set()
    all_clean = True
    for category, x_percent in CATEGORIES:
        bot.check()
        if _category_done_key(category) in visited:
            bot.record(f"Gift Claims: Event Center/{category} đã DONE ở lát trước; bỏ qua")
            continue
        if category == "activities":
            visited.add(_category_done_key(category))
            bot.record("Gift Claims: Event Center/activities tạm thời bỏ qua; đánh dấu DONE")
            continue
        if not _select_category(bot, category, x_percent):
            bot.log(f"Gift Claims: không mở được nhóm Event Center/{category}")
            all_clean = False
            continue
        if _scan_category(bot, category, visited):
            # Persist category completion in the same in-memory checkpoint set
            # as its rows, so a 120-second boss yield cannot force a full list
            # verification of Limited/Activities again.
            visited.add(_category_done_key(category))
        else:
            all_clean = False

    return_home(bot)
    return all_clean


TASK = GiftTask(KEY, "Event Center Limited", run)
