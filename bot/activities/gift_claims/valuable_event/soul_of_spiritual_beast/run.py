"""Claim Soul of Spiritual Beast quest rows and main-page score chests."""
import cv2

from ...common import (GiftTask, close_congratulations, find, find_all,
                       return_home, select_carousel_tab)
from ...lobby import open_named
from ...screens import GiftScreen
from ...super_value_return.login_gifts.run import CONGRATULATIONS
from ..named_flow import (ExactFlow, SLOW_SWIPE_DURATION, STEP_DELAY,
                          region_hamming_distance)

KEY = "gift_soul_of_spiritual_beast"
PAGE = "SuperValueReturn/title"
TAB = "SuperValueReturn/SoulOfSpiritualBeast/tab"
CHALLENGE_QUEST = "SuperValueReturn/SoulOfSpiritualBeast/challenge_quest"
QUESTS_TITLE = "SuperValueReturn/SoulOfSpiritualBeast/title_quests"
DAILY_TASKS = "SuperValueReturn/SoulOfSpiritualBeast/tab_daily_tasks"
SEASONAL = "SuperValueReturn/SoulOfSpiritualBeast/tab_seasonal"
CLAIM = "SuperValueReturn/SoulOfSpiritualBeast/button_claim"
CLAIMED = "SuperValueReturn/SoulOfSpiritualBeast/status_claimed"
GO = "ValuableEvent/SuperValueWeeklyCard/button_go"

# Main-page chest rectangle from the second supplied 396x704 screenshot.
MAIN_CHEST_REGION = (1, 22, 34, 40)
# Median from 50 stable ADB frames on 21513 (2026-10-27): genuine scores
# 0.8323..0.9834 and the strongest other match in this green rectangle was
# 0.2027.  0.65 retains a generous live-animation margin without allowing a
# background match to be treated as a chest.
MAIN_CHEST = "SuperValueReturn/SoulOfSpiritualBeast/button_reward_chest_median"
MAIN_CHEST_THRESHOLD = 0.65
# Quest-list rectangle from the first supplied 396x704 screenshot.
QUEST_REGION = (5, 34, 97, 82)
SCAN_SWIPE = (50, 78, 50, 43)
RETURN_TOP_SWIPE = (50, 43, 50, 78)
EDGE_CONFIRMATIONS = 2
CHEST_ABSENCE_CONFIRMATIONS = 2
SAME_DISTANCE = 24
CLAIM_THRESHOLD = 0.72
CLAIMED_THRESHOLD = 0.76
MAX_CLAIMS_PER_VIEW = 12
GREEN_MIN_RATIO = 0.22
GRAY_MIN_RATIO = 0.50

DONE = "done"
DONE_1 = "done_1"
PENDING = "pending"

FLOW = ExactFlow()


