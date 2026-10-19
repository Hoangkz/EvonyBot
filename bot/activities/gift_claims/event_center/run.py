"""Scroll Event Center and process every red-dot row safely."""
import cv2
import numpy as np

from . import (blessing_of_pallas, dragon_battle, dwarfs_treasure,
               giants_wisdom_temple, grace_of_star_trail, hypnos_dream,
               poseidons_day, precious_blazon_exchange, revelation_of_horus,
               sealed_imperial_treasury, wishful_windmill_festival)
from ..common import (ClaimReport, GiftTask, TEXT_CLAIM_CONTROLS, back_if_close_x,
                     claim_fixed_controls, claim_sparkles,
                     close_congratulations, find, find_all,
                     mark_task_done, open_event_center, return_home)
from ..screens import GiftScreen, identify

KEY = "gift_event_center_limited"
PAGE = "EventCenter/title"
DOT = "EventCenter/notification_dot"
CONGRATULATIONS = "LoginGifts/congratulations"
MAX_SCROLLS = 8
# Text controls such as Blessing of Pallas' green Claim sit as low as 91% of
# the 396x704 frame.  Fixed text templates are safe to search down to the
# bottom because they only match Claim/Free/Daily Free words.  Sparkle remains
# restricted separately so decorative/purchase animation near the footer can
# never become a blind tap.
LOWER = (0, 18, 100, 98)
# Grace of Star Trail keeps its Gift launcher in the top-right carousel, well
# above the ordinary body controls covered by LOWER.
REWARD_NAV_REGION = (0, 7, 100, 30)
SPARKLE_SAFE = (5, 18, 90, 78)
INNER_TOP = (0, 7, 100, 15)
MAX_INNER_SWIPES = 4
MAX_EVENT_VERIFY_PASSES = 2
CATEGORIES = (
    ("limited", 18),
)
CATEGORY_DONE_PREFIX = b"__category_done__\0"
FORCED_EVENT_PREFIX = b"__forced_event__\0"
POLICY_SEEN_PREFIX = b"__policy_seen__\0"
EVENT_POLICIES = (
    blessing_of_pallas.POLICY,
    dragon_battle.POLICY,
    precious_blazon_exchange.POLICY,
    poseidons_day.POLICY,
    hypnos_dream.POLICY,
    grace_of_star_trail.POLICY,
    sealed_imperial_treasury.POLICY,
    dwarfs_treasure.POLICY,
    giants_wisdom_temple.POLICY,
    wishful_windmill_festival.POLICY,
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
    ("BlessingOfPallas/list_row", FORCED_EVENT_PREFIX + b"blessing_of_pallas",
     None, "Blessing of Pallas", blessing_of_pallas.POLICY.key),
    ("DragonBattle/list_row", FORCED_EVENT_PREFIX + b"dragon_battle",
     GiftScreen.DRAGON_BATTLE, "Dragon Battle", dragon_battle.POLICY.key),
    ("PreciousBlazonExchange/list_row",
     FORCED_EVENT_PREFIX + b"precious_blazon_exchange",
     GiftScreen.PRECIOUS_BLAZON_EXCHANGE, "Precious Blazon Exchange",
     precious_blazon_exchange.POLICY.key),
    ("GraceOfStarTrail/list_row", FORCED_EVENT_PREFIX + b"grace_of_star_trail",
     GiftScreen.GRACE_OF_STAR_TRAIL, "Grace of Star Trail",
     grace_of_star_trail.POLICY.key),
    # Dwarf's Treasure may lose its outer Event Center badge while the
    # Daily Free chest inside is still claimable.  Check the named row once
    # per daily run instead of using the outer badge as its source of truth.
    ("DwarfsTreasure/list_row", FORCED_EVENT_PREFIX + b"dwarfs_treasure",
     GiftScreen.DWARFS_TREASURE, "Dwarf's Treasure", dwarfs_treasure.POLICY.key),
    ("GiantsWisdomTemple/list_row", FORCED_EVENT_PREFIX + b"giants_wisdom_temple",
     GiftScreen.GIANTS_WISDOM_TEMPLE, "Giant's Wisdom Temple",
     giants_wisdom_temple.POLICY.key),
    ("WishfulWindmillFestival/list_row",
     FORCED_EVENT_PREFIX + b"wishful_windmill_festival",
     GiftScreen.WISHFUL_WINDMILL_FESTIVAL, "Wishful Windmill Festival",
     wishful_windmill_festival.POLICY.key),
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


def _close_exact_congratulations(bot) -> bool:
    """Close either supplied Event Center congratulations marker."""
    if close_congratulations(bot, attempts=1):
        return True
    screen = bot.screenshot()
    if find(bot, "PreciousBlazonExchange/popup_congratulations", screen,
            threshold=0.72, region=(0, 35, 100, 65)) is None:
        return False
    bot.back(delay=0.8)
    return True


def _wait_for(bot, template: str, *, attempts=4, threshold=0.68,
              region=(0, 0, 100, 100)):
    for attempt in range(attempts):
        screen = bot.screenshot()
        pos = find(bot, template, screen, threshold=threshold, region=region)
        if pos is not None:
            return pos
        if attempt + 1 < attempts:
            bot.sleep(0.5)
    return None


def _ensure_skip_animation(bot, folder: str) -> bool:
    """Enable Skip animation and require the supplied green checked state."""
    region = (35, 35, 100, 92)
    checked = f"{folder}/checkbox_skip_animation_checked"
    unchecked = f"{folder}/checkbox_skip_animation_unchecked"
    if _wait_for(bot, checked, attempts=2, region=region) is not None:
        return True
    # Background art differs between events, so the full supplied crop can
    # score poorly even though the green check itself is unchanged. Detect
    # that check by colour/shape inside the named Skip-animation strip.
    screen = bot.screenshot()
    height, width = screen.shape[:2]
    area = screen[int(height * .35):int(height * .92),
                  int(width * .35):width]
    hsv = cv2.cvtColor(area, cv2.COLOR_BGR2HSV)
    green = cv2.inRange(hsv, np.array((35, 100, 80)),
                        np.array((95, 255, 255)))
    _, _, stats, _ = cv2.connectedComponentsWithStats(green)
    scale = width / 396
    if any(6 * scale <= w <= 28 * scale and 6 * scale <= h <= 28 * scale
           and pixels >= 18 * scale * scale
           for _, _, w, h, pixels in stats[1:]):
        bot.record(f"Gift Claims: {folder} đã có dấu tích xanh Skip animation")
        return True
    pos = _wait_for(bot, unchecked, attempts=3, region=region)
    if pos is None:
        bot.log(f"Gift Claims: {folder} không nhận diện được Skip animation")
        return False
    bot.record(f"Gift Claims: {folder} bật Skip animation")
    bot.tap(*pos, delay=0.8)
    return _wait_for(bot, checked, attempts=3, region=region) is not None


def _handle_precious(bot):
    attempted = 0
    for attempt in range(4):
        screen = bot.screenshot()
        if find(bot, "PreciousBlazonExchange/status_rewards_claimed", screen,
                threshold=0.68, region=(0, 12, 40, 48)) is not None:
            return ClaimReport(attempted, 1), True
        rewards = find(bot, "PreciousBlazonExchange/button_rewards_text", screen,
                       threshold=0.62, region=(0, 12, 45, 48))
        if rewards is not None:
            attempted += 1
            bot.record("Gift Claims: Precious Blazon Exchange tap exact Rewards")
            bot.tap(*rewards, delay=0.8)
            if _close_exact_congratulations(bot):
                return ClaimReport(attempted, 1), True
        if attempt + 1 < 4:
            bot.sleep(0.5)
    done = _wait_for(bot, "PreciousBlazonExchange/status_rewards_claimed", attempts=2,
                     threshold=0.68, region=(0, 12, 40, 48)) is not None
    return ClaimReport(attempted, int(done)), done


def _handle_hypnos(bot):
    attempted = 0
    # The page is already identified by its fixed title.  Four misses in the
    # exact upper-right reward area means its chest/Rewards control is gone.
    for attempt in range(4):
        screen = bot.screenshot()
        rewards = find(bot, "HypnosDream/button_rewards_text", screen,
                       threshold=0.62, region=(65, 12, 100, 38))
        if rewards is None:
            if attempt + 1 < 4:
                bot.sleep(0.4)
                continue
            bot.record("Gift Claims: Hypnos' Dream không còn Rewards ở góc phải")
            return ClaimReport(attempted, 1), True
        attempted += 1
        bot.record("Gift Claims: Hypnos' Dream tap exact Rewards")
        bot.tap(*rewards, delay=0.8)
        if _close_exact_congratulations(bot):
            return ClaimReport(attempted, 1), True
    return ClaimReport(attempted, 0), False


def _handle_poseidon(bot):
    attempted = 0
    for attempt in range(5):
        screen = bot.screenshot()
        if find(bot, "PoseidonsDay/status_daily_free_claimed", screen, threshold=0.68,
                region=(65, 12, 100, 38)) is not None:
            return ClaimReport(attempted, 1), True
        daily = find(bot, "PoseidonsDay/button_daily_free_text", screen,
                     threshold=0.62, region=(65, 12, 100, 38))
        if daily is not None:
            attempted += 1
            bot.record("Gift Claims: Poseidon's Day tap exact Daily Free")
            bot.tap(*daily, delay=0.8)
            if _close_exact_congratulations(bot):
                return ClaimReport(attempted, 1), True
        elif attempt == 0:
            package = find(bot, "PoseidonsDay/tab_packages_red_dot", screen,
                           threshold=0.68, region=(45, 5, 90, 18))
            if package is not None:
                attempted += 1
                bot.record("Gift Claims: Poseidon's Day mở tab Packages có chấm đỏ")
                bot.tap(*package, delay=0.8)
        if attempt + 1 < 5:
            bot.sleep(0.5)
    done = _wait_for(bot, "PoseidonsDay/status_daily_free_claimed", attempts=2, threshold=0.68,
                     region=(65, 12, 100, 38)) is not None
    return ClaimReport(attempted, int(done)), done


def _handle_grace(bot):
    report = _tap_reward_navigation(bot)
    return report, report.verified > 0


def _handle_giant(bot):
    if not _ensure_skip_animation(bot, "GiantsWisdomTemple"):
        return ClaimReport(), False
    target = _wait_for(bot, "GiantsWisdomTemple/button_free_wisdom_tile", attempts=4,
                       threshold=0.70, region=(0, 30, 100, 92))
    if target is None:
        return ClaimReport(), False
    bot.record("Gift Claims: Giant's Wisdom Temple tap exact free tile")
    bot.tap(*target, delay=0.8)
    if _close_exact_congratulations(bot):
        return ClaimReport(1, 1), True
    done = _wait_for(bot, "GiantsWisdomTemple/message_not_enough_items", attempts=4,
                     threshold=0.70, region=(0, 15, 100, 45)) is not None
    return ClaimReport(1, int(done)), done


def _handle_dwarf(bot):
    if not _ensure_skip_animation(bot, "DwarfsTreasure"):
        return ClaimReport(), False
    daily = _wait_for(bot, "DwarfsTreasure/button_daily_free_chest", attempts=4,
                      threshold=0.66, region=(65, 12, 100, 38))
    if daily is None:
        bot.log("Gift Claims: Dwarf's Treasure không thấy Daily Free chính xác")
        return ClaimReport(), False
    bot.record("Gift Claims: Dwarf's Treasure tap exact Daily Free")
    bot.tap(*daily, delay=0.8)
    if _close_exact_congratulations(bot):
        return ClaimReport(1, 1), True
    gone = _wait_for(bot, "DwarfsTreasure/button_daily_free_chest", attempts=3,
                     threshold=0.66, region=(65, 12, 100, 38)) is None
    return ClaimReport(1, int(gone)), gone


def _wishful_open_blessings(bot) -> bool:
    if _wait_for(bot, "WishfulWindmillFestival/title_wind_blessings",
                 attempts=1, threshold=0.68) is not None:
        return True
    entry = _wait_for(bot, "WishfulWindmillFestival/button_wind_blessings",
                      attempts=4, threshold=0.68, region=(65, 15, 100, 60))
    if entry is None:
        return False
    bot.tap(*entry, delay=0.8)
    return _wait_for(bot, "WishfulWindmillFestival/title_wind_blessings",
                     attempts=4, threshold=0.68) is not None


def _handle_wishful(bot):
    attempted = 0
    if not _wishful_open_blessings(bot):
        return ClaimReport(), False
    no_records = _wait_for(bot, "WishfulWindmillFestival/status_no_records",
                           attempts=2, threshold=0.68, region=(0, 18, 100, 92))
    if no_records is None:
        claim_all = _wait_for(bot, "WishfulWindmillFestival/button_claim_all",
                              attempts=4, threshold=0.68, region=(35, 15, 100, 95))
        if claim_all is None:
            return ClaimReport(), False
        attempted += 1
        bot.record("Gift Claims: Wishful Windmill tap Claim All")
        bot.tap(*claim_all, delay=0.8)
        _close_exact_congratulations(bot)
        # Claim All returns to the main event; if it did not, one Back is safe
        # because the Wind Blessings title proves the child panel.
        if _wait_for(bot, "WishfulWindmillFestival/button_wind_blessings",
                     attempts=2, threshold=0.68, region=(65, 15, 100, 60)) is None:
            bot.back(delay=0.8)
        if not _wishful_open_blessings(bot):
            return ClaimReport(attempted, 0), False
        no_records = _wait_for(bot, "WishfulWindmillFestival/status_no_records",
                               attempts=4, threshold=0.68, region=(0, 18, 100, 92))
    if no_records is None:
        return ClaimReport(attempted, 0), False

    bot.record("Gift Claims: Wishful Windmill phần Wind Blessings = No Records")
    bot.back(delay=0.8)
    storage = _wait_for(bot, "WishfulWindmillFestival/tab_wind_power_storage",
                        attempts=4, threshold=0.68, region=(20, 5, 80, 20))
    if storage is None:
        return ClaimReport(attempted, 1), False
    bot.tap(*storage, delay=0.8)
    challenge = _wait_for(bot, "WishfulWindmillFestival/button_challenge_quest",
                          attempts=4, threshold=0.68, region=(0, 10, 100, 95))
    if challenge is None:
        return ClaimReport(attempted, 1), False
    bot.tap(*challenge, delay=0.6)
    for _ in range(12):
        claim = _wait_for(bot, "WishfulWindmillFestival/button_claim",
                          attempts=2, threshold=0.68, region=(35, 15, 100, 95))
        if claim is None:
            bot.record("Gift Claims: Wishful Windmill phần Challenge Quest hết Claim")
            return ClaimReport(attempted, 2), True
        attempted += 1
        bot.tap(*claim, delay=0.7)
        _close_exact_congratulations(bot)
    return ClaimReport(attempted, 1), False


EXACT_HANDLERS = {
    GiftScreen.PRECIOUS_BLAZON_EXCHANGE: _handle_precious,
    GiftScreen.POSEIDONS_DAY: _handle_poseidon,
    GiftScreen.HYPNOS_DREAM: _handle_hypnos,
    GiftScreen.GRACE_OF_STAR_TRAIL: _handle_grace,
    GiftScreen.GIANTS_WISDOM_TEMPLE: _handle_giant,
    GiftScreen.DWARFS_TREASURE: _handle_dwarf,
    GiftScreen.WISHFUL_WINDMILL_FESTIVAL: _handle_wishful,
}


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
    opened_entries = set()
    for attempt in range(attempts):
        bot.check()
        screen = bot.screenshot()
        screen_name = identify(bot, screen)
        control = SPECIAL_NAVIGATION.get(screen_name)
        if screen_name is not None and control is None:
            # A fixed page such as Grace has no Rewards/Daily Free launcher;
            # do not spend four screenshots proving that before its own flow.
            return ClaimReport()
        if control is not None:
            label, template = control
            pos = find(bot, template, screen, threshold=0.68, region=LOWER)
            if pos is not None:
                bot.record(f"Gift Claims: Event Center tap {label} ({template})")
                bot.tap(*pos, delay=1)
                attempted_count += 1
                if close_congratulations(bot):
                    bot.record(f"Gift Claims: verified {label} Congratulations")
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
            else:
                policy = POLICY_BY_SCREEN.get(screen_name)
                if policy is not None:
                    for entry in policy.navigation_entry:
                        if entry in opened_entries:
                            continue
                        entry_pos = find(bot, entry, screen, threshold=0.72,
                                         region=(0, 7, 100, 22))
                        if entry_pos is None:
                            continue
                        opened_entries.add(entry)
                        attempted_count += 1
                        bot.record(f"Gift Claims: Event Center mở tab {entry}")
                        bot.tap(*entry_pos, delay=1)
                        break
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
        pos = find(bot, template, screen, threshold=0.68,
                   region=REWARD_NAV_REGION)
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
                         threshold=0.70, region=REWARD_NAV_REGION)
            if claim is not None:
                attempted += 1
                bot.record("Gift Claims: tap Grace of Star Trail coin Claim")
                bot.tap(*claim, delay=1)
                if close_congratulations(bot):
                    bot.record("Gift Claims: verified Star Trail coin Congratulations")
                    return ClaimReport(attempted, 1)
                after = bot.screenshot()
                if find(bot, "GraceOfStarTrail/button_claim", after,
                        threshold=0.70, region=REWARD_NAV_REGION) is None:
                    bot.record("Gift Claims: verified Star Trail coin Claim disappeared")
                    return ClaimReport(attempted, 1)
            if attempt < 3:
                bot.sleep(0.5)
        # The user-defined terminal state is the opened Star Trail Gift page
        # with no remaining coin Claim control.
        bot.record("Gift Claims: Star Trail Gift đã mở và không còn coin Claim; DONE")
        return ClaimReport(attempted, 1)
    return ClaimReport()


