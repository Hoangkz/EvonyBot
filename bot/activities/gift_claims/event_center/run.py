"""Scroll Event Center and process only the explicitly supported events."""
import time

import cv2
import numpy as np

from . import (blessing_of_pallas, dragon_battle, dwarfs_lucky_apple,
               dwarfs_treasure,
               eagle_of_freedom,
               giants_wisdom_temple, grace_of_star_trail, hypnos_dream,
               legion_hunting,
               moment_of_glory,
               poseidons_day, precious_blazon_exchange, revelation_of_horus,
               sealed_imperial_treasury, wishful_windmill_festival)
from ..common import (ClaimReport, GiftTask, TEXT_CLAIM_CONTROLS, back_if_close_x,
                     _scaled_template,
                     claim_fixed_controls, claim_sparkles,
                     close_congratulations, find, find_all,
                     mark_task_done, open_event_center, return_home)
from ..screens import GiftScreen, identify
from ..valuable_event.named_flow import region_hamming_distance

KEY = "gift_event_center_limited"
PAGE = "EventCenter/title"
CONGRATULATIONS = "SuperValueReturn/LoginGifts/congratulations"
# Event Center uses the same edge contract as Valuable Event: an edge is real
# only after two consecutive settled swipes do not move the list.  There is no
# local swipe ceiling; bot.check() owns Stop/deadline safety.
LIST_EDGE_CONFIRMATIONS = 2
# The Event Center rows animate their artwork, timers and marquee descriptions
# even while the list is stationary.  Hash only the vertical row structure;
# 16 consecutive live top-edge frames on emulator 21503 measured 0 changed
# bits, while simulated list displacement measured 18..48 bits.
LIST_SAME_DISTANCE = 8
LIST_SIGNATURE_BITS = 96
# Eagle of Freedom owns a vertically scrolling quest panel.  This limit is a
# safety ceiling only; normal completion is detected from two no-movement
# swipes at the real bottom, not from a fixed number of four content screens.
MAX_EAGLE_CONTENT_SWIPES = 12
EAGLE_BOTTOM_CONFIRMATIONS = 2
# Legion Hunting uses the green quest list (roughly y=39..98%).  Its DONE
# contract is one complete top-to-bottom pass without a Claim button.
LEGION_CONTENT_REGION = (2, 39, 98, 98)
LEGION_CLAIM_REGION = (65, 39, 100, 98)
MAX_LEGION_CONTENT_SWIPES = 12
MAX_LEGION_VERIFY_PASSES = 3
MAX_LEGION_CLAIMS_PER_VIEW = 6
LEGION_EDGE_CONFIRMATIONS = 2
MOMENT_CONTENT_REGION = (1, 40, 99, 97)
MOMENT_CLAIM_REGION = (62, 40, 100, 97)
MOMENT_SCAN_SWIPE = (50, 90, 50, 48)
MOMENT_RETURN_TOP_SWIPE = (50, 48, 50, 90)
MOMENT_EDGE_CONFIRMATIONS = 2
MOMENT_SAME_DISTANCE = 24
MAX_MOMENT_CLAIMS_PER_VIEW = 12
MOMENT_GREEN_MIN_RATIO = 0.20
MOMENT_GRAY_MAX_RATIO = 0.45
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
APPLE_STATE_THRESHOLD = 0.80
APPLE_ORNAMENT_THRESHOLD = 0.70
APPLE_ORNAMENT_WIDTH_RATIO = 0.18
# Exact text/border scores fall to 0.485 on the user's lagged live frames,
# while their HSV bands remain decisive (ACTIVE S=185/81% saturated; DONE
# S=24/7%). Require the exact control to score at least 0.44, then let the
# strict yellow/gray colour gates below decide the state.
APPLE_COLOR_LOCATE_THRESHOLD = 0.44
APPLE_ACTIVE_SATURATION_MIN = 110.0
APPLE_ACTIVE_COLOR_RATIO_MIN = 0.35
APPLE_DONE_SATURATION_MAX = 65.0
APPLE_DONE_COLOR_RATIO_MAX = 0.20
APPLE_COLOR_SATURATION_CUTOFF = 100
# Sau khi chính nút đỏ x10 vừa được nhận diện ACTIVE và được bấm, layout đổi
# làm template DONE chỉ còn khoảng 0.50 (log thực tế 0.507). Khi đồng thời thấy
# Once đỏ và dải tại vị trí x10 đã xám, ngưỡng định vị thấp này là an toàn.
APPLE_RED_POST_TAP_GRAY_LOCATE_THRESHOLD = 0.45
APPLE_RED_X10_DISTINCT_DISTANCE = 45
APPLE_RED_MULTIPLIER_DONE_THRESHOLD = 0.80
APPLE_RED_MULTIPLIER_DISTINCT_DISTANCE = 45
# A loose multiplier threshold is necessary on lagged devices, but the exact
# Wish Once crop still scores much higher at its own location.  Do not let
# that yellow/grey Once button impersonate x100/x10 merely because their
# ornaments overlap visually.
APPLE_ONCE_EXCLUSION_THRESHOLD = 0.70
APPLE_ONCE_EXCLUSION_DISTANCE = 45
MAX_APPLE_TAPS_PER_PHASE = 100
APPLE_STATE_MISS_RETRIES = 3
# MEmu can become noticeably slower when the worker controls many devices at
# once.  Keep every Event Center interaction paced from one place so image
# recognition never samples the previous frame immediately after a tap/swipe.
UI_SETTLE_SECONDS = 1.5
SWIPE_DURATION_SECONDS = 1.0
# A 30-emulator host can keep moving/repainting the Event Center list after
# ADB has finished the swipe.  List navigation therefore gets a longer pause
# than ordinary taps, and every list position is sampled twice before moving.
LIST_SCROLL_SETTLE_SECONDS = 2.0
# Activities currently owns one supported row: Dwarf's Lucky Apple.  Its
# title is static, so the list can be scanned safely at the faster cadence the
# user requested instead of inheriting the conservative multi-device delay of
# the animated Limited list.
APPLE_LIST_SETTLE_SECONDS = 0.8
APPLE_LIST_EDGE_CONFIRMATIONS = 2
WISHFUL_SETTLE_SECONDS = 1.0
WISHFUL_CONFIRMATION_DELAY_SECONDS = 1.0
# Screenshot_20261027-? Wind Blessings green frame: x=20..376,
# y=190..573 on 396x704.  Restrict all reads and gestures to its interior.
WISHFUL_CONTENT_REGION = (6, 28, 94, 81)
WISHFUL_CLAIM_REGION = (65, 28, 94, 81)
WISHFUL_SCAN_SWIPE = (8, 79.5, 8, 29)
WISHFUL_SCROLL_DURATION_SECONDS = 1.2
WISHFUL_SAME_DISTANCE = 8
MAX_WISHFUL_CLAIMS = 30
MAX_WISHFUL_TAPS_PER_CLAIM = 3
WISHFUL_EDGE_CONFIRMATIONS = 2
# The supplied active Claim crop measures green=0.583/low-saturation=0.483;
# the Claimed crop measures green=0.000/low-saturation=0.867.  Its white text
# makes the generic 0.45 gray ceiling too strict for this event.
WISHFUL_GREEN_MIN_RATIO = 0.22
WISHFUL_GRAY_MIN_RATIO = 0.50
WISHFUL_ACTIVE_GRAY_MAX_RATIO = 0.65
WISHFUL_DONE_ONE_LIMIT = (
    "EventCenter/WishfulWindmillFestival/status_done_one_claim_limit", 0.84)
WISHFUL_DONE_ONE_NO_RECORDS = (
    "EventCenter/WishfulWindmillFestival/status_no_records", 0.84)
WISHFUL_DONE_TWO_CHEST = (
    "EventCenter/WishfulWindmillFestival/button_done2_reward_chest_median",
    0.70,
)
WISHFUL_DONE_TWO_CHEST_REGION = (2, 15, 28, 35)
EMPTY_POSITION_CHECKS = 2
APPLE_GREEN_ONCE_STATES = (
    ("EventCenter/DwarfsLuckyApple/status_green_wish_once", 0.84),
    ("EventCenter/DwarfsLuckyApple/status_green_wish_once_gray", 0.80),
)
APPLE_RED_ONCE_STATES = (
    ("EventCenter/DwarfsLuckyApple/status_red_wish_once", 0.84),
    ("EventCenter/DwarfsLuckyApple/status_red_wish_once_gray", 0.80),
)
CATEGORIES = (
    ("limited", 18),
    ("activities", 49),
)
CATEGORY_DONE_PREFIX = b"__category_done__\0"
FORCED_EVENT_PREFIX = b"__forced_event__\0"
POLICY_SEEN_PREFIX = b"__policy_seen__\0"
SEEN_POLICIES_ATTR = "_gift_claims_event_center_seen_policies"
SCAN_COMPLETE_ATTR = "_gift_claims_event_center_scan_complete"
SCANNED_CATEGORIES_ATTR = "_gift_claims_event_center_scanned_categories"
PENDING_THIS_RUN_ATTR = "_gift_claims_event_center_pending_this_run"
CATEGORY_RESUME_KEYS = {
    "limited": "gift_event_center_resume_limited",
    "activities": "gift_event_center_resume_activities",
}


def _ordered_categories(bot):
    """Put the durable resume category first for the next 120-second window."""
    preferred = next((category for category, _ in CATEGORIES
                      if bot.is_daily_done(CATEGORY_RESUME_KEYS[category])), None)
    if preferred is None:
        return CATEGORIES
    return tuple(item for item in CATEGORIES if item[0] == preferred) + tuple(
        item for item in CATEGORIES if item[0] != preferred)


def _set_resume_category(bot, category: str) -> None:
    """Persist which category must run first after a timeout or boss yield."""
    wanted = CATEGORY_RESUME_KEYS[category]
    for key in CATEGORY_RESUME_KEYS.values():
        if key == wanted:
            if not bot.is_daily_done(key):
                bot.mark_daily_done(key)
        elif bot.done_at(key) is not None:
            bot.forget_daily(key)
    bot.record(f"Gift Claims: lượt Event Center kế tiếp bắt đầu từ {category}")


def clear_resume_category(bot) -> None:
    for key in CATEGORY_RESUME_KEYS.values():
        if bot.done_at(key) is not None:
            bot.forget_daily(key)


EVENT_POLICIES = (
    blessing_of_pallas.POLICY,
    dragon_battle.POLICY,
    precious_blazon_exchange.POLICY,
    poseidons_day.POLICY,
    hypnos_dream.POLICY,
    grace_of_star_trail.POLICY,
    sealed_imperial_treasury.POLICY,
    dwarfs_treasure.POLICY,
    dwarfs_lucky_apple.POLICY,
    eagle_of_freedom.POLICY,
    legion_hunting.POLICY,
    moment_of_glory.POLICY,
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
    ("EventCenter/BlessingOfPallas/list_row", FORCED_EVENT_PREFIX + b"blessing_of_pallas",
     None, "Blessing of Pallas", blessing_of_pallas.POLICY.key),
    ("EventCenter/DragonBattle/list_row", FORCED_EVENT_PREFIX + b"dragon_battle",
     GiftScreen.DRAGON_BATTLE, "Dragon Battle", dragon_battle.POLICY.key),
    ("EventCenter/PreciousBlazonExchange/list_row",
     FORCED_EVENT_PREFIX + b"precious_blazon_exchange",
     GiftScreen.PRECIOUS_BLAZON_EXCHANGE, "Precious Blazon Exchange",
     precious_blazon_exchange.POLICY.key),
    ("EventCenter/GraceOfStarTrail/list_row", FORCED_EVENT_PREFIX + b"grace_of_star_trail",
     GiftScreen.GRACE_OF_STAR_TRAIL, "Grace of Star Trail",
     grace_of_star_trail.POLICY.key),
    # Dwarf's Treasure may lose its outer Event Center badge while the
    # Daily Free chest inside is still claimable.  Check the named row once
    # per daily run instead of using the outer badge as its source of truth.
    ("EventCenter/DwarfsTreasure/list_row", FORCED_EVENT_PREFIX + b"dwarfs_treasure",
     GiftScreen.DWARFS_TREASURE, "Dwarf's Treasure", dwarfs_treasure.POLICY.key),
    ("EventCenter/GiantsWisdomTemple/list_row", FORCED_EVENT_PREFIX + b"giants_wisdom_temple",
     GiftScreen.GIANTS_WISDOM_TEMPLE, "Giant's Wisdom Temple",
     giants_wisdom_temple.POLICY.key),
    ("EventCenter/WishfulWindmillFestival/list_row",
     FORCED_EVENT_PREFIX + b"wishful_windmill_festival",
     GiftScreen.WISHFUL_WINDMILL_FESTIVAL, "Wishful Windmill Festival",
     wishful_windmill_festival.POLICY.key),
    ("EventCenter/EagleOfFreedom/list_row", FORCED_EVENT_PREFIX + b"eagle_of_freedom",
     GiftScreen.EAGLE_OF_FREEDOM, "Eagle of Freedom",
     eagle_of_freedom.POLICY.key),
    ("EventCenter/LegionHunting/list_row", FORCED_EVENT_PREFIX + b"legion_hunting",
     GiftScreen.LEGION_HUNTING, "Legion Hunting",
     legion_hunting.POLICY.key),
    ("EventCenter/MomentOfGlory/list_row", FORCED_EVENT_PREFIX + b"moment_of_glory",
     GiftScreen.MOMENT_OF_GLORY, "Moment of Glory",
     moment_of_glory.POLICY.key),
)
FORCED_ACTIVITY_ROWS = (
    ("EventCenter/DwarfsLuckyApple/list_row",
     FORCED_EVENT_PREFIX + b"dwarfs_lucky_apple",
     GiftScreen.DWARFS_LUCKY_APPLE, "Dwarf's Lucky Apple",
     dwarfs_lucky_apple.POLICY.key),
)
POLICY_CATEGORIES = {
    dwarfs_lucky_apple.POLICY.key: "activities",
}


def run(bot):
    screen = open_event_center(bot)
    if screen is None:
        return False
    completed = run_opened(bot)
    return_home(bot)
    return completed