def _button_crop(screen, center, reference_size):
    scale = screen.shape[1] / 396
    width = max(1, round(reference_size[0] * scale))
    height = max(1, round(reference_size[1] * scale))
    left = max(0, center[0] - width // 2)
    top = max(0, center[1] - height // 2)
    return screen[top:min(screen.shape[0], top + height),
                  left:min(screen.shape[1], left + width)]


def _colour_ratios(crop) -> tuple[float, float]:
    if crop.size == 0:
        return 0.0, 0.0
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    green = ((hsv[..., 0] >= 35) & (hsv[..., 0] <= 90) &
             (hsv[..., 1] >= 60) & (hsv[..., 2] >= 50))
    gray = ((hsv[..., 1] <= 70) & (hsv[..., 2] >= 50))
    return float(green.mean()), float(gray.mean())


def _is_green_claim(screen, center) -> bool:
    green, gray = _colour_ratios(_button_crop(screen, center, (69, 26)))
    return green >= GREEN_MIN_RATIO and gray < 0.45


def _is_gray_claimed(screen, center) -> bool:
    green, gray = _colour_ratios(_button_crop(screen, center, (65, 24)))
    return green <= 0.08 and gray >= GRAY_MIN_RATIO


def _green_claims(bot, screen):
    return [point for point in find_all(
        bot, CLAIM, screen, threshold=CLAIM_THRESHOLD, region=QUEST_REGION)
            if _is_green_claim(screen, point)]


def _gray_claimed(bot, screen):
    return [point for point in find_all(
        bot, CLAIMED, screen, threshold=CLAIMED_THRESHOLD,
        region=QUEST_REGION) if _is_gray_claimed(screen, point)]


def _has_pending_go(bot, screen) -> bool:
    return find(bot, GO, screen, threshold=0.70,
                region=QUEST_REGION) is not None


def _main_open(bot, screen=None) -> bool:
    screen = bot.screenshot() if screen is None else screen
    return find(bot, CHALLENGE_QUEST, screen, threshold=0.78,
                region=(55, 30, 100, 55)) is not None


def _find_main_chest(bot, screen):
    """Find only the 21513-calibrated Soul Beast chest in its green frame."""
    return find(bot, MAIN_CHEST, screen, threshold=MAIN_CHEST_THRESHOLD,
                region=MAIN_CHEST_REGION)


def _confirm_main_chest_absent(bot) -> bool:
    """Confirm on fresh main-page frames that the reward chest is gone."""
    absent = 0
    for attempt in range(CHEST_ABSENCE_CONFIRMATIONS + 2):
        screen = bot.screenshot()
        on_main = _main_open(bot, screen)
        chest = _find_main_chest(bot, screen)
        absent = absent + 1 if on_main and chest is None else 0
        bot.record(
            "Gift Claims: Soul Beast kiểm tra lại rương sau tap "
            f"({attempt + 1}/{CHEST_ABSENCE_CONFIRMATIONS}); "
            + ("không thấy rương" if on_main and chest is None
               else "rương vẫn còn hoặc chưa ở màn Challenge Quest")
        )
        if absent >= CHEST_ABSENCE_CONFIRMATIONS:
            return True
        if attempt + 1 < CHEST_ABSENCE_CONFIRMATIONS + 2:
            bot.sleep(1)
    return False


def _claim_main_chests(bot) -> bool:
    """Claim every visible chest; disappearance is the terminal condition."""
    while True:
        bot.check()
        screen = bot.screenshot()
        if not _main_open(bot, screen):
            bot.record("Gift Claims: Soul Beast chưa xác nhận màn chính")
            return False
        chest = _find_main_chest(bot, screen)
        if chest is None:
            bot.record("Gift Claims: Soul Beast quét vùng rương xanh: "
                       "không thấy rương")
            return True
        bot.record("Gift Claims: Soul Beast thấy rương trong vùng xanh; tap")
        bot.tap(*chest, delay=STEP_DELAY)
        bot.sleep(1)
        for attempt in range(6):
            popup = find(bot, CONGRATULATIONS, bot.screenshot(), threshold=0.78,
                         region=(0, 38, 100, 62))
            if popup is not None:
                bot.record("Gift Claims: Soul Beast thấy Congratulations; "
                           "Back và kiểm tra rương tiếp")
                bot.back(delay=STEP_DELAY)
                break
            if attempt + 1 < 6:
                bot.sleep(1)
        else:
            bot.record("Gift Claims: Soul Beast không thấy Congratulations; "
                       "kiểm tra lại vùng rương")
            if _confirm_main_chest_absent(bot):
                bot.record("Gift Claims: Soul Beast rương đã biến mất dù "
                           "không có Congratulations; hoàn tất lượt rương")
                return True
            bot.record("Gift Claims: Soul Beast rương vẫn còn hoặc chưa xác "
                       "nhận được màn chính; giữ PENDING")
            return False


def _open_quests(bot) -> bool:
    screen = bot.screenshot()
    challenge = find(bot, CHALLENGE_QUEST, screen, threshold=0.78,
                     region=(55, 30, 100, 55))
    if challenge is None:
        return False
    bot.record("Gift Claims: Soul Beast mở Challenge Quest")
    bot.tap(*challenge, delay=STEP_DELAY)
    for attempt in range(4):
        if find(bot, QUESTS_TITLE, bot.screenshot(), threshold=0.78,
                region=(20, 8, 80, 24)) is not None:
            return True
        if attempt + 1 < 4:
            bot.sleep(STEP_DELAY)
    return False


def _select_quest_tab(bot, template) -> bool:
    for attempt in range(4):
        screen = bot.screenshot()
        pos = find(bot, template, screen, threshold=0.78,
                   region=(0, 25, 100, 40))
        if pos is not None:
            bot.tap(*pos, delay=STEP_DELAY)
            return True
        if attempt + 1 < 4:
            bot.sleep(STEP_DELAY)
    return False


def _swipe(bot, gesture) -> int:
    before = bot.screenshot()
    bot.swipe_percent(*gesture, duration=SLOW_SWIPE_DURATION,
                      delay=STEP_DELAY)
    after = bot.screenshot()
    return region_hamming_distance(before, after, QUEST_REGION)


def _swipe_to_top(bot) -> None:
    unchanged = 0
    while unchanged < EDGE_CONFIRMATIONS:
        bot.check()
        distance = _swipe(bot, RETURN_TOP_SWIPE)
        unchanged = unchanged + 1 if distance <= SAME_DISTANCE else 0
        bot.record("Gift Claims: Soul Beast về đầu vùng xanh, Hamming "
                   f"{distance}/{SAME_DISTANCE}, không đổi "
                   f"{unchanged}/{EDGE_CONFIRMATIONS}")


def _claim_current_view(bot) -> tuple[bool, bool, bool, bool]:
    claimed_now = False
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
            return (claimed_now, bool(green_claims),
                    bool(_gray_claimed(bot, final)),
                    _has_pending_go(bot, final))
        point = candidates[0]
        bot.record("Gift Claims: Soul Beast thấy Claim có dải xanh; tap")
        bot.tap(*point, delay=STEP_DELAY)
        close_congratulations(bot, attempts=2)
        claimed_now = True
        after = bot.screenshot()
        if any((candidate[0] - point[0]) ** 2 +
               (candidate[1] - point[1]) ** 2 <= 30 ** 2
               for candidate in _green_claims(bot, after)):
            blocked.append(point)
    return claimed_now, bool(_green_claims(bot, bot.screenshot())), False, False


def _scan_quest_tab(bot) -> tuple[bool, bool, bool, bool]:
    _swipe_to_top(bot)
    claimed_any = saw_claimed = saw_pending = False
    unchanged = 0
    while True:
        bot.check()
        claimed, stuck, claimed_state, pending_state = _claim_current_view(bot)
        claimed_any = claimed_any or claimed
        saw_claimed = saw_claimed or claimed_state
        saw_pending = saw_pending or pending_state
        if stuck:
            return claimed_any, True, saw_claimed, saw_pending
        if claimed:
            unchanged = 0
        distance = _swipe(bot, SCAN_SWIPE)
        unchanged = unchanged + 1 if distance <= SAME_DISTANCE else 0
        bot.record("Gift Claims: Soul Beast quét vùng xanh, Hamming "
                   f"{distance}/{SAME_DISTANCE}, không đổi "
                   f"{unchanged}/{EDGE_CONFIRMATIONS}")
        if unchanged < EDGE_CONFIRMATIONS:
            continue
        claimed, stuck, claimed_state, pending_state = _claim_current_view(bot)
        claimed_any = claimed_any or claimed
        saw_claimed = saw_claimed or claimed_state
        saw_pending = saw_pending or pending_state
        if stuck:
            return claimed_any, True, saw_claimed, saw_pending
        if claimed:
            unchanged = 0
            continue
        return claimed_any, False, saw_claimed, saw_pending


def claim_opened(bot) -> str:
    """Process an already selected Soul Beast tab once in this 120s window."""
    if not _main_open(bot):
        return PENDING
    # The chest visible before Challenge Quest is opportunistic. A successful
    # tap shows Congratulations and the helper keeps checking for more. If it
    # is absent or an animation absorbs the tap, quest processing must still
    # continue; only the post-Claim chest sweep below is a strict condition.
    if not _claim_main_chests(bot):
        bot.record("Gift Claims: Soul Beast rương ban đầu không nhận được; "
                   "vẫn tiếp tục mở Challenge Quest")
    if not _open_quests(bot):
        return PENDING

    claimed_any = False
    all_claimed = True
    both_tabs_clear_of_claims = True
    for tab in (DAILY_TASKS, SEASONAL):
        if not _select_quest_tab(bot, tab):
            bot.back(delay=STEP_DELAY)
            return PENDING
        claimed, stuck, saw_claimed, saw_pending = _scan_quest_tab(bot)
        claimed_any = claimed_any or claimed
        both_tabs_clear_of_claims = both_tabs_clear_of_claims and not stuck
        all_claimed = all_claimed and saw_claimed and not saw_pending and not stuck

    if claimed_any:
        if not both_tabs_clear_of_claims:
            bot.record("Gift Claims: Soul Beast đã bấm Claim nhưng chưa xác "
                       "nhận nhận hết Claim ở cả Daily Tasks và Seasonal; "
                       "không ra nhận rương")
            bot.back(delay=STEP_DELAY)
            return PENDING
        bot.sleep(1)
        bot.back(delay=STEP_DELAY)
        if not _main_open(bot):
            bot.record("Gift Claims: Soul Beast Back một lần nhưng chưa về "
                       "màn Challenge Quest")
            return PENDING
        if not _claim_main_chests(bot):
            return PENDING
        bot.record("Gift Claims: Soul Beast đã nhận hết Claim và rương của "
                   "lượt này; DONE_1")
        return DONE_1

    # No Claim was tapped, so only close the Quests popup; do not perform the
    # post-claim chest sequence requested exclusively after a real claim.
    bot.back(delay=STEP_DELAY)
    if all_claimed:
        bot.record("Gift Claims: Soul Beast cả Daily Tasks và Seasonal đều "
                   "toàn bộ Claimed; DONE")
        return DONE
    bot.record("Gift Claims: Soul Beast chưa toàn bộ Claimed; DONE_1 cho cửa "
               "sổ 120s hiện tại")
    return DONE_1


def run(bot) -> bool:
    if (not open_named(bot, GiftScreen.SUPER_VALUE_RETURN)
            or not select_carousel_tab(bot, PAGE, TAB)):
        return False
    outcome = claim_opened(bot)
    return_home(bot)
    return outcome == DONE


TASK = GiftTask(KEY, "Soul of Spiritual Beast", run)