def _process_current_event_content(bot, *, special_attempts=4):
    """Process one selected inner tab; return (claims, panel_was_closed)."""
    opened_name = identify(bot)
    special = (_tap_special_navigation(bot, attempts=special_attempts)
               if opened_name in SPECIAL_NAVIGATION else ClaimReport())
    if opened_name in SPECIAL_NAVIGATION:
        # Dwarf/Precious/Hypnos each has one exact free-reward launcher.  Once
        # it has been checked, the event is exhausted.  Continuing into the
        # generic sparkle fallback is unsafe: on the real Dwarf page the
        # animated castle bubbles led out to the paid Decorate screen even
        # after Daily Free had already produced Congratulations.
        return special, False
    reward_navigation = _tap_reward_navigation(bot)
    if opened_name == GiftScreen.GRACE_OF_STAR_TRAIL:
        # Grace has one exact contract: Star Trail Gift -> coin Claim.  If the
        # child opened but Claim was not verified, keep it pending; unrelated
        # sparkle checks must not hide that actionable recognition failure.
        return reward_navigation, False
    fixed = claim_fixed_controls(bot, FIXED_CLAIMS, max_taps=16,
                                 initial_wait_attempts=2, region=LOWER)
    if back_if_close_x(bot):
        return ClaimReport(special.attempted + reward_navigation.attempted +
                           fixed.attempted,
                           special.verified + reward_navigation.verified +
                           fixed.verified), True
    sparkle = claim_sparkles(bot, region=SPARKLE_SAFE, attempts=3)
    if sparkle.claimed:
        bot.record("Gift Claims: Event Center nhận quà sparkle (Congratulations)")
    return (ClaimReport(special.attempted + reward_navigation.attempted +
                        fixed.attempted + sparkle.attempted,
                        special.verified + reward_navigation.verified +
                        fixed.verified + sparkle.verified), False)