def _close_congratulations(bot):
    screen = bot.screenshot()
    if find(bot, CONGRATULATIONS, screen, threshold=0.78,
            region=(0, 38, 100, 62)) is not None:
        bot.back(delay=UI_SETTLE_SECONDS)
        return True
    return False


def _close_exact_congratulations(bot) -> bool:
    """Close either supplied Event Center congratulations marker."""
    if close_congratulations(bot, attempts=1):
        return True
    screen = bot.screenshot()
    if find(bot, "EventCenter/PreciousBlazonExchange/popup_congratulations", screen,
            threshold=0.72, region=(0, 35, 100, 65)) is None:
        return False
    bot.back(delay=UI_SETTLE_SECONDS)
    return True


def _wait_for(bot, template: str, *, attempts=4, threshold=0.68,
              region=(0, 0, 100, 100), delay=None):
    delay = UI_SETTLE_SECONDS if delay is None else delay
    for attempt in range(attempts):
        screen = bot.screenshot()
        pos = find(bot, template, screen, threshold=threshold, region=region)
        if pos is not None:
            return pos
        if attempt + 1 < attempts:
            bot.sleep(delay)
    return None


def _wait_for_any(bot, templates: tuple[str, ...], *, attempts=4,
                  threshold=0.68, region=(0, 0, 100, 100), delay=None):
    """Find the first matching visual variant on each freshly captured frame."""
    delay = UI_SETTLE_SECONDS if delay is None else delay
    for attempt in range(attempts):
        screen = bot.screenshot()
        for template in templates:
            pos = find(bot, template, screen, threshold=threshold,
                       region=region)
            if pos is not None:
                bot.record(f"Gift Claims: nhận diện {template}")
                return pos
        if attempt + 1 < attempts:
            bot.sleep(delay)
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
    bot.tap(*pos, delay=UI_SETTLE_SECONDS)
    return _wait_for(bot, checked, attempts=3, region=region) is not None


def _handle_precious(bot):
    attempted = 0
    for attempt in range(4):
        screen = bot.screenshot()
        if find(bot, "EventCenter/PreciousBlazonExchange/status_rewards_claimed", screen,
                threshold=0.68, region=(0, 12, 40, 48)) is not None:
            return ClaimReport(attempted, 1), True
        rewards = find(bot, "EventCenter/PreciousBlazonExchange/button_rewards_text", screen,
                       threshold=0.62, region=(0, 12, 45, 48))
        if rewards is not None:
            attempted += 1
            bot.record("Gift Claims: Precious Blazon Exchange tap exact Rewards")
            bot.tap(*rewards, delay=UI_SETTLE_SECONDS)
            if _close_exact_congratulations(bot):
                return ClaimReport(attempted, 1), True
        if attempt + 1 < 4:
            bot.sleep(UI_SETTLE_SECONDS)
    done = _wait_for(bot, "EventCenter/PreciousBlazonExchange/status_rewards_claimed", attempts=2,
                     threshold=0.68, region=(0, 12, 40, 48)) is not None
    return ClaimReport(attempted, int(done)), done


def _handle_hypnos(bot):
    attempted = 0
    # The page is already identified by its fixed title.  Four misses in the
    # exact upper-right reward area means its chest/Rewards control is gone.
    for attempt in range(4):
        screen = bot.screenshot()
        rewards = find(bot, "EventCenter/HypnosDream/button_rewards_text", screen,
                       threshold=0.62, region=(65, 12, 100, 38))
        if rewards is None:
            if attempt + 1 < 4:
                bot.sleep(UI_SETTLE_SECONDS)
                continue
            bot.record("Gift Claims: Hypnos' Dream không còn Rewards ở góc phải")
            return ClaimReport(attempted, 1), True
        attempted += 1
        bot.record("Gift Claims: Hypnos' Dream tap exact Rewards")
        bot.tap(*rewards, delay=UI_SETTLE_SECONDS)
        if _close_exact_congratulations(bot):
            return ClaimReport(attempted, 1), True
    return ClaimReport(attempted, 0), False


def _handle_poseidon(bot):
    attempted = 0
    for attempt in range(5):
        screen = bot.screenshot()
        if find(bot, "EventCenter/PoseidonsDay/status_daily_free_claimed", screen, threshold=0.68,
                region=(65, 12, 100, 38)) is not None:
            return ClaimReport(attempted, 1), True
        daily = find(bot, "EventCenter/PoseidonsDay/button_daily_free_text", screen,
                     threshold=0.62, region=(65, 12, 100, 38))
        if daily is not None:
            attempted += 1
            bot.record("Gift Claims: Poseidon's Day tap exact Daily Free")
            bot.tap(*daily, delay=UI_SETTLE_SECONDS)
            if _close_exact_congratulations(bot):
                return ClaimReport(attempted, 1), True
        elif attempt == 0:
            package = find(bot, "EventCenter/PoseidonsDay/tab_packages_red_dot", screen,
                           threshold=0.68, region=(45, 5, 90, 18))
            if package is not None:
                attempted += 1
                bot.record("Gift Claims: Poseidon's Day mở tab Packages có chấm đỏ")
                bot.tap(*package, delay=UI_SETTLE_SECONDS)
        if attempt + 1 < 5:
            bot.sleep(UI_SETTLE_SECONDS)
    done = _wait_for(bot, "EventCenter/PoseidonsDay/status_daily_free_claimed", attempts=2, threshold=0.68,
                     region=(65, 12, 100, 38)) is not None
    return ClaimReport(attempted, int(done)), done


def _handle_grace(bot):
    report = _tap_reward_navigation(bot)
    return report, report.verified > 0


def _handle_giant(bot):
    ended = _wait_for(bot, "EventCenter/GiantsWisdomTemple/status_event_ended",
                      attempts=2, threshold=0.70,
                      region=(0, 8, 100, 75))
    if ended is not None:
        bot.record("Gift Claims: Giant's Wisdom Temple hiện Event has ended; DONE")
        return ClaimReport(0, 1), True
    if not _ensure_skip_animation(bot, "GiantsWisdomTemple"):
        return ClaimReport(), False
    target = _wait_for(bot, "EventCenter/GiantsWisdomTemple/button_free_wisdom_tile", attempts=4,
                       threshold=0.70, region=(0, 30, 100, 92))
    if target is None:
        return ClaimReport(), False
    bot.record("Gift Claims: Giant's Wisdom Temple tap exact free tile")
    # The result animation is noticeably slower on a multi-emulator host.
    bot.tap(*target, delay=LIST_SCROLL_SETTLE_SECONDS)
    if _close_exact_congratulations(bot):
        return ClaimReport(1, 1), True
    ended = _wait_for(bot, "EventCenter/GiantsWisdomTemple/status_event_ended",
                      attempts=4, threshold=0.70,
                      region=(0, 8, 100, 75))
    if ended is not None:
        bot.record("Gift Claims: Giant's Wisdom Temple nhận Event has ended; DONE")
        return ClaimReport(1, 1), True
    done = _wait_for(bot, "EventCenter/GiantsWisdomTemple/message_not_enough_items", attempts=4,
                     threshold=0.70, region=(0, 15, 100, 45)) is not None
    return ClaimReport(1, int(done)), done


def _handle_dwarf(bot):
    if not _ensure_skip_animation(bot, "DwarfsTreasure"):
        return ClaimReport(), False
    daily = _wait_for(bot, "EventCenter/DwarfsTreasure/button_daily_free_chest", attempts=4,
                      threshold=0.66, region=(65, 12, 100, 38))
    if daily is None:
        # The exact Dwarf page and checked Skip-animation state prove that the
        # page finished loading.  Daily Free disappears after it is claimed,
        # so four paced misses are the terminal already-claimed state rather
        # than an unfinished task.
        bot.record("Gift Claims: Dwarf's Treasure không còn Daily Free; DONE")
        return ClaimReport(0, 1), True
    bot.record("Gift Claims: Dwarf's Treasure tap exact Daily Free")
    bot.tap(*daily, delay=UI_SETTLE_SECONDS)
    if _close_exact_congratulations(bot):
        return ClaimReport(1, 1), True
    gone = _wait_for(bot, "EventCenter/DwarfsTreasure/button_daily_free_chest", attempts=3,
                     threshold=0.66, region=(65, 12, 100, 38)) is None
    return ClaimReport(1, int(gone)), gone


def _handle_dragon_battle(bot):
    """Use Dragon Battle's exact chest and terminal-state contract."""
    return dragon_battle.claim_opened(bot)


def _wishful_panel_open(bot, *, attempts=5) -> bool:
    """Recognize either captured Wind Blessings title without leaving it."""
    variants = (
        ("EventCenter/WishfulWindmillFestival/title_wind_blessings_text", 0.80),
        ("EventCenter/WishfulWindmillFestival/title_wind_blessings", 0.68),
    )
    for attempt in range(attempts):
        screen = bot.screenshot()
        for template, threshold in variants:
            if find(bot, template, screen, threshold=threshold,
                    region=(0, 12, 100, 28)) is not None:
                return True
        if attempt + 1 < attempts:
            bot.sleep(WISHFUL_SETTLE_SECONDS)
    return False


def _wishful_find_entry(bot, *, attempts=5):
    """Find a stable Wind Blessings launcher, including the new Wind chest."""
    variants = (
        ("EventCenter/WishfulWindmillFestival/button_wind_blessings", 0.68,
         "Wind Blessings"),
        # Screenshot_20261023-073758 includes the chest and its dark Wind
        # caption, making it safer than matching only the animated chest.
        ("EventCenter/WishfulWindmillFestival/button_reward_chest_wind", 0.86,
         "rương Wind Blessings"),
        ("EventCenter/WishfulWindmillFestival/button_reward_chest", 0.82,
         "rương DONE 1"),
    )
    for attempt in range(attempts):
        screen = bot.screenshot()
        for template, threshold, label in variants:
            entry = find(bot, template, screen, threshold=threshold,
                         region=(0, 12, 100, 85))
            if entry is not None:
                return entry, template, threshold, label
        if attempt + 1 < attempts:
            bot.sleep(WISHFUL_SETTLE_SECONDS)
    return None


def _wishful_open_blessings(bot) -> bool:
    if _wishful_panel_open(bot, attempts=1):
        return True
    found = _wishful_find_entry(bot)
    if found is None:
        bot.record("Gift Claims: Wishful Windmill không thấy icon Wind "
                   "Blessings hoặc các rương DONE 1 sau 5 lần; giữ PENDING")
        return False
    entry, entry_template, entry_threshold, entry_name = found
    bot.record("Gift Claims: Wishful Windmill chờ trang ổn định rồi tap "
               f"{entry_name}")
    bot.tap(*entry, delay=WISHFUL_SETTLE_SECONDS)
    opened = _wishful_panel_open(bot)
    if not opened:
        # A glow/animation can absorb the first tap on this event.  Retry only
        # after finding the same approved launcher again, so we never tap a
        # stale coordinate on a page that has already changed.
        entry = _wait_for(bot, entry_template, attempts=2,
                          threshold=entry_threshold, region=(0, 12, 100, 85),
                          delay=WISHFUL_SETTLE_SECONDS)
        if entry is not None:
            bot.record(f"Gift Claims: Wishful Windmill {entry_name} vẫn còn "
                       "sau cú tap đầu; tap lại đúng ảnh")
            bot.tap(*entry, delay=WISHFUL_SETTLE_SECONDS)
            opened = _wishful_panel_open(bot)
    if not opened:
        bot.record("Gift Claims: Wishful Windmill đã tap icon nhưng chưa thấy "
                   "title Wind Blessings; giữ PENDING")
    return opened


def _wishful_content_signature(screen):
    """Animation-tolerant signature limited to the supplied green frame."""
    height, width = screen.shape[:2]
    x0, y0, x1, y1 = WISHFUL_CONTENT_REGION
    patch = cv2.cvtColor(
        screen[int(height * y0 / 100):int(height * y1 / 100),
               int(width * x0 / 100):int(width * x1 / 100)],
        cv2.COLOR_BGR2GRAY,
    )
    tiny = cv2.resize(patch, (33, 16), interpolation=cv2.INTER_AREA)
    return np.packbits(tiny[:, 1:] > tiny[:, :-1]).tobytes()


def _wishful_content_distance(before, after) -> int:
    old = np.frombuffer(_wishful_content_signature(before), dtype=np.uint8)
    new = np.frombuffer(_wishful_content_signature(after), dtype=np.uint8)
    return int(np.unpackbits(np.bitwise_xor(old, new)).sum())


def _wishful_content_moved(before, after) -> bool:
    return _wishful_content_distance(before, after) > WISHFUL_SAME_DISTANCE


def _wishful_claims(bot, screen):
    """Only saturated-green Claim buttons, never the text inside Claimed."""
    return [pos for pos in find_all(
        bot, "EventCenter/WishfulWindmillFestival/button_claim", screen,
        threshold=0.74, region=WISHFUL_CLAIM_REGION)
        if _wishful_is_green_claim(screen, pos)]


def _wishful_claimed(bot, screen):
    return [pos for pos in find_all(
        bot, "EventCenter/WishfulWindmillFestival/status_claimed", screen,
        threshold=0.82, region=WISHFUL_CLAIM_REGION)
        if _wishful_is_gray_claimed(screen, pos)]