def _finish_event(bot, policy, report: ClaimReport) -> ClaimReport:
    """Persist the named child only after its opened content was exhausted."""
    if policy is not None and policy.key is not None:
        mark_task_done(bot, policy.key)
    return report


def _process_known_event(bot, policy) -> ClaimReport:
    """Check a named event twice when no reward success can be verified."""
    exact = EXACT_HANDLERS.get(policy.screen)
    if exact is not None:
        report, completed = exact(bot)
        if completed:
            return _finish_event(bot, policy, report)
        bot.record(f"Gift Claims: {policy.label} chưa đạt điều kiện DONE riêng; giữ PENDING")
        return report

    total = ClaimReport()
    for pass_number in range(1, MAX_EVENT_VERIFY_PASSES + 1):
        bot.check()
        # One exact control probe per outer verification pass. Poseidon's
        # first pass may open Ocean Offering and the second then claims Daily
        # Free; Dwarf/Hypnos/Precious never receive more than two blind taps.
        report, _ = _process_current_event_content(bot, special_attempts=1)
        total = ClaimReport(total.attempted + report.attempted,
                            total.verified + report.verified)
        if report.claimed:
            bot.record(f"Gift Claims: {policy.label} đã xác minh nhận quà ở "
                       f"lượt {pass_number}/{MAX_EVENT_VERIFY_PASSES}")
            return _finish_event(bot, policy, total)
        bot.log(f"Gift Claims: {policy.label} chưa có Congratulations/nút biến "
                f"mất ở lượt {pass_number}/{MAX_EVENT_VERIFY_PASSES}")

    bot.record(f"Gift Claims: {policy.label} không nhận thêm được quà sau "
               f"{MAX_EVENT_VERIFY_PASSES} lượt kiểm tra; coi mục đã cạn và "
               "DONE hôm nay")
    return _finish_event(bot, policy, total)