def _wishful_button_crop(screen, center, reference_size):
    scale = screen.shape[1] / 396
    width = max(1, round(reference_size[0] * scale))
    height = max(1, round(reference_size[1] * scale))
    left = max(0, center[0] - width // 2)
    top = max(0, center[1] - height // 2)
    return screen[top:min(screen.shape[0], top + height),
                  left:min(screen.shape[1], left + width)]


def _wishful_colour_ratios(crop) -> tuple[float, float]:
    """Return (green active-band ratio, low-saturation Claimed-band ratio)."""
    if crop.size == 0:
        return 0.0, 0.0
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    green = ((hsv[..., 0] >= 35) & (hsv[..., 0] <= 90) &
             (hsv[..., 1] >= 60) & (hsv[..., 2] >= 50))
    gray = ((hsv[..., 1] <= 70) & (hsv[..., 2] >= 50))
    return float(green.mean()), float(gray.mean())


def _wishful_is_green_claim(screen, center) -> bool:
    green, gray = _wishful_colour_ratios(
        _wishful_button_crop(screen, center, (70, 26)))
    return (green >= WISHFUL_GREEN_MIN_RATIO and
            gray < WISHFUL_ACTIVE_GRAY_MAX_RATIO)


def _wishful_is_gray_claimed(screen, center) -> bool:
    green, gray = _wishful_colour_ratios(
        _wishful_button_crop(screen, center, (77, 28)))
    return green <= 0.08 and gray >= WISHFUL_GRAY_MIN_RATIO


def _wishful_claimed_near(bot, screen, claim) -> bool:
    return any(abs(pos[0] - claim[0]) <= 50 and abs(pos[1] - claim[1]) <= 30
               for pos in _wishful_claimed(bot, screen))


def _wishful_done_one_limit(bot, screen) -> bool:
    """The claim-limit toast finishes Wind Blessings DONE 1 only."""
    template, threshold = WISHFUL_DONE_ONE_LIMIT
    return find(bot, template, screen, threshold=threshold,
                region=(0, 5, 100, 95)) is not None


def _wishful_done_one_no_records(bot, screen) -> bool:
    """``No Records`` inside the green panel is an immediate DONE 1 state."""
    template, threshold = WISHFUL_DONE_ONE_NO_RECORDS
    position = find(bot, template, screen, threshold=threshold,
                    region=WISHFUL_CONTENT_REGION)
    return isinstance(position, tuple) and len(position) == 2


def _close_wishful_congratulations(bot) -> bool:
    """Dismiss Congratulations by the user's fixed tap, never with Back."""
    for attempt in range(3):
        screen = bot.screenshot()
        common_popup = find(bot, CONGRATULATIONS, screen, threshold=0.78,
                            region=(0, 38, 100, 62))
        exact_popup = find(
            bot, "EventCenter/PreciousBlazonExchange/popup_congratulations", screen,
            threshold=0.72, region=(0, 35, 100, 65))
        if common_popup is not None or exact_popup is not None:
            height, width = screen.shape[:2]
            bot.record("Gift Claims: Wishful Windmill đóng Congratulations "
                       "bằng điểm cố định, giữ nguyên panel")
            bot.tap(round(width * 195 / 396), round(height * 20 / 704),
                    delay=WISHFUL_SETTLE_SECONDS)
            return True
        if attempt + 1 < 3:
            bot.sleep(WISHFUL_CONFIRMATION_DELAY_SECONDS)
    return False


def _tap_wishful_claim(bot, claim: tuple[int, int],
                       phase: str) -> tuple[int, bool, bool]:
    """Retry one Claim; third result is the special DONE-1 limit toast."""
    for tap_number in range(1, MAX_WISHFUL_TAPS_PER_CLAIM + 1):
        bot.record(f"Gift Claims: Wishful Windmill {phase} tap Claim "
                   f"lần {tap_number}/{MAX_WISHFUL_TAPS_PER_CLAIM} tại {claim}")
        bot.tap(*claim, delay=WISHFUL_SETTLE_SECONDS)
        # Screenshot_20261023-073771 is a short-lived toast.  Read the first
        # post-tap frame before waiting for/dismissing Congratulations.
        immediate = bot.screenshot()
        if phase == "DONE 1" and _wishful_done_one_limit(bot, immediate):
            bot.record("Gift Claims: Wishful Windmill DONE 1 thấy 'Claim "
                       "failed. The limit has been...'; DONE 1 ngay và chuyển "
                       "sang kiểm tra DONE 2")
            return tap_number, True, True
        if _wishful_claimed_near(bot, immediate, claim):
            bot.record(f"Gift Claims: Wishful Windmill {phase} Claim đã đổi "
                       "thành Claimed; DONE")
            return tap_number, True, True
        popup_closed = _close_wishful_congratulations(bot)
        bot.sleep(WISHFUL_CONFIRMATION_DELAY_SECONDS)
        after = bot.screenshot()
        if _wishful_claimed_near(bot, after, claim):
            bot.record(f"Gift Claims: Wishful Windmill {phase} xác nhận dòng "
                       "Claimed sau khi bấm; DONE")
            return tap_number, True, True
        nearby = next(
            (pos for pos in _wishful_claims(bot, after)
             if abs(pos[0] - claim[0]) <= 35 and
             abs(pos[1] - claim[1]) <= 30),
            None,
        )
        if popup_closed or nearby is None:
            return tap_number, True, False
        claim = nearby
        if tap_number < MAX_WISHFUL_TAPS_PER_CLAIM:
            bot.record(f"Gift Claims: Wishful Windmill {phase} Claim vẫn còn; "
                       "chờ rồi bấm lại ngay trong panel")
    return MAX_WISHFUL_TAPS_PER_CLAIM, False, False


def _claim_wishful_panel(bot, phase: str) -> tuple[ClaimReport, bool]:
    """Stay inside one Wind Blessings panel until its green frame has no Claim."""
    if not _wishful_panel_open(bot):
        bot.record(f"Gift Claims: Wishful Windmill {phase} chưa thấy title "
                   "Wind Blessings; giữ PENDING")
        return ClaimReport(), False

    # DONE 1 has two terminal paths.  ``No Records`` is the explicit empty
    # state and finishes immediately; otherwise the ordinary Claim scan below
    # runs to its confirmed bottom and also finishes once no Claim remains.
    if phase == "DONE 1" and _wishful_done_one_no_records(bot, bot.screenshot()):
        bot.record("Gift Claims: Wishful Windmill DONE 1 thấy 'No Records' "
                   "trong vùng xanh; DONE 1 ngay")
        return ClaimReport(0, 1), True

    attempted = verified = 0
    unresolved = False
    bottom_checks = 0
    position = 0
    while True:
        position += 1
        bot.record(f"Gift Claims: Wishful Windmill {phase} quét vùng xanh "
                   f"vị trí {position}")
        blocked_positions = []
        empty_checks = 0
        while attempted < MAX_WISHFUL_CLAIMS:
            bot.check()
            screen = bot.screenshot()
            claim = next(
                (pos for pos in _wishful_claims(bot, screen)
                 if all((pos[0] - old[0]) ** 2 + (pos[1] - old[1]) ** 2
                        > 30 ** 2 for old in blocked_positions)),
                None,
            )
            if claim is None:
                empty_checks += 1
                if empty_checks < EMPTY_POSITION_CHECKS:
                    bot.sleep(WISHFUL_CONFIRMATION_DELAY_SECONDS)
                    continue
                if _wishful_claimed(bot, screen):
                    bot.record(f"Gift Claims: Wishful Windmill {phase} khung "
                               "hiện tại chỉ có Claimed; chưa kết luận, lướt "
                               "tiếp hết vùng xanh")
                break

            empty_checks = 0
            taps, claim_verified, done_one_limit = _tap_wishful_claim(
                bot, claim, phase)
            attempted += taps
            if done_one_limit:
                verified += 1
                return ClaimReport(attempted, verified), True
            if claim_verified:
                verified += 1
                bot.record(f"Gift Claims: Wishful Windmill {phase} đã nhận "
                           "một Claim; tiếp tục ngay trong panel")
            else:
                unresolved = True
                blocked_positions.append(claim)
                bot.record(f"Gift Claims: Wishful Windmill {phase} Claim vẫn "
                           "còn sau khi bấm; bỏ đúng vị trí và tiếp tục quét")

        before = bot.screenshot()
        bot.record(f"Gift Claims: Wishful Windmill {phase} hết Claim trong "
                   "khung hiện tại; lướt chậm ở mép trái trong vùng xanh")
        bot.swipe_percent(*WISHFUL_SCAN_SWIPE,
                          duration=WISHFUL_SCROLL_DURATION_SECONDS,
                          delay=LIST_SCROLL_SETTLE_SECONDS)
        after = bot.screenshot()
        distance = _wishful_content_distance(before, after)
        if distance > WISHFUL_SAME_DISTANCE:
            bot.record(f"Gift Claims: Wishful Windmill {phase} vùng xanh "
                       f"đã di chuyển, Hamming {distance}/{WISHFUL_SAME_DISTANCE}")
            bottom_checks = 0
            continue
        bottom_checks += 1
        bot.record(f"Gift Claims: Wishful Windmill {phase} vùng xanh không "
                   f"di chuyển, Hamming {distance}/{WISHFUL_SAME_DISTANCE} "
                   f"({bottom_checks}/{WISHFUL_EDGE_CONFIRMATIONS})")
        if bottom_checks < WISHFUL_EDGE_CONFIRMATIONS:
            continue
        remaining = _wishful_claims(bot, after)
        done = not remaining and not unresolved
        if done:
            bot.record(f"Gift Claims: Wishful Windmill {phase} đã lướt hết "
                       "vùng xanh và không còn Claim; DONE")
        else:
            bot.record(f"Gift Claims: Wishful Windmill {phase} vẫn còn Claim "
                       "chưa xác minh; giữ PENDING")
        return ClaimReport(attempted, max(verified, int(done))), done

    return ClaimReport(attempted, verified), False


def _claim_wishful_done_two_chest(bot) -> tuple[ClaimReport, bool]:
    """Finish DONE 2 from the outer chest after the full green-panel scan.

    No chest in the measured outer region is also terminal: Challenge Quest
    was already scanned to its confirmed edge, so there is no remaining outer
    reward to collect.  A chest which *is* visible is repeatedly found again
    and tapped until it disappears.  A Congratulations popup is closed, but
    is not sufficient by itself: the outer region is checked again before
    DONE 2 is accepted.
    """
    template, threshold = WISHFUL_DONE_TWO_CHEST
    chest = _wait_for(
        bot, template, attempts=5, threshold=threshold,
        region=WISHFUL_DONE_TWO_CHEST_REGION,
        delay=WISHFUL_SETTLE_SECONDS,
    )
    if chest is None:
        bot.record("Gift Claims: Wishful Windmill đã quét xong Claim DONE 2 "
                   "và không có rương ngoài để nhận; DONE")
        return ClaimReport(0, 1), True
    attempted = 0
    while chest is not None:
        # There is deliberately no tap-count ceiling here.  A live chest is
        # a pending reward, not a reason to conclude DONE/PENDING and leave
        # it behind.  BotContext.check() still yields safely at the worker's
        # normal 120-second/boss boundary.
        bot.check()
        attempted += 1
        bot.record(f"Gift Claims: Wishful Windmill thấy rương cuối tại {chest}; "
                   f"tap ({attempted})")
        bot.tap(*chest, delay=WISHFUL_SETTLE_SECONDS)
        saw_congratulations = close_congratulations(
            bot, attempts=8, region=(0, 18, 100, 65))
        chest = _wait_for(
            bot, template, attempts=3, threshold=threshold,
            region=WISHFUL_DONE_TWO_CHEST_REGION,
            delay=WISHFUL_SETTLE_SECONDS,
        )
        if chest is None:
            if saw_congratulations:
                bot.record("Gift Claims: Wishful Windmill rương cuối đã hiện "
                           "Congratulations và biến mất; DONE")
            else:
                bot.record("Gift Claims: Wishful Windmill rương cuối đã biến "
                           "mất khỏi đúng vùng; DONE")
            return ClaimReport(attempted, 1), True
        bot.record("Gift Claims: Wishful Windmill rương cuối vẫn còn; tìm lại "
                   "đúng ảnh và tap tiếp")

    # Kept for static type checkers; the loop returns when chest becomes None.
    return ClaimReport(attempted, 1), True


def _wait_event_row_open(bot, expected_screen=None, *, delay=UI_SETTLE_SECONDS):
    """Wait through Event Center transition frames after selecting one row.

    ``identify`` legitimately returns ``None`` while the new page is painting;
    that is not proof that navigation finished.  Forced rows wait for their
    exact captured title.  Generic red rows accept any identified non-list
    Event Center page.
    """
    actual = None
    for attempt in range(5):
        actual = identify(bot)
        if expected_screen is not None and actual == expected_screen:
            return actual
        if (expected_screen is None
                and actual not in (None, GiftScreen.EVENT_CENTER)):
            return actual
        if (expected_screen is not None
                and actual not in (None, GiftScreen.EVENT_CENTER,
                                   expected_screen)):
            return actual
        if attempt < 4:
            bot.sleep(delay)
    return actual


def _handle_wishful(bot):
    bot.record("Gift Claims: Wishful Windmill tìm và tap rương ngay; "
               "mỗi thao tác chỉ chờ 1s; chỉ nhận Claim, không "
               "dùng Claim All")
    if not _wishful_open_blessings(bot):
        return ClaimReport(), False
    first, first_done = _claim_wishful_panel(bot, "DONE 1")
    if not first_done:
        return first, False

    # Leave the completed child panel once, then keep the second panel open
    # until every Challenge Quest Claim is exhausted.
    bot.back(delay=WISHFUL_SETTLE_SECONDS)
    storage = _wait_for(bot, "EventCenter/WishfulWindmillFestival/tab_wind_power_storage",
                        attempts=5, threshold=0.68, region=(0, 5, 100, 25),
                        delay=WISHFUL_SETTLE_SECONDS)
    if storage is None:
        bot.record("Gift Claims: Wishful Windmill chưa thấy tab Wind Power "
                   "Storage; giữ PENDING")
        return first, False
    bot.record("Gift Claims: Wishful Windmill tap Wind Power Storage")
    bot.tap(*storage, delay=WISHFUL_SETTLE_SECONDS)
    challenge = _wait_for(bot, "EventCenter/WishfulWindmillFestival/button_challenge_quest",
                          attempts=5, threshold=0.68,
                          region=(0, 10, 100, 95),
                          delay=WISHFUL_SETTLE_SECONDS)
    if challenge is None:
        bot.record("Gift Claims: Wishful Windmill chưa thấy Challenge Quest; "
                   "giữ PENDING")
        return first, False
    bot.record("Gift Claims: Wishful Windmill tap Challenge Quest")
    bot.tap(*challenge, delay=WISHFUL_SETTLE_SECONDS)
    second, second_done = _claim_wishful_panel(bot, "Challenge Quest")
    total = ClaimReport(first.attempted + second.attempted,
                        first.verified + second.verified)
    if not second_done:
        return total, False

    # A DONE-2 panel is never terminal by itself.  Whether it contained new
    # Claims or only Claimed rows, first finish the full green-frame scan,
    # then return to Wind Power Storage and claim the Wishful chest.
    bot.record("Gift Claims: Wishful Windmill Challenge Quest đã quét hết "
               "Claim; Back ra ngoài nhận rương trước DONE 2")
    bot.back(delay=WISHFUL_SETTLE_SECONDS)
    chest, chest_done = _claim_wishful_done_two_chest(bot)
    return ClaimReport(total.attempted + chest.attempted,
                       total.verified + chest.verified), chest_done


def _apple_done_ornament_matches(screen, template, center) -> tuple[bool, tuple[float, float]]:
    """Require both dark ornamental side borders of an Apple DONE control."""
    height, width = template.shape[:2]
    # ScreenMixin.best_match() reports ``top_left + size // 2``. Reverse that
    # exact integer operation here. ``round(center - size / 2)`` is wrong for
    # odd-sized Apple templates (111 px wide): depending on coordinate parity
    # banker's rounding shifts the ornamental border by one pixel and turns an
    # exact DONE match into false border scores around 0.1-0.3.
    left = center[0] - width // 2
    top = center[1] - height // 2
    right, bottom = left + width, top + height
    if left < 0 or top < 0 or right > screen.shape[1] or bottom > screen.shape[0]:
        return False, (0.0, 0.0)
    patch = screen[top:bottom, left:right]
    border = max(4, round(width * APPLE_ORNAMENT_WIDTH_RATIO))

    def score(actual, expected):
        if actual.shape != expected.shape or actual.size == 0:
            return 0.0
        return float(cv2.matchTemplate(
            actual, expected, cv2.TM_CCOEFF_NORMED)[0, 0])

    scores = (score(patch[:, :border], template[:, :border]),
              score(patch[:, -border:], template[:, -border:]))
    return min(scores) >= APPLE_ORNAMENT_THRESHOLD, scores


def _apple_button_color_band(screen, center) -> tuple[float, float]:
    """Return (mean HSV saturation, saturated-pixel ratio) near button centre.

    The supplied active buttons have a yellow/orange band around S=199..210
    with over 75% strongly saturated pixels.  The disabled ornamental buttons
    are grey around S=24..27 with under 8%.  Sampling the common 70x24 centre
    strip is therefore much more stable than comparing their shared wording.
    """
    scale_x = screen.shape[1] / 396
    scale_y = screen.shape[0] / 704
    half_width = max(8, round(35 * scale_x))
    half_height = max(4, round(12 * scale_y))
    left = max(0, center[0] - half_width)
    right = min(screen.shape[1], center[0] + half_width)
    top = max(0, center[1] - half_height)
    bottom = min(screen.shape[0], center[1] + half_height)
    patch = screen[top:bottom, left:right]
    if patch.size == 0:
        return 0.0, 0.0
    saturation = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)[..., 1]
    return (float(saturation.mean()),
            float(np.mean(saturation >= APPLE_COLOR_SATURATION_CUTOFF)))


def _apple_once_states_for_multiplier(active: str):
    """Exact Once states that must not satisfy a multiplier template."""
    if active in (
            "EventCenter/DwarfsLuckyApple/button_green_wish_x100",
            "EventCenter/DwarfsLuckyApple/button_green_wish_x10"):
        return APPLE_GREEN_ONCE_STATES
    if active == "EventCenter/DwarfsLuckyApple/button_red_wish_x10":
        return APPLE_RED_ONCE_STATES
    return ()


def _apple_multiplier_is_once(bot, screen, active: str, position,
                              *, region) -> bool:
    """Whether ``position`` is an exact Wish Once control, not x100/x10."""
    if position is None:
        return False
    for template_name, _threshold in _apple_once_states_for_multiplier(active):
        template = _scaled_template(bot, template_name, screen)
        score, once_position = bot.best_match(template, screen=screen,
                                              region=region)
        if (once_position is None or
                score < APPLE_ONCE_EXCLUSION_THRESHOLD):
            continue
        distance_sq = ((position[0] - once_position[0]) ** 2 +
                       (position[1] - once_position[1]) ** 2)
        if distance_sq <= APPLE_ONCE_EXCLUSION_DISTANCE ** 2:
            bot.record("Gift Claims: Dwarf's Lucky Apple template multiplier "
                       f"đang khớp vào Wish Once ({template_name}, "
                       f"score={score:.3f}, vị trí={once_position}); loại "
                       "kết quả để không bấm nhầm")
            return True
    return False


def _apple_button_state(bot, screen, active: str, finished: str,
                        region=(0, 15, 100, 98), *, exclude_once=False):
    """Distinguish the orange active button from the grey disabled button.

    Their wording and coin icon are nearly identical, so testing the disabled
    template first with a loose threshold can classify an active orange button
    as DONE. Compare both full-colour scores from the same frame instead. DONE
    must beat the active score by a visible margin; an ambiguous result is
    deliberately treated as active/PENDING rather than completed.
    """
    active_template = _scaled_template(bot, active, screen)
    done_template = _scaled_template(bot, finished, screen)
    active_score, active_pos = bot.best_match(
        active_template, screen=screen, region=region)
    done_score, done_pos = bot.best_match(
        done_template, screen=screen, region=region)
    active_color = (_apple_button_color_band(screen, active_pos)
                    if active_pos is not None else (0.0, 0.0))
    done_color = (_apple_button_color_band(screen, done_pos)
                  if done_pos is not None else (0.0, 0.0))
    bot.record(f"Gift Claims: Dwarf's Lucky Apple dải màu "
               f"ACTIVE score={active_score:.3f} tại {active_pos}, S={active_color[0]:.1f}, "
               f"tỷ lệ vàng={active_color[1]:.2f}; DONE score={done_score:.3f}, "
               f"tại {done_pos}, S={done_color[0]:.1f}, tỷ lệ vàng={done_color[1]:.2f}")

    active_is_once = (exclude_once and
                      _apple_multiplier_is_once(bot, screen, active,
                                                 active_pos, region=region))
    done_is_once = (exclude_once and
                    _apple_multiplier_is_once(bot, screen, active,
                                               done_pos, region=region))

    done_is_gray = (done_color[0] <= APPLE_DONE_SATURATION_MAX and
                    done_color[1] <= APPLE_DONE_COLOR_RATIO_MAX)
    if (done_pos is not None and done_score >= APPLE_STATE_THRESHOLD
            and done_is_gray and not done_is_once):
        ornament_ok, ornament_scores = _apple_done_ornament_matches(
            screen, done_template, done_pos)
        bot.record("Gift Claims: Dwarf's Lucky Apple kiểm tra hoa văn DONE "
                   f"trái={ornament_scores[0]:.3f}, "
                   f"phải={ornament_scores[1]:.3f} -> "
                   f"{'đạt' if ornament_ok else 'không đạt'}")
        if ornament_ok:
            return "done", done_pos
        bot.record("Gift Claims: ảnh giống DONE nhưng thiếu viền hoa văn; "
                   "không được kết luận DONE")

    # Both templates share the same text and coin icon.  Use whichever one
    # locates that control most strongly, then let its yellow colour band
    # decide ACTIVE. This handles animation frames where the active-template
    # score falls while the visually wrong grey template scores near 1.0.
    candidates = [(active_score, active_pos, active_color),
                  (done_score, done_pos, done_color)]
    locate_score, locate_pos, locate_color = max(
        candidates, key=lambda candidate: candidate[0])
    active_is_yellow = (
        locate_color[0] >= APPLE_ACTIVE_SATURATION_MIN and
        locate_color[1] >= APPLE_ACTIVE_COLOR_RATIO_MIN)
    if (locate_pos is not None and
            locate_score >= APPLE_COLOR_LOCATE_THRESHOLD and
            active_is_yellow and not (active_is_once if locate_pos == active_pos
                                       else done_is_once)):
        bot.record("Gift Claims: Dwarf's Lucky Apple dải vàng đạt chuẩn; "
                   "xác nhận nút ACTIVE và tiếp tục bấm")
        return "active", locate_pos
    # A live account can render the already-pressed x100/x10 control with a
    # slightly different border/crop from the supplied DONE template.  In the
    # failing layout the shared button artwork still locates the exact control
    # reliably (for example ACTIVE=0.742), while the DONE crop scores only
    # about 0.56.  Its colour band is nevertheless unambiguously grey
    # (S~26, saturated ratio~0.07).  Treat that state as DONE instead of
    # leaving the phase in an endless unreadable-frame loop.  Yellow always
    # wins above, so an actionable control cannot enter this branch.
    located_is_gray = (
        locate_color[0] <= APPLE_DONE_SATURATION_MAX and
        locate_color[1] <= APPLE_DONE_COLOR_RATIO_MAX)
    if (locate_pos is not None and
            locate_score >= APPLE_COLOR_LOCATE_THRESHOLD and
            located_is_gray and not (active_is_once if locate_pos == active_pos
                                      else done_is_once)):
        bot.record("Gift Claims: Dwarf's Lucky Apple đã định vị đúng nút và "
                   "dải màu đã xám; xác nhận DONE không chờ template/hoa văn")
        return "done", locate_pos
    if done_pos is not None and done_score >= APPLE_STATE_THRESHOLD:
        bot.record("Gift Claims: Dwarf's Lucky Apple ảnh gần DONE nhưng dải "
                   "màu chưa đủ xám; chờ frame ổn định")
    return None, None


def _apple_red_x10_post_tap_done(bot, screen) -> bool:
    """Recognize the live red-x10 grey layout after a verified active tap.

    On that layout the yellow Once control wins the ACTIVE-template search,
    while the real grey x10 only scores about 0.50 against the older DONE
    crop.  This fallback is called only after this run positively recognized
    and tapped red x10; it additionally requires an exact red Once state and
    a grey colour band at the weak x10 match.
    """
    red_once = _apple_special_state(
        bot, screen, APPLE_RED_ONCE_STATES,
        "Wish Once táo đỏ sau khi đã bấm x10")
    if red_once is None:
        return False

    # The live terminal layout can remove x10 completely and leave only Wish
    # Once. The x10 ACTIVE template then weakly matches that remaining control
    # (0.449 in the supplied frame). Do not mistake it for a separate x10: a
    # genuinely actionable x10 is yellow and spatially distinct from Once.
    active = "EventCenter/DwarfsLuckyApple/button_red_wish_x10"
    active_template = _scaled_template(bot, active, screen)
    active_score, active_pos = bot.best_match(
        active_template, screen=screen, region=(0, 15, 100, 98))
    if active_pos is not None:
        active_saturation, active_color_ratio = _apple_button_color_band(
            screen, active_pos)
        once_pos = red_once[1]
        distance_sq = ((active_pos[0] - once_pos[0]) ** 2 +
                       (active_pos[1] - once_pos[1]) ** 2)
        active_is_yellow = (
            active_saturation >= APPLE_ACTIVE_SATURATION_MIN and
            active_color_ratio >= APPLE_ACTIVE_COLOR_RATIO_MIN)
        if (active_score >= APPLE_COLOR_LOCATE_THRESHOLD and
                active_is_yellow and
                distance_sq > APPLE_RED_X10_DISTINCT_DISTANCE ** 2):
            bot.record("Gift Claims: Dwarf's Lucky Apple vẫn thấy một nút "
                       "đỏ x10 vàng tách biệt với Wish Once; tiếp tục pha")
            return False

    finished = "EventCenter/DwarfsLuckyApple/status_red_wish_x10_done"
    done_template = _scaled_template(bot, finished, screen)
    done_score, done_pos = bot.best_match(
        done_template, screen=screen, region=(0, 15, 100, 98))
    if (done_pos is not None and
            done_score >= APPLE_RED_POST_TAP_GRAY_LOCATE_THRESHOLD):
        saturation, color_ratio = _apple_button_color_band(screen, done_pos)
        if (saturation <= APPLE_DONE_SATURATION_MAX and
                color_ratio <= APPLE_DONE_COLOR_RATIO_MAX):
            bot.record("Gift Claims: Dwarf's Lucky Apple đỏ x10 sau tap đã "
                       f"xám (score={done_score:.3f}, S={saturation:.1f}, "
                       f"tỷ lệ màu={color_ratio:.2f}) và còn Wish Once; "
                       "xác nhận DONE")
            return True

    bot.record("Gift Claims: Dwarf's Lucky Apple đã từng bấm đỏ x10, hiện "
               "chỉ còn Wish Once và không còn x10 vàng tách biệt; DONE")
    return True


def _apple_red_multipliers_gray(bot) -> bool:
    """DONE when the red tab simultaneously shows grey Wish x100 and x10.

    These two terminal controls are checked on one frame and must be spatially
    distinct.  This prevents the very similar button ornaments from allowing
    one grey control to satisfy both templates.
    """
    screen = bot.screenshot()
    if not isinstance(screen, np.ndarray) or screen.ndim < 2:
        return False
    hits = []
    for label, template_name in (
            ("x100", "EventCenter/DwarfsLuckyApple/status_red_wish_x100_done"),
            ("x10", "EventCenter/DwarfsLuckyApple/status_red_wish_x10_done")):
        template = _scaled_template(bot, template_name, screen)
        result = bot.best_match(template, screen=screen,
                                region=(0, 15, 100, 98))
        if (not isinstance(result, tuple) or len(result) != 2
                or not isinstance(result[0], (int, float))
                or not isinstance(result[1], tuple)):
            return False
        score, position = result
        saturation, color_ratio = _apple_button_color_band(screen, position)
        gray = (saturation <= APPLE_DONE_SATURATION_MAX and
                color_ratio <= APPLE_DONE_COLOR_RATIO_MAX)
        bot.record("Gift Claims: Dwarf's Lucky Apple táo đỏ kiểm tra Wish "
                   f"{label} xám: score={score:.3f}, S={saturation:.1f}, "
                   f"tỷ lệ màu={color_ratio:.2f}")
        if score < APPLE_RED_MULTIPLIER_DONE_THRESHOLD or not gray:
            return False
        hits.append(position)
    distance_sq = ((hits[0][0] - hits[1][0]) ** 2 +
                   (hits[0][1] - hits[1][1]) ** 2)
    if distance_sq <= APPLE_RED_MULTIPLIER_DISTINCT_DISTANCE ** 2:
        bot.record("Gift Claims: ảnh đỏ x100/x10 xám trùng cùng một vị trí; "
                   "không kết luận DONE")
        return False
    bot.record("Gift Claims: táo đỏ thấy đồng thời Wish x100 và Wish x10 đều "
               "màu xám ở hai vị trí riêng; DONE toàn nhiệm vụ")
    return True


def _apple_green_multipliers_gray(bot) -> bool:
    """True when the supplied green x100 and x10 controls are both grey.

    The two controls must be visible in the same stable frame, pass their
    exact template thresholds, have a grey colour band, and occupy separate
    positions.  This is a phase-transition signal only: it means there is
    nothing left to do on the green apple, so the caller must continue with
    the red apple rather than waiting for a separate Wish Once control.
    """
    screen = bot.screenshot()
    if not isinstance(screen, np.ndarray) or screen.ndim < 2:
        return False
    hits = []
    for label, template_name in (
            ("x100", "EventCenter/DwarfsLuckyApple/status_green_wish_x100_done"),
            ("x10", "EventCenter/DwarfsLuckyApple/status_green_wish_x10_done")):
        template = _scaled_template(bot, template_name, screen)
        result = bot.best_match(template, screen=screen,
                                region=(0, 15, 100, 98))
        if (not isinstance(result, tuple) or len(result) != 2
                or not isinstance(result[0], (int, float))
                or not isinstance(result[1], tuple)):
            return False
        score, position = result
        saturation, color_ratio = _apple_button_color_band(screen, position)
        gray = (saturation <= APPLE_DONE_SATURATION_MAX and
                color_ratio <= APPLE_DONE_COLOR_RATIO_MAX)
        bot.record("Gift Claims: Dwarf's Lucky Apple táo xanh kiểm tra Wish "
                   f"{label} xám: score={score:.3f}, S={saturation:.1f}, "
                   f"tỷ lệ màu={color_ratio:.2f}")
        if score < APPLE_RED_MULTIPLIER_DONE_THRESHOLD or not gray:
            return False
        hits.append(position)
    distance_sq = ((hits[0][0] - hits[1][0]) ** 2 +
                   (hits[0][1] - hits[1][1]) ** 2)
    if distance_sq <= APPLE_RED_MULTIPLIER_DISTINCT_DISTANCE ** 2:
        bot.record("Gift Claims: ảnh xanh x100/x10 xám trùng cùng một vị trí; "
                   "không chuyển tab")
        return False
    bot.record("Gift Claims: táo xanh thấy đồng thời Wish x100 và Wish x10 "
               "đều xám ở hai vị trí riêng")
    return True


def _apple_congratulations_hit(bot, screen):
    """Return a Lucky Apple popup match without taking a second screenshot."""
    for template in (CONGRATULATIONS,
                     "EventCenter/PreciousBlazonExchange/popup_congratulations"):
        hit = find(bot, template, screen, threshold=0.78,
                   region=(0, 35, 100, 65))
        if hit is not None:
            return hit
    return None


def _close_apple_congratulations(bot, attempts=3,
                                 *, safe_tap_after_reward=False) -> bool:
    """Dismiss Lucky Apple Congratulations at the approved fixed top point.

    Back can close the entire Dwarf's Lucky Apple page on this event.  The
    fixed point (195, 20) is in the safe title ribbon, outside every reward
    control, and keeps the current green/red phase open.
    """
    for attempt in range(attempts):
        screen = bot.screenshot()
        hit = _apple_congratulations_hit(bot, screen)
        if hit is not None:
            bot.record("Gift Claims: Dwarf's Lucky Apple tap cố định (195, 20) "
                       "để đóng Congratulations; không dùng Back")
            bot.tap(195, 20, delay=UI_SETTLE_SECONDS)
            return True
        if attempt + 1 < attempts:
            bot.sleep(UI_SETTLE_SECONDS)
    if safe_tap_after_reward:
        # The Congratulations artwork fades/animates and occasionally misses
        # both templates on overloaded multi-device hosts. This call is made
        # only immediately after tapping a verified Apple reward button. The
        # approved title coordinate is harmless without a popup and guarantees
        # that a visually present but unmatched popup is dismissed.
        bot.record("Gift Claims: Dwarf's Lucky Apple không bắt được ảnh "
                   "Congratulations sau nút nhận; vẫn tap an toàn (195, 20)")
        bot.tap(195, 20, delay=UI_SETTLE_SECONDS)
        return True
    return False


def _apple_special_state(bot, screen, variants, label: str):
    """Return an exact user-supplied Apple shortcut state on this frame."""
    for template, threshold in variants:
        position = find(bot, template, screen, threshold=threshold,
                        region=(0, 15, 100, 98))
        if isinstance(position, tuple) and len(position) == 2:
            bot.record(f"Gift Claims: Dwarf's Lucky Apple thấy {label} "
                       f"({template}, ngưỡng {threshold:.2f})")
            return template, position
    return None


def _wait_apple_special_state(bot, variants, label: str, *, attempts=2):
    for attempt in range(attempts):
        state = _apple_special_state(bot, bot.screenshot(), variants, label)
        if state is not None:
            return state
        if attempt + 1 < attempts:
            bot.sleep(UI_SETTLE_SECONDS)
    return None


def _apple_phase(bot, active: str, finished: str,
                 *, max_taps=MAX_APPLE_TAPS_PER_PHASE):
    """Continuously tap one Lucky Apple phase until its disabled state.

    A short fade/animation must not eject the task between taps. Unreadable
    frames are retried in-place; only the worker's 120-second deadline may
    interrupt the phase and resume it later.
    """
    attempted = 0
    missing_frames = 0
    wrong_page_frames = 0
    while attempted < max_taps:
        bot.check()
        screen = bot.screenshot()
        # Never compare ACTIVE/DONE against a frame still covered by the
        # Congratulations overlay. Dismiss it, wait one full UI interval,
        # and obtain a fresh frame on the next loop iteration.
        if _apple_congratulations_hit(bot, screen) is not None:
            bot.record("Gift Claims: Dwarf's Lucky Apple còn Congratulations; "
                       f"đóng popup và chờ {UI_SETTLE_SECONDS:g}s trước khi "
                       "nhận dạng DONE/ACTIVE")
            _close_apple_congratulations(bot, attempts=1)
            bot.sleep(UI_SETTLE_SECONDS)
            continue
        if (attempted > 0 and
                active == "EventCenter/DwarfsLuckyApple/button_red_wish_x10" and
                _apple_red_x10_post_tap_done(bot, screen)):
            return ClaimReport(attempted, attempted), True
        state, button = _apple_button_state(bot, screen, active, finished,
                                            exclude_once=True)
        if state == "done":
            return ClaimReport(attempted, attempted), True
        if state != "active" or button is None:
            missing_frames += 1
            if identify(bot, screen) != GiftScreen.DWARFS_LUCKY_APPLE:
                wrong_page_frames += 1
                bot.record("Gift Claims: Dwarf's Lucky Apple không còn thấy "
                           "title trang hiện tại "
                           f"({wrong_page_frames}/{APPLE_STATE_MISS_RETRIES})")
                if wrong_page_frames >= APPLE_STATE_MISS_RETRIES:
                    bot.record("Gift Claims: Dwarf's Lucky Apple đã rời trang; "
                               "dừng PENDING thay vì đọc nút trên màn khác")
                    return ClaimReport(attempted, 0), False
            else:
                wrong_page_frames = 0
            bot.record(f"Gift Claims: Dwarf's Lucky Apple chưa đọc được trạng "
                       f"thái pha hiện tại (lần {missing_frames}); chờ rồi "
                       "kiểm tra lại nút")
            if missing_frames % APPLE_STATE_MISS_RETRIES == 0:
                bot.record("Gift Claims: Dwarf's Lucky Apple vẫn ở nguyên "
                           "trang để đọc lại; không chuyển PENDING/không Back")
            bot.sleep(UI_SETTLE_SECONDS)
            continue
        missing_frames = 0
        wrong_page_frames = 0
        attempted += 1
        bot.record(f"Gift Claims: Dwarf's Lucky Apple tap {active} "
                   f"({attempted}/{max_taps})")
        bot.tap(*button, delay=UI_SETTLE_SECONDS)
        # Wait for a late Congratulations, but never tap the title merely
        # because an overloaded device did not render the popup. The next
        # loop still checks ACTIVE/DONE and presses ACTIVE again when needed.
        _close_apple_congratulations(bot, attempts=3)
        # Keep recognition separate from the tap/animation delay. The next
        # ACTIVE/DONE comparison must use a stable post-popup frame.
        bot.sleep(UI_SETTLE_SECONDS)
    bot.record(f"Gift Claims: Dwarf's Lucky Apple chạm giới hạn an toàn "
               f"{max_taps} lần ở một pha; giữ PENDING")
    return ClaimReport(attempted, 0), False


def _probe_optional_apple_phase(bot, active: str, finished: str,
                                label: str, *, attempts=3):
    """Read an optional x100/x10 phase without confusing absence with DONE.

    The Lucky Apple layout changes by account: some accounts expose x100,
    x10 and Once while others expose only x10 + Once or Once.  A bounded
    probe tells the caller whether this phase is present.  Once is deliberately
    *not* checked here, because it may coexist with an actionable x100/x10.
    """
    for attempt in range(attempts):
        bot.check()
        screen = bot.screenshot()
        if _apple_congratulations_hit(bot, screen) is not None:
            _close_apple_congratulations(bot, attempts=1)
            bot.sleep(UI_SETTLE_SECONDS)
            continue
        state, _button = _apple_button_state(bot, screen, active, finished,
                                              exclude_once=True)
        if state is not None:
            bot.record("Gift Claims: Dwarf's Lucky Apple "
                       f"{label} xuất hiện ({state.upper()})")
            return state
        if attempt + 1 < attempts:
            bot.sleep(UI_SETTLE_SECONDS)
    bot.record("Gift Claims: Dwarf's Lucky Apple "
               f"không có {label} sau {attempts} lần kiểm tra")
    return None


def _run_optional_apple_phase(bot, active: str, finished: str, label: str):
    """Finish a visible x phase, or skip it only when it is truly absent."""
    state = _probe_optional_apple_phase(bot, active, finished, label)
    if state is None:
        return ClaimReport(), True, False
    if state == "done":
        return ClaimReport(), True, True
    report, done = _apple_phase(bot, active, finished)
    return report, done, True


def _handle_dwarfs_lucky_apple(bot):
    """Finish every visible multiplier before using Once as a transition."""
    deadline = getattr(bot, "_deadline", None)
    if isinstance(deadline, (int, float)):
        remaining = max(0, round(deadline - time.monotonic()))
        bot.record("Gift Claims: Dwarf's Lucky Apple thuộc Event Center/"
                   f"Activities; deadline worker còn {remaining}s, hết giờ sẽ "
                   "nhường Join Monster War")
    else:
        bot.record("Gift Claims: Dwarf's Lucky Apple thuộc Event Center/"
                   "Activities; lượt này không có deadline 120s (Join Boss "
                   "không hoạt động hoặc đang chờ thể lực)")
    # The page artwork and buttons fade in after the title is already visible.
    # Always begin from the green tab.  Never probe the red DONE template on
    # the initial/default page: a grey green-x10 state has nearly identical
    # wording and could otherwise shortcut the whole task as completed.
    bot.sleep(UI_SETTLE_SECONDS)
    green = _wait_for_any(
        bot,
        ("EventCenter/DwarfsLuckyApple/tab_green_apple",
         "EventCenter/DwarfsLuckyApple/tab_green_apple_1"),
        attempts=4, threshold=0.70, region=(45, 40, 100, 68))
    if green is None:
        bot.record("Gift Claims: Dwarf's Lucky Apple không nhận diện được "
                   "cả hai ảnh tab táo xanh; giữ PENDING")
        return ClaimReport(), False
    bot.tap(*green, delay=UI_SETTLE_SECONDS)

    if _apple_green_multipliers_gray(bot):
        # The user-supplied grey x100 (500) + x10 (50) images are already a
        # complete green-phase proof.  Do not wait for Wish Once, which may be
        # absent in this terminal layout; go directly to the red phase.
        total = ClaimReport()
        bot.record("Gift Claims: hai Wish táo xanh đã xám; chuyển ngay sang "
                   "táo đỏ để kiểm tra tiếp")
    else:
        first, first_done, first_present = _run_optional_apple_phase(
            bot, "EventCenter/DwarfsLuckyApple/button_green_wish_x100",
            "EventCenter/DwarfsLuckyApple/status_green_wish_x100_done", "xanh x100")
        if not first_done:
            return first, False

        second, second_done, second_present = _run_optional_apple_phase(
            bot, "EventCenter/DwarfsLuckyApple/button_green_wish_x10",
            "EventCenter/DwarfsLuckyApple/status_green_wish_x10_done", "xanh x10")
        if not second_done:
            total = ClaimReport(first.attempted + second.attempted,
                                first.verified + second.verified)
            return total, False
        total = ClaimReport(first.attempted + second.attempted,
                            first.verified + second.verified)
        green_once = _wait_apple_special_state(
            bot, APPLE_GREEN_ONCE_STATES,
            "Wish Once táo xanh sau khi xử lý hết x100/x10", attempts=3)
        if green_once is None:
            bot.record("Gift Claims: Dwarf's Lucky Apple chưa thấy Wish Once táo "
                       "xanh sau khi kiểm tra x100/x10; giữ nguyên trang để lượt "
                       "sau kiểm tra lại")
            return total, False
        visible = []
        if first_present:
            visible.append("x100")
        if second_present:
            visible.append("x10")
        bot.record("Gift Claims: Dwarf's Lucky Apple nhánh xanh đã xử lý xong "
                   f"{', '.join(visible) if visible else 'chỉ có Once'}; "
                   "chuyển sang táo đỏ")

    red = _wait_for_any(
        bot,
        ("EventCenter/DwarfsLuckyApple/tab_red_apple",
         "EventCenter/DwarfsLuckyApple/tab_red_apple_1"),
        attempts=4, threshold=0.70, region=(0, 40, 55, 68))
    if red is None:
        bot.record("Gift Claims: Dwarf's Lucky Apple không nhận diện được "
                   "cả hai ảnh tab táo đỏ; giữ PENDING")
        return total, False
    bot.record("Gift Claims: Dwarf's Lucky Apple bấm tab táo đỏ; chỉ từ "
               "thời điểm này mới được xét DONE toàn nhiệm vụ")
    bot.tap(*red, delay=UI_SETTLE_SECONDS)
    # A grey red x10 is the primary terminal state.  Check it before every
    # shortcut involving Wish Once: Once may coexist with x10, and looking at
    # it earlier would incorrectly skip an already exhausted multiplier.
    third, third_done, third_present = _run_optional_apple_phase(
        bot, "EventCenter/DwarfsLuckyApple/button_red_wish_x10",
        "EventCenter/DwarfsLuckyApple/status_red_wish_x10_done", "đỏ x10")
    final = ClaimReport(total.attempted + third.attempted,
                        total.verified + third.verified)
    if third_present and third_done:
        bot.record("Gift Claims: Dwarf's Lucky Apple đỏ x10 đã hiện trạng "
                   "thái DONE; hoàn thành toàn bộ nhiệm vụ")
        return final, True
    if not third_done:
        return final, False

    # x10 was not readable/present in the regular phase probe.  Retain the
    # stricter two-control visual fallback for the supplied grey x100+x10
    # layout before considering the Once-only terminal state.
    if _apple_red_multipliers_gray(bot):
        return ClaimReport(final.attempted, max(1, final.verified)), True

    # Red x10 is genuinely absent.  Only now may Once (active or grey) finish
    # the task; checking it earlier would incorrectly skip an actionable x10.
    red_once = _wait_apple_special_state(
        bot, APPLE_RED_ONCE_STATES,
        "Wish Once táo đỏ khi không có x10; DONE toàn nhiệm vụ", attempts=3)
    if red_once is not None:
        bot.record("Gift Claims: Dwarf's Lucky Apple táo đỏ chỉ có Wish Once "
                   "(màu vàng hoặc xám); DONE toàn nhiệm vụ")
        return ClaimReport(final.attempted, max(1, final.verified)), True
    bot.record("Gift Claims: Dwarf's Lucky Apple không thấy đỏ x10 hoặc Wish "
               "Once sau 3 lần; giữ PENDING để tránh kết luận nhầm")
    return final, False


def _eagle_active_claims(bot, screen):
    """Return Claim buttons without confusing the prefix in ``Claimed``.

    OpenCV template matching quite correctly finds the shorter word Claim
    inside the longer word Claimed.  A captured Claimed marker therefore owns
    the nearby match and removes it from the actionable list.
    """
    claimed = find_all(bot, "EventCenter/EagleOfFreedom/status_claimed", screen,
                       threshold=0.72, region=(55, 18, 100, 98))
    claims = find_all(bot, "EventCenter/EagleOfFreedom/button_claim", screen,
                      threshold=0.68, region=(55, 18, 100, 98))
    return [
        pos for pos in claims
        if all(abs(pos[0] - done[0]) > 55 or abs(pos[1] - done[1]) > 24
               for done in claimed)
    ]


def _eagle_content_signature(screen):
    """Animation-tolerant dHash for detecting the vertical list boundary."""
    height, width = screen.shape[:2]
    patch = cv2.cvtColor(screen[int(height * .18):int(height * .98), :width],
                         cv2.COLOR_BGR2GRAY)
    tiny = cv2.resize(patch, (33, 16), interpolation=cv2.INTER_AREA)
    return np.packbits(tiny[:, 1:] > tiny[:, :-1]).tobytes()


def _eagle_content_moved(before, after) -> bool:
    old = np.frombuffer(_eagle_content_signature(before), dtype=np.uint8)
    new = np.frombuffer(_eagle_content_signature(after), dtype=np.uint8)
    distance = int(np.unpackbits(np.bitwise_xor(old, new)).sum())
    return distance > 8


def _handle_eagle_of_freedom(bot):
    """Claim every exact Claim control until the real bottom of the panel."""
    attempted = 0
    verified = 0
    unresolved = False
    bottom_checks = 0
    position = 0
    swipes = 0
    while True:
        position += 1
        bot.record(f"Gift Claims: Eagle of Freedom kiểm tra vùng nhiệm vụ "
                   f"{position} (lướt tới đáy thực tế)")
        empty_checks = 0
        blocked_positions = []
        while attempted < 20:
            bot.check()
            screen = bot.screenshot()
            claims = _eagle_active_claims(bot, screen)
            claim = next(
                (pos for pos in claims
                 if all((pos[0] - old[0]) ** 2 + (pos[1] - old[1]) ** 2
                        > 30 ** 2 for old in blocked_positions)),
                None,
            )
            if claim is None:
                empty_checks += 1
                if empty_checks < EMPTY_POSITION_CHECKS:
                    bot.sleep(UI_SETTLE_SECONDS)
                    continue
                break
            empty_checks = 0
            attempted += 1
            blocked_positions.append(claim)
            bot.record(f"Gift Claims: Eagle of Freedom tap Claim "
                       f"({attempted}/20) tại {claim}")
            bot.tap(*claim, delay=LIST_SCROLL_SETTLE_SECONDS)
            _close_exact_congratulations(bot)
            after_tap = bot.screenshot()
            still_active = any(
                abs(pos[0] - claim[0]) <= 35 and abs(pos[1] - claim[1]) <= 30
                for pos in _eagle_active_claims(bot, after_tap)
            )
            if still_active:
                unresolved = True
                bot.record("Gift Claims: Eagle of Freedom nút vẫn là Claim sau "
                           "khi bấm; giữ PENDING để lần sau kiểm tra lại")
            else:
                verified += 1
                bot.record("Gift Claims: Eagle of Freedom nút đã thành Claimed")

        before_swipe = bot.screenshot()
        if swipes >= MAX_EAGLE_CONTENT_SWIPES:
            bot.record("Gift Claims: Eagle of Freedom chạm giới hạn an toàn "
                       "12 lần lướt nhưng chưa xác nhận đáy; giữ PENDING")
            return ClaimReport(attempted, verified), False
        bot.record("Gift Claims: Eagle of Freedom đã kiểm tra khung hiện tại; "
                   "lướt chậm tìm đáy danh sách")
        bot.swipe_percent(50, 88, 50, 45,
                          duration=SWIPE_DURATION_SECONDS,
                          delay=LIST_SCROLL_SETTLE_SECONDS)
        swipes += 1
        after_swipe = bot.screenshot()
        if _eagle_content_moved(before_swipe, after_swipe):
            bottom_checks = 0
            continue
        bottom_checks += 1
        bot.record(f"Gift Claims: Eagle of Freedom danh sách không di chuyển "
                   f"({bottom_checks}/{EAGLE_BOTTOM_CONFIRMATIONS})")
        if bottom_checks < EAGLE_BOTTOM_CONFIRMATIONS:
            continue
        final_claims = _eagle_active_claims(bot, after_swipe)
        done = not final_claims and not unresolved
        break

    if done:
        bot.record("Gift Claims: Eagle of Freedom đã lướt hết và không còn Claim; DONE")
    elif unresolved:
        bot.record("Gift Claims: Eagle of Freedom đã tới đáy nhưng còn nút Claim "
                   "chưa đổi trạng thái; giữ PENDING")
    return ClaimReport(attempted, max(verified, int(done))), done


def _legion_claims(bot, screen):
    return find_all(bot, "EventCenter/LegionHunting/button_claim", screen,
                    threshold=0.78, region=LEGION_CLAIM_REGION)


def _legion_content_signature(screen):
    """dHash only the green quest frame; ignore animation in the banner."""
    height, width = screen.shape[:2]
    x0, y0, x1, y1 = LEGION_CONTENT_REGION
    patch = cv2.cvtColor(
        screen[int(height * y0 / 100):int(height * y1 / 100),
               int(width * x0 / 100):int(width * x1 / 100)],
        cv2.COLOR_BGR2GRAY,
    )
    tiny = cv2.resize(patch, (33, 16), interpolation=cv2.INTER_AREA)
    return np.packbits(tiny[:, 1:] > tiny[:, :-1]).tobytes()


def _legion_content_moved(before, after) -> bool:
    old = np.frombuffer(_legion_content_signature(before), dtype=np.uint8)
    new = np.frombuffer(_legion_content_signature(after), dtype=np.uint8)
    return int(np.unpackbits(np.bitwise_xor(old, new)).sum()) > 8


def _legion_swipe_to_top(bot) -> bool:
    """Reach the real top using touches confined to the green quest frame."""
    unchanged = 0
    for _ in range(MAX_LEGION_CONTENT_SWIPES):
        before = bot.screenshot()
        bot.swipe_percent(50, 52, 50, 90,
                          duration=SWIPE_DURATION_SECONDS,
                          delay=LIST_SCROLL_SETTLE_SECONDS)
        after = bot.screenshot()
        if _legion_content_moved(before, after):
            unchanged = 0
        else:
            unchanged += 1
            if unchanged >= LEGION_EDGE_CONFIRMATIONS:
                return True
    return False


def _scan_legion_once(bot) -> tuple[ClaimReport, bool, bool]:
    """Return (report, reached_bottom, unresolved_claim) for one full pass."""
    attempted = verified = 0
    bottom_checks = 0
    for position in range(1, MAX_LEGION_CONTENT_SWIPES + 2):
        bot.record("Gift Claims: Legion Hunting quét vùng nhiệm vụ màu xanh "
                   f"vị trí {position}")
        blocked_positions = []
        empty_checks = 0
        while attempted < 30:
            bot.check()
            screen = bot.screenshot()
            claim = next(
                (pos for pos in _legion_claims(bot, screen)
                 if all((pos[0] - old[0]) ** 2 + (pos[1] - old[1]) ** 2
                        > 30 ** 2 for old in blocked_positions)),
                None,
            )
            if claim is None:
                empty_checks += 1
                if empty_checks < EMPTY_POSITION_CHECKS:
                    bot.sleep(UI_SETTLE_SECONDS)
                    continue
                break

            empty_checks = 0
            blocked_positions.append(claim)
            attempted += 1
            bot.record(f"Gift Claims: Legion Hunting tap Claim tại {claim}")
            bot.tap(*claim, delay=LIST_SCROLL_SETTLE_SECONDS)
            close_congratulations(bot, attempts=2)
            after_tap = bot.screenshot()
            if any(abs(pos[0] - claim[0]) <= 35 and
                   abs(pos[1] - claim[1]) <= 30
                   for pos in _legion_claims(bot, after_tap)):
                bot.record("Gift Claims: Legion Hunting nút Claim vẫn còn sau "
                           "khi bấm; giữ PENDING")
                return ClaimReport(attempted, verified), False, True
            verified += 1

            if len(blocked_positions) >= MAX_LEGION_CLAIMS_PER_VIEW:
                break

        before = bot.screenshot()
        if position > MAX_LEGION_CONTENT_SWIPES:
            return ClaimReport(attempted, verified), False, False
        bot.record("Gift Claims: Legion Hunting đã kiểm tra khung hiện tại; "
                   "lướt chậm tìm Claim phía dưới")
        bot.swipe_percent(50, 90, 50, 52,
                          duration=SWIPE_DURATION_SECONDS,
                          delay=LIST_SCROLL_SETTLE_SECONDS)
        after = bot.screenshot()
        if _legion_content_moved(before, after):
            bottom_checks = 0
            continue
        bottom_checks += 1
        bot.record("Gift Claims: Legion Hunting danh sách không di chuyển "
                   f"({bottom_checks}/{LEGION_EDGE_CONFIRMATIONS})")
        if bottom_checks >= LEGION_EDGE_CONFIRMATIONS:
            return ClaimReport(attempted, verified), True, False
    return ClaimReport(attempted, verified), False, False


def _handle_legion_hunting(bot):
    """Claim rows, then require one whole Claim-free sweep before DONE."""
    total = ClaimReport()
    for pass_number in range(1, MAX_LEGION_VERIFY_PASSES + 1):
        bot.record("Gift Claims: Legion Hunting bắt đầu lượt quét đầy đủ "
                   f"{pass_number}/{MAX_LEGION_VERIFY_PASSES}")
        if not _legion_swipe_to_top(bot):
            bot.record("Gift Claims: Legion Hunting chưa xác nhận được đầu "
                       "danh sách; giữ PENDING")
            return total, False
        report, reached_bottom, unresolved = _scan_legion_once(bot)
        total = ClaimReport(total.attempted + report.attempted,
                            total.verified + report.verified)
        if unresolved or not reached_bottom:
            if not reached_bottom and not unresolved:
                bot.record("Gift Claims: Legion Hunting chưa xác nhận được đáy "
                           "danh sách; giữ PENDING")
            return total, False
        if report.attempted == 0:
            bot.record("Gift Claims: Legion Hunting đã lướt một lượt từ đầu "
                       "tới cuối và không còn Claim; DONE")
            return total, True
        bot.record("Gift Claims: Legion Hunting vừa nhận được quà; quay về đầu "
                   "và quét lại để xác nhận không còn Claim")
        bot.sleep(UI_SETTLE_SECONDS)
    bot.record("Gift Claims: Legion Hunting chưa có lượt quét sạch Claim; "
               "giữ PENDING")
    return total, False


def _moment_claim_colour_ratios(screen, center) -> tuple[float, float]:
    """Return green and low-saturation ratios around a Claim candidate."""
    scale = screen.shape[1] / 396
    width, height = max(1, round(82 * scale)), max(1, round(34 * scale))
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


def _moment_claims(bot, screen):
    """Find green Claim only; reject the Claim prefix inside gray Claimed."""
    candidates = find_all(bot, "Common/button_claim_text", screen,
                          threshold=0.65, region=MOMENT_CLAIM_REGION)
    return [point for point in candidates
            if ((ratios := _moment_claim_colour_ratios(screen, point))[0]
                >= MOMENT_GREEN_MIN_RATIO
                and ratios[1] < MOMENT_GRAY_MAX_RATIO)]


def _moment_swipe(bot, gesture, label: str) -> int:
    before = bot.screenshot()
    bot.swipe_percent(*gesture, duration=SWIPE_DURATION_SECONDS,
                      delay=LIST_SCROLL_SETTLE_SECONDS)
    after = bot.screenshot()
    distance = region_hamming_distance(before, after, MOMENT_CONTENT_REGION)
    bot.record(f"Gift Claims: Moment of Glory {label}, Hamming "
               f"{distance}/{MOMENT_SAME_DISTANCE}")
    return distance


def _moment_swipe_to_top(bot) -> None:
    unchanged = 0
    while unchanged < MOMENT_EDGE_CONFIRMATIONS:
        bot.check()
        distance = _moment_swipe(bot, MOMENT_RETURN_TOP_SWIPE,
                                 "đưa vùng xanh về đầu")
        unchanged = unchanged + 1 if distance <= MOMENT_SAME_DISTANCE else 0
        bot.record("Gift Claims: Moment of Glory biên đầu không đổi "
                   f"{unchanged}/{MOMENT_EDGE_CONFIRMATIONS}")


def _scan_moment_once(bot) -> tuple[ClaimReport, bool, bool]:
    """Return report, reached_bottom and unresolved Claim for one full pass."""
    attempted = verified = 0
    bottom_checks = 0
    while True:
        blocked_positions = []
        for _ in range(MAX_MOMENT_CLAIMS_PER_VIEW):
            bot.check()
            screen = bot.screenshot()
            claim = next(
                (pos for pos in _moment_claims(bot, screen)
                 if all((pos[0] - old[0]) ** 2 + (pos[1] - old[1]) ** 2
                        > 30 ** 2 for old in blocked_positions)),
                None,
            )
            if claim is None:
                break
            blocked_positions.append(claim)
            attempted += 1
            bot.record(f"Gift Claims: Moment of Glory tap Claim tại {claim}")
            bot.tap(*claim, delay=LIST_SCROLL_SETTLE_SECONDS)
            close_congratulations(bot, attempts=2)
            after = bot.screenshot()
            if any(abs(pos[0] - claim[0]) <= 35 and
                   abs(pos[1] - claim[1]) <= 30
                   for pos in _moment_claims(bot, after)):
                bot.record("Gift Claims: Moment of Glory Claim vẫn còn sau "
                           "khi bấm; giữ PENDING")
                return ClaimReport(attempted, verified), False, True
            verified += 1

        distance = _moment_swipe(bot, MOMENT_SCAN_SWIPE,
                                 "quét xuống cuối vùng xanh")
        bottom_checks = (bottom_checks + 1
                         if distance <= MOMENT_SAME_DISTANCE else 0)
        bot.record("Gift Claims: Moment of Glory biên cuối không đổi "
                   f"{bottom_checks}/{MOMENT_EDGE_CONFIRMATIONS}")
        if bottom_checks >= MOMENT_EDGE_CONFIRMATIONS:
            final = bot.screenshot()
            unresolved = bool(_moment_claims(bot, final))
            return ClaimReport(attempted, verified), True, unresolved


def _handle_moment_of_glory(bot):
    """Claim all rows, then require one complete Claim-free pass for DONE."""
    total = ClaimReport()
    while True:
        bot.check()
        _moment_swipe_to_top(bot)
        report, reached_bottom, unresolved = _scan_moment_once(bot)
        total = ClaimReport(total.attempted + report.attempted,
                            total.verified + report.verified)
        if unresolved or not reached_bottom:
            return total, False
        if report.attempted == 0:
            bot.record("Gift Claims: Moment of Glory đã quét từ đầu tới cuối "
                       "không còn Claim; DONE")
            return total, True
        bot.record("Gift Claims: Moment of Glory vừa nhận Claim; quay lại đầu "
                   "để quét xác nhận")


EXACT_HANDLERS = {
    GiftScreen.DRAGON_BATTLE: _handle_dragon_battle,
    GiftScreen.PRECIOUS_BLAZON_EXCHANGE: _handle_precious,
    GiftScreen.POSEIDONS_DAY: _handle_poseidon,
    GiftScreen.HYPNOS_DREAM: _handle_hypnos,
    GiftScreen.GRACE_OF_STAR_TRAIL: _handle_grace,
    GiftScreen.GIANTS_WISDOM_TEMPLE: _handle_giant,
    GiftScreen.DWARFS_TREASURE: _handle_dwarf,
    GiftScreen.WISHFUL_WINDMILL_FESTIVAL: _handle_wishful,
    GiftScreen.DWARFS_LUCKY_APPLE: _handle_dwarfs_lucky_apple,
    GiftScreen.EAGLE_OF_FREEDOM: _handle_eagle_of_freedom,
    GiftScreen.LEGION_HUNTING: _handle_legion_hunting,
    GiftScreen.MOMENT_OF_GLORY: _handle_moment_of_glory,
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
        bot.back(delay=UI_SETTLE_SECONDS)
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
                bot.tap(*pos, delay=UI_SETTLE_SECONDS)
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
                        bot.tap(*entry_pos, delay=UI_SETTLE_SECONDS)
                        break
        if attempt + 1 < attempts:
            bot.sleep(UI_SETTLE_SECONDS)
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
        bot.tap(*pos, delay=UI_SETTLE_SECONDS)
        if close_congratulations(bot):
            bot.record("Gift Claims: verified Star Trail Gift Congratulations")
            return ClaimReport(1, 1)
        attempted = 1
        for attempt in range(4):
            claim_screen = bot.screenshot()
            claim = find(bot, "EventCenter/GraceOfStarTrail/button_claim", claim_screen,
                         threshold=0.70, region=REWARD_NAV_REGION)
            if claim is not None:
                attempted += 1
                bot.record("Gift Claims: tap Grace of Star Trail coin Claim")
                bot.tap(*claim, delay=UI_SETTLE_SECONDS)
                if close_congratulations(bot):
                    bot.record("Gift Claims: verified Star Trail coin Congratulations")
                    return ClaimReport(attempted, 1)
                after = bot.screenshot()
                if find(bot, "EventCenter/GraceOfStarTrail/button_claim", after,
                        threshold=0.70, region=REWARD_NAV_REGION) is None:
                    bot.record("Gift Claims: verified Star Trail coin Claim disappeared")
                    return ClaimReport(attempted, 1)
            if attempt < 3:
                bot.sleep(UI_SETTLE_SECONDS)
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
        pending = getattr(bot, PENDING_THIS_RUN_ATTR, None)
        if isinstance(pending, set) and policy.key is not None:
            pending.add(policy.key)
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
        if find(bot, "EventCenter/BlessingOfPallas/status_claimed", opened, threshold=0.68,
                region=LOWER) is not None:
            bot.record("Gift Claims: Blessing of Pallas đã hiện Claimed")
            mark_task_done(bot, blessing_of_pallas.POLICY.key)
            return ClaimReport(0, 1)
        bot.record("Gift Claims: Event Center page chưa có title template; "
                   "kiểm tra nội dung một lần, không quét dot trong artwork")
        report, _ = _process_current_event_content(bot)
        after = bot.screenshot()
        if find(bot, "EventCenter/BlessingOfPallas/status_claimed", after, threshold=0.68,
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
                        delay=UI_SETTLE_SECONDS)
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
                    bot.swipe_percent(85, 11, 20, 11,
                                      duration=SWIPE_DURATION_SECONDS,
                                      delay=UI_SETTLE_SECONDS)
                else:
                    bot.swipe_percent(20, 11, 85, 11,
                                      duration=SWIPE_DURATION_SECONDS,
                                      delay=UI_SETTLE_SECONDS)
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


def _category_done_key(category: str) -> bytes:
    return CATEGORY_DONE_PREFIX + category.encode("ascii")


def _category_policy_keys(category: str) -> tuple[str, ...]:
    """Daily DB keys that must be DONE before leaving one category."""
    return tuple(
        policy.key for policy in EVENT_POLICIES
        if policy.key is not None
        and POLICY_CATEGORIES.get(policy.key, "limited") == category
    )


def _category_db_done(bot, category: str) -> bool:
    return all(bool(bot.is_daily_done(key))
               for key in _category_policy_keys(category))


def _select_category(bot, name: str, x_percent: int) -> bool:
    bot.record(f"Gift Claims: Event Center chọn nhóm {name}")
    screen = bot.screenshot()
    # Always select Limited explicitly after opening Event Center.  Evony can
    # remember the previously selected Activities tab, so starting the list
    # scan without this click may inspect the wrong category.  Use the exact
    # text crop supplied from the live UI; the coordinate is only a fallback
    # for a temporarily animated/blurred tab.
    category_template = ("EventCenter/tab_activities"
                         if name == "activities"
                         else "EventCenter/tab_limited")
    category_pos = find(bot, category_template, screen, threshold=0.72,
                        region=(0, 5, 80, 18))
    settle = (APPLE_LIST_SETTLE_SECONDS
              if name == "activities" else UI_SETTLE_SECONDS)
    if category_pos is not None:
        bot.tap(*category_pos, delay=settle)
    else:
        bot.tap_percent(x_percent, 11, delay=settle)
    for _ in range(4):
        screen = bot.screenshot()
        if find(bot, PAGE, screen, threshold=0.72,
                region=(0, 0, 100, 13)) is not None:
            return True
        bot.sleep(settle)
    return False


def _list_signature(screen) -> bytes:
    """Hash vertical row structure, ignoring per-row animation and timers."""
    right = max(1, int(screen.shape[1] * 0.68))
    top = max(0, int(screen.shape[0] * 0.14))
    bottom = max(top + 1, int(screen.shape[0] * 0.98))
    patch = cv2.cvtColor(screen[top:bottom, :right], cv2.COLOR_BGR2GRAY)
    patch = cv2.GaussianBlur(patch, (5, 5), 0)
    # Average each horizontal strip. Row dividers and title bands move when
    # the list scrolls; animated pixels inside a row average away.
    tiny = cv2.resize(
        patch, (32, LIST_SIGNATURE_BITS), interpolation=cv2.INTER_AREA)
    vertical_profile = tiny.mean(axis=1)
    return np.packbits(
        vertical_profile[1:] > vertical_profile[:-1]).tobytes()


def _list_hamming_distance(before: bytes, after: bytes) -> int:
    old = np.frombuffer(before, dtype=np.uint8)
    new = np.frombuffer(after, dtype=np.uint8)
    if old.shape != new.shape:
        return LIST_SIGNATURE_BITS
    return int(np.unpackbits(np.bitwise_xor(old, new)).sum())


def _same_list_position(before: bytes, after: bytes,
                        max_distance=LIST_SAME_DISTANCE) -> bool:
    return _list_hamming_distance(before, after) <= max_distance


def _return_list_to_top(bot, category: str) -> bool:
    """Prove the real top with consecutive settled no-movement swipes."""
    bot.record(f"Gift Claims: Event Center/{category} đưa danh sách về đầu")
    unchanged = 0
    step = 0
    while True:
        bot.check()
        step += 1
        before = _list_signature(bot.screenshot())
        bot.swipe_percent(50, 32, 50, 86,
                          duration=SWIPE_DURATION_SECONDS,
                          delay=LIST_SCROLL_SETTLE_SECONDS)
        after = _list_signature(bot.screenshot())
        distance = _list_hamming_distance(before, after)
        bot.record(f"Gift Claims: Event Center/{category} dừng "
                   f"{LIST_SCROLL_SETTLE_SECONDS:.0f}s sau lướt về đầu "
                   f"(lần {step}), Hamming "
                   f"{distance}/{LIST_SAME_DISTANCE}")
        unchanged = (unchanged + 1
                     if _same_list_position(before, after) else 0)
        if unchanged >= LIST_EDGE_CONFIRMATIONS:
            bot.record(f"Gift Claims: Event Center/{category} đã xác nhận "
                       f"biên đầu sau {LIST_EDGE_CONFIRMATIONS} cú không đổi")
            return True


def _find_dwarfs_lucky_apple_row(bot) -> bool:
    """Scan Activities from top to bottom, then bottom to top at 0.8 s.

    Both edges require two consecutive no-movement swipes.  The reverse pass
    matters because a title can be hidden by a still-moving frame on the first
    descent.  This helper only locates the row; the caller re-finds the exact
    template before tapping it.
    """
    template = "EventCenter/DwarfsLuckyApple/list_row"

    def swipe(start_y, end_y, direction, *, search: bool) -> bool | None:
        unchanged = 0
        step = 0
        while True:
            bot.check()
            step += 1
            screen = bot.screenshot()
            if (search and find(bot, template, screen, threshold=0.90,
                                region=(10, 15, 75, 98)) is not None):
                bot.record("Gift Claims: Activities tìm thấy dòng Dwarf's "
                           f"Lucky Apple khi quét {direction}")
                return True
            before = _list_signature(screen)
            bot.swipe_percent(50, start_y, 50, end_y,
                              duration=SWIPE_DURATION_SECONDS,
                              delay=APPLE_LIST_SETTLE_SECONDS)
            after = _list_signature(bot.screenshot())
            distance = _list_hamming_distance(before, after)
            same = _same_list_position(before, after)
            unchanged = unchanged + 1 if same else 0
            bot.record("Gift Claims: Activities lướt " + direction +
                       f", chờ {APPLE_LIST_SETTLE_SECONDS:.1f}s rồi quét "
                       f"(lần {step}), Hamming "
                       f"{distance}/{LIST_SAME_DISTANCE}")
            if unchanged >= APPLE_LIST_EDGE_CONFIRMATIONS:
                bot.record(f"Gift Claims: Activities đã xác nhận tới {direction}")
                return False

    # First establish the real top.  Do not waste a 1.5 s duplicate probe at
    # each position: every swipe already settles for 0.8 s before the frame is
    # sampled.
    swipe(32, 86, "đỉnh", search=False)
    if swipe(86, 32, "xuống đáy", search=True):
        return True
    if swipe(32, 86, "lên đỉnh", search=True):
        return True

    # Scan the final top frame too: the second edge-confirming swipe may have
    # exposed the row only after the previous screenshot.
    return find(bot, template, bot.screenshot(), threshold=0.90,
                region=(10, 15, 75, 98)) is not None


def _record_missing_event_policies(bot, seen_policy_keys: set[str],
                                   category="limited") -> set[str]:
    """Report policies absent in this pass without prematurely writing DONE."""
    missing = set()
    for policy in EVENT_POLICIES:
        if policy.key is None or policy.key in seen_policy_keys:
            continue
        if POLICY_CATEGORIES.get(policy.key, "limited") != category:
            continue
        if bot.is_daily_done(policy.key):
            continue
        bot.record(f"Gift Claims: không tìm thấy {policy.label} trong lượt quét "
                   f"{category} từ đầu tới cuối; ghi nhận một lượt không thấy")
        missing.add(policy.key)
    return missing


def _policy_seen_checkpoint(policy_key: str) -> bytes:
    return POLICY_SEEN_PREFIX + policy_key.encode("utf-8")


def _scan_category(bot, category: str, visited: set[bytes]) -> bool:
    """Process every explicitly registered task in one category."""
    opened_count = 0
    failed_forced = set()
    recentered_forced = set()
    seen_policy_keys: set[str] = {
        item[len(POLICY_SEEN_PREFIX):].decode("utf-8")
        for item in visited if item.startswith(POLICY_SEEN_PREFIX)
    }
    seen_policies = getattr(bot, SEEN_POLICIES_ATTR, None)
    if not isinstance(seen_policies, set):
        seen_policies = set()
        setattr(bot, SEEN_POLICIES_ATTR, seen_policies)
    seen_policies.update(seen_policy_keys)
    pending_this_run = getattr(bot, PENDING_THIS_RUN_ATTR, None)
    if not isinstance(pending_this_run, set):
        pending_this_run = set()
    # Activities has a dedicated bidirectional 0.8-second scan. Limited first
    # proves its real top and then runs until the real bottom, with no local
    # swipe-count ceiling, exactly like Valuable Event's edge traversal.
    if category == "activities":
        if not _find_dwarfs_lucky_apple_row(bot):
            _record_missing_event_policies(bot, seen_policy_keys, category)
            bot.record("Gift Claims: Activities đã quét từ đỉnh xuống đáy rồi "
                       "từ đáy lên đỉnh nhưng chưa thấy Dwarf's Lucky Apple")
            return True
        scan_to_bottom = False
        list_settle = APPLE_LIST_SETTLE_SECONDS
    else:
        # Evony remembers a separate vertical position for each category.
        _return_list_to_top(bot, category)
        scan_to_bottom = True
        list_settle = LIST_SCROLL_SETTLE_SECONDS
    scroll = 0
    bottom_checks = 0
    while True:
        bot.check()
        empty_checks = 0
        bot.record(f"Gift Claims: Event Center/{category} quét vị trí danh sách "
                   f"{scroll + 1}")
        pending_labels = [
            policy.label for policy in EVENT_POLICIES
            if policy.key is not None
            and POLICY_CATEGORIES.get(policy.key, "limited") == category
            and not bot.is_daily_done(policy.key)
        ]
        bot.record(f"Gift Claims: Event Center/{category} đang kiểm tra: "
                   + (", ".join(pending_labels) if pending_labels else
                      "không còn nhiệm vụ PENDING"))
        while True:
            bot.check()
            screen = bot.screenshot()
            candidate = None
            forced_rows = (FORCED_LIMITED_ROWS if category == "limited"
                           else FORCED_ACTIVITY_ROWS
                           if category == "activities" else ())
            if forced_rows:
                for (template, key, expected_screen, event_label,
                     policy_key) in forced_rows:
                    if key in visited or key in failed_forced:
                        continue
                    if (policy_key is not None
                            and bot.is_daily_done(policy_key) is True):
                        # A forced row exists only to inspect named events that
                        # can lose their outer red badge.  Once its durable DB
                        # key is current, reopening it wastes several seconds
                        # per device and may revisit paid/decorative controls.
                        visited.add(key)
                        continue
                    row = find(bot, template, screen, threshold=0.90,
                               region=(10, 15, 75, 98))
                    if isinstance(row, tuple) and len(row) == 2:
                        if policy_key in pending_this_run:
                            # This named task already exhausted its own bounded
                            # checks during the current Gift Claims window.
                            # Remember its named key so it is not reopened in
                            # this 120-second window.
                            tap_y = min(screen.shape[0] - 1, row[1] + 18)
                            visited.add(key)
                            bot.record(f"Gift Claims: {event_label} đang PENDING "
                                       "trong lượt 120s này; bỏ qua để làm "
                                       "nhiệm vụ kế tiếp")
                            continue
                        if policy_key is not None:
                            seen_policy_keys.add(policy_key)
                            seen_policies.add(policy_key)
                            visited.add(_policy_seen_checkpoint(policy_key))
                        if (row[1] > int(screen.shape[0] * 0.80)
                                and key not in recentered_forced):
                            # A row title can be visible above the bottom bar
                            # while its clickable body is still off-screen.
                            # Bring it into the list body before selecting it.
                            recentered_forced.add(key)
                            bot.record(f"Gift Claims: kéo {event_label} từ sát đáy "
                                       "lên giữa màn hình trước khi bấm")
                            bot.swipe_percent(50, 82, 50, 52,
                                              duration=SWIPE_DURATION_SECONDS,
                                              delay=list_settle)
                            candidate = "recenter"
                            break
                        # The title sits near the top edge of a list row. Tap
                        # below it so a small residual scroll cannot select
                        # the preceding event (observed with Dwarf -> Sealed).
                        tap_y = min(screen.shape[0] - 1, row[1] + 18)
                        # Use the detected title's horizontal centre instead
                        # of a fixed x=52%.  Wishful's row caption can sit far
                        # left on narrower/scaled emulator frames.
                        candidate = (row[0], tap_y, key, expected_screen,
                                     event_label, policy_key)
                        bot.record(f"Gift Claims: Event Center mở {event_label} "
                                   "để kiểm tra quà bên trong dù dòng ngoài không đỏ "
                                   f"(y={tap_y})")
                        break
                if candidate == "recenter":
                    continue
            if candidate == "recenter":
                empty_checks = 0
                continue
            if candidate is None:
                empty_checks += 1
                # The dedicated Activities traversal has already waited 0.8 s
                # and inspected each stable position.  Do not add the old
                # extra 1.5-second duplicate check before moving on.
                required_checks = (1 if category == "activities"
                                   else EMPTY_POSITION_CHECKS)
                if empty_checks < required_checks:
                    bot.record(f"Gift Claims: Event Center/{category} chưa thấy "
                               "nhiệm vụ ở khung hiện tại; chờ "
                               f"{UI_SETTLE_SECONDS:g}s rồi quét lại")
                    bot.sleep(UI_SETTLE_SECONDS)
                    continue
                break
            empty_checks = 0
            x, y, key, expected_screen, event_label, forced_policy_key = candidate
            tap_settle = (APPLE_LIST_SETTLE_SECONDS
                          if category == "activities" else UI_SETTLE_SECONDS)
            bot.tap(x, y, delay=tap_settle)
            actual_screen = _wait_event_row_open(
                bot, expected_screen, delay=tap_settle)
            if (actual_screen == GiftScreen.EVENT_CENTER
                    and expected_screen is not None):
                # The first tap can be swallowed while the scrolling list is
                # still settling.  Re-find the exact named row before retrying
                # so a changed list position can never open the wrong event.
                row_template = next(
                    (template for template, row_key, *_ in forced_rows
                     if row_key == key), None)
                refreshed = (find(bot, row_template, bot.screenshot(),
                                  threshold=0.90, region=(10, 15, 75, 98))
                             if row_template is not None else None)
                if isinstance(refreshed, tuple) and len(refreshed) == 2:
                    retry_y = min(screen.shape[0] - 1, refreshed[1] + 18)
                    bot.record(f"Gift Claims: {event_label} vẫn ở danh sách sau "
                               "cú tap đầu; tìm lại đúng hàng và tap lần 2")
                    bot.tap(refreshed[0], retry_y,
                            delay=tap_settle)
                    actual_screen = _wait_event_row_open(
                        bot, expected_screen, delay=tap_settle)
            if actual_screen == GiftScreen.EVENT_CENTER:
                bot.log("Gift Claims: bấm hàng nhưng vẫn ở Event Center; bỏ vị trí "
                        "này trong lượt quét và không kết luận event vắng mặt")
                failed_forced.add(key)
                if forced_policy_key is not None:
                    if isinstance(pending_this_run, set):
                        pending_this_run.add(forced_policy_key)
                    seen_policy_keys.add(forced_policy_key)
                    seen_policies.add(forced_policy_key)
                    visited.add(_policy_seen_checkpoint(forced_policy_key))
                visited.add(key)
                continue
            actual_policy = POLICY_BY_SCREEN.get(actual_screen)
            if actual_policy is not None and actual_policy.key is not None:
                seen_policy_keys.add(actual_policy.key)
                seen_policies.add(actual_policy.key)
                visited.add(_policy_seen_checkpoint(actual_policy.key))
            elif forced_policy_key is not None:
                # Pallas currently has no stable page-title crop; the exact
                # list label is its identity.
                seen_policy_keys.add(forced_policy_key)
                seen_policies.add(forced_policy_key)
                visited.add(_policy_seen_checkpoint(forced_policy_key))
            if expected_screen is not None:
                if actual_screen != expected_screen:
                    bot.log(f"Gift Claims: bấm hàng {event_label} nhưng mở "
                            f"{getattr(actual_screen, 'value', actual_screen)}; "
                            "không đánh dấu DONE, giữ PENDING")
                    failed_forced.add(key)
                    if (forced_policy_key is not None
                            and isinstance(pending_this_run, set)):
                        pending_this_run.add(forced_policy_key)
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
        if not scan_to_bottom:
            break
        before = _list_signature(bot.screenshot())
        bot.swipe_percent(50, 86, 50, 32,
                          duration=SWIPE_DURATION_SECONDS,
                          delay=list_settle)
        bot.record(f"Gift Claims: Event Center/{category} đã dừng "
                   f"{list_settle:g}s sau lướt; bắt đầu quét")
        after = _list_signature(bot.screenshot())
        distance = _list_hamming_distance(before, after)
        same = _same_list_position(before, after)
        bottom_checks = bottom_checks + 1 if same else 0
        bot.record(f"Gift Claims: Event Center/{category} Hamming "
                   f"{distance}/{LIST_SAME_DISTANCE}, không đổi "
                   f"{bottom_checks}/{LIST_EDGE_CONFIRMATIONS}")
        if bottom_checks >= LIST_EDGE_CONFIRMATIONS:
            bot.log(f"Gift Claims: Event Center/{category} đã xác nhận cuối "
                    f"danh sách sau {LIST_EDGE_CONFIRMATIONS} cú không đổi")
            break
        scroll += 1

    clean = not failed_forced
    if clean:
        _record_missing_event_policies(bot, seen_policy_keys, category)
    bot.record(f"Gift Claims: Event Center/{category} đã mở {opened_count} "
               "nhiệm vụ đã đăng ký; "
               + ("đã quét hết danh sách; chờ xác nhận các key DB" if clean
                  else "còn nhiệm vụ đã nhận diện nhưng chưa mở/xử lý xong"))
    return clean


def run_opened(bot, handled=None):
    """Finish Limited first, then Activities, resuming after a Boss yield."""
    screen = bot.screenshot()
    if find(bot, PAGE, screen, threshold=0.72,
            region=(0, 0, 100, 13)) is None:
        return_home(bot)
        return False

    visited = handled if handled is not None else set()
    all_clean = True
    categories = _ordered_categories(bot)
    bot.record("Gift Claims: thứ tự Event Center lượt này: "
               + " -> ".join(category for category, _ in categories))
    for category, x_percent in categories:
        bot.check()
        if _category_db_done(bot, category):
            bot.record(f"Gift Claims: Event Center/{category} toàn bộ key đã "
                       "DONE trong DB; chuyển sang nhóm kế tiếp")
            visited.add(_category_done_key(category))
            continue
        if _category_done_key(category) in visited:
            bot.record(f"Gift Claims: Event Center/{category} đã DONE ở lát trước; bỏ qua")
            continue
        if not _select_category(bot, category, x_percent):
            bot.log(f"Gift Claims: không mở được nhóm Event Center/{category}")
            all_clean = False
            continue
        scanned_clean = _scan_category(bot, category, visited)
        setattr(bot, SCAN_COMPLETE_ATTR, scanned_clean)
        if scanned_clean:
            scanned_categories = getattr(bot, SCANNED_CATEGORIES_ATTR, None)
            if not isinstance(scanned_categories, set):
                scanned_categories = set()
                setattr(bot, SCANNED_CATEGORIES_ATTR, scanned_categories)
            scanned_categories.add(category)
            next_category = ("activities" if category == "limited"
                             else "limited")
            _set_resume_category(bot, next_category)
        category_done = scanned_clean and _category_db_done(bot, category)
        if category_done:
            # Persist category completion in the same in-memory checkpoint set
            # as its rows, so a 120-second boss yield cannot force a full list
            # verification of Limited/Activities again.
            visited.add(_category_done_key(category))
        else:
            all_clean = False
            if scanned_clean:
                pending = [key for key in _category_policy_keys(category)
                           if not bot.is_daily_done(key)]
                bot.record(f"Gift Claims: Event Center/{category} đã quét hết "
                           f"nhưng còn {len(pending)} key PENDING trong DB")

        if category == "limited" and not category_done:
            bot.record("Gift Claims: Limited còn PENDING; vẫn chuyển sang "
                       "Activities để làm các nhiệm vụ khác trong lượt này")

    return all_clean


TASK = GiftTask(KEY, "Event Center Limited", run)