def _process_opened_event(bot):
    opened = bot.screenshot()
    name = identify(bot, opened)
    policy = POLICY_BY_SCREEN.get(name)
    if (policy is not None and policy.key is not None
            and bot.is_daily_done(policy.key) is True):
        bot.record(f"Gift Claims: {policy.label} đã DONE trong DB hôm nay; bỏ qua")
        return ClaimReport()
    skipped = SKIPPED_SCREENS.get(name)
    if name == GiftScreen.EVENT_CENTER:
        bot.log("Gift Claims: cú bấm vẫn ở danh sách Event Center; không xử lý "
                "chấm đỏ của thanh nhóm như tab quà")
        return ClaimReport()
    if skipped is not None:
        bot.record(f"Gift Claims: {skipped.label} - {skipped.skip_reason}")
        return _finish_event(bot, skipped, ClaimReport())
    if name in (GiftScreen.BACCHUS_TAVERN, GiftScreen.FOLLOW_US):
        bot.record(f"Gift Claims: {name.value} - nhận diện và bỏ qua")
        return ClaimReport()

    # A page without a captured title (currently including Blessing of
    # Pallas) must not feed its artwork into the red-dot
    # carousel detector.  On the real Pallas frame the countdown/book art at
    # y≈64 was mistaken for three inner tabs, costing almost the whole 120 s
    # slice.  Inspect the page body exactly once; its fixed Claim/Free controls
    # are still handled, but decorative red pixels can no longer drive taps.
    if name is None:
        if find(bot, "BlessingOfPallas/status_claimed", opened, threshold=0.68,
                region=LOWER) is not None:
            bot.record("Gift Claims: Blessing of Pallas đã hiện Claimed")
            mark_task_done(bot, blessing_of_pallas.POLICY.key)
            return ClaimReport(0, 1)
        bot.record("Gift Claims: Event Center page chưa có title template; "
                   "kiểm tra nội dung một lần, không quét dot trong artwork")
        report, _ = _process_current_event_content(bot)
        after = bot.screenshot()
        if find(bot, "BlessingOfPallas/status_claimed", after, threshold=0.68,
                region=LOWER) is not None:
            bot.record("Gift Claims: Blessing of Pallas xác minh Claim -> Claimed")
            mark_task_done(bot, blessing_of_pallas.POLICY.key)
        return report

    # Grace may keep its claim badge only on the nested Star Trail Gift icon,
    # without a reliable red dot on the Event Center list row. Open it once
    # per task and use the exact current icon crop before any generic red scan.
    if name == GiftScreen.GRACE_OF_STAR_TRAIL:
        return _process_known_event(bot, policy)

    # Every captured Event Center page owns a dedicated policy.  Its exact
    # Rewards/Daily Free/Claim controls are safer and faster than interpreting
    # arbitrary red artwork in the title strip.  On real Hypnos frames the
    # gold info icon, and later the red X plus quest decorations, all satisfied
    # the old generic dot geometry and opened the Quests modal after Rewards
    # had already been collected.  Keep generic inner-tab scanning only for a
    # genuinely UNKNOWN page until that event receives its own title/policy.
    if policy is not None:
        return _process_known_event(bot, policy)

    # Most Event Center rows have no nested carousel badge. Scanning the full
    # horizontal strip for every such row can consume the whole 120-second
    # window. A visible badge is the signal that this event needs the nested
    # sweep; otherwise process only its current reward content.
    if not _inner_red_dots(opened):
        report, _ = _process_current_event_content(bot)
        return _finish_event(bot, policy, report)

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
                        delay=1)
                report, closed = _process_current_event_content(bot)
                total = ClaimReport(total.attempted + report.attempted,
                                    total.verified + report.verified)
                attempted.add(signature)
                handled_positions.append(dot)
                if closed:
                    return _finish_event(bot, policy, total)
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
    return _finish_event(bot, policy, total)


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
    bot.tap_percent(x_percent, 11, delay=1)
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


def _mark_missing_event_policies_done(bot, seen_policy_keys: set[str]) -> None:
    """Close DB keys for rotating events absent from a complete Limited scan.

    Event Center entries rotate or expire from day to day.  Absence is a
    terminal daily result, but a page that was found and failed its own exact
    completion contract must remain pending.
    """
    for policy in EVENT_POLICIES:
        if policy.key is None or policy.key in seen_policy_keys:
            continue
        if bot.is_daily_done(policy.key):
            continue
        bot.record(f"Gift Claims: không tìm thấy {policy.label} trong lượt quét "
                   "Limited từ đầu tới cuối; DONE hôm nay")
        mark_task_done(bot, policy.key)


def _policy_seen_checkpoint(policy_key: str) -> bytes:
    return POLICY_SEEN_PREFIX + policy_key.encode("utf-8")


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
    failed_forced = set()
    recentered_forced = set()
    recentered_rows = set()
    seen_policy_keys: set[str] = {
        item[len(POLICY_SEEN_PREFIX):].decode("utf-8")
        for item in visited if item.startswith(POLICY_SEEN_PREFIX)
    }
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
                for (template, key, expected_screen, event_label,
                     policy_key) in FORCED_LIMITED_ROWS:
                    if key in visited or key in failed_forced:
                        continue
                    row = find(bot, template, screen, threshold=0.90,
                               region=(10, 15, 75, 98))
                    if isinstance(row, tuple) and len(row) == 2:
                        if (row[1] > int(screen.shape[0] * 0.80)
                                and key not in recentered_forced):
                            # A row title can be visible above the bottom bar
                            # while its clickable body is still off-screen.
                            # Bring it into the list body before selecting it.
                            recentered_forced.add(key)
                            bot.record(f"Gift Claims: kéo {event_label} từ sát đáy "
                                       "lên giữa màn hình trước khi bấm")
                            bot.swipe_percent(50, 82, 50, 52,
                                              duration=0.4, delay=0.8)
                            candidate = "recenter"
                            break
                        # The title sits near the top edge of a list row. Tap
                        # below it so a small residual scroll cannot select
                        # the preceding event (observed with Dwarf -> Sealed).
                        tap_y = min(screen.shape[0] - 1, row[1] + 18)
                        candidate = (tap_y, key, expected_screen, event_label,
                                     policy_key)
                        bot.record(f"Gift Claims: Event Center mở {event_label} "
                                   "để kiểm tra quà bên trong dù dòng ngoài không đỏ "
                                   f"(y={tap_y})")
                        break
                if candidate == "recenter":
                    continue
            for _, y in _row_dots(bot, screen):
                if candidate is not None:
                    break
                signature = _row_signature(screen, y)
                key = _category_signature(category, signature)
                if not _category_seen(category, signature, visited):
                    if (y > int(screen.shape[0] * 0.80)
                            and key not in recentered_rows):
                        recentered_rows.add(key)
                        bot.record("Gift Claims: kéo hàng đỏ sát đáy lên giữa trước khi bấm")
                        bot.swipe_percent(50, 82, 50, 52,
                                          duration=0.4, delay=0.8)
                        candidate = "recenter"
                        break
                    candidate = y, key, None, None, None
                    break
            if candidate == "recenter":
                continue
            if candidate is None:
                break
            y, key, expected_screen, event_label, forced_policy_key = candidate
            bot.tap_percent(52, y * 100 / screen.shape[0], delay=1)
            actual_screen = identify(bot)
            for _ in range(4):
                if actual_screen != GiftScreen.EVENT_CENTER:
                    break
                bot.sleep(0.5)
                actual_screen = identify(bot)
            if actual_screen == GiftScreen.EVENT_CENTER:
                bot.log("Gift Claims: bấm hàng nhưng vẫn ở Event Center; bỏ vị trí "
                        "này trong lượt quét và không kết luận event vắng mặt")
                failed_forced.add(key)
                if forced_policy_key is not None:
                    seen_policy_keys.add(forced_policy_key)
                    visited.add(_policy_seen_checkpoint(forced_policy_key))
                visited.add(key)
                continue
            actual_policy = POLICY_BY_SCREEN.get(actual_screen)
            if actual_policy is not None and actual_policy.key is not None:
                seen_policy_keys.add(actual_policy.key)
                visited.add(_policy_seen_checkpoint(actual_policy.key))
            elif forced_policy_key is not None:
                # Pallas currently has no stable page-title crop; the exact
                # list label is its identity.
                seen_policy_keys.add(forced_policy_key)
                visited.add(_policy_seen_checkpoint(forced_policy_key))
            if expected_screen is not None:
                if actual_screen != expected_screen:
                    bot.log(f"Gift Claims: bấm hàng {event_label} nhưng mở "
                            f"{getattr(actual_screen, 'value', actual_screen)}; "
                            "không đánh dấu DONE, giữ PENDING")
                    failed_forced.add(key)
                    if not _back_to_list(bot):
                        return False
                    continue
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

    clean = _verify_clean(bot, category, visited) and not failed_forced
    has_checkpoint = any(item.startswith(category.encode("ascii") + b"\0")
                         for item in visited)
    if not clean and has_checkpoint and not failed_forced:
        # The authoritative sweep already opened every visible red row.  Some
        # event badges remain red for purchases, locked rewards, or rotating
        # notices even after four failed claim/sparkle checks.  They are now
        # explicit bounded skips and must not block the combined DB task.
        bot.record(f"Gift Claims: Event Center/{category} còn badge đỏ dai dẳng "
                   "sau khi đã quét; đánh dấu skip/done")
        clean = True
    if clean and category == "limited":
        _mark_missing_event_policies_done(bot, seen_policy_keys)
    bot.record(f"Gift Claims: Event Center/{category} đã mở {opened_count} dòng đỏ; "
               + ("DONE, danh sách hết đỏ" if clean
                  else "chưa DONE, danh sách vẫn còn đỏ"))
    return clean


def run_opened(bot, handled=None):
    """Scan only Limited, resuming its handled rows after a Boss yield."""
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
