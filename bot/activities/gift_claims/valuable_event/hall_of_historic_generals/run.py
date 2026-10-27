"""Claim Hall of Historic Generals Daily Tasks scores without confusing Claimed."""
import cv2

from ...common import (GiftTask, close_congratulations, find, find_all,
                       find_reward_chest, return_home, select_carousel_tab)
from ...lobby import open_named
from ...screens import GiftScreen
from ...super_value_return.login_gifts.run import CONGRATULATIONS
from ..named_flow import (ExactFlow, SLOW_SWIPE_DURATION, STEP_DELAY,
                          region_hamming_distance)

KEY = "gift_hall_of_historic_generals"
PAGE = "SuperValueReturn/title"
TAB = "SuperValueReturn/HallOfHistoricGenerals/tab"
CHALLENGE_QUEST = "SuperValueReturn/HallOfHistoricGenerals/challenge_quest"
SCORES_TITLE = "SuperValueReturn/HallOfHistoricGenerals/title_how_to_earn_scores"
CLAIM = "SuperValueReturn/HallOfHistoricGenerals/button_claim"
CLAIMED = "SuperValueReturn/HallOfHistoricGenerals/status_claimed"
PENDING_CONTROLS = (
    "ValuableEvent/SuperValueWeeklyCard/button_go",
    "ValuableEvent/SuperValueWeeklyCard/button_continue",
)

# User-marked green rectangle in the 396x704 reference frame.
REWARD_REGION = (5, 40, 97, 86)
# Main-page chest rectangle from the supplied Hall screenshot. The tap target
# always comes from the shared Login Gifts chest template, never coordinates.
MAIN_CHEST_REGION = (2, 18, 27, 41)
# On the supplied Hall screenshot the shared Login Gifts chest scores 0.6078;
# the strongest match outside this Hall box is 0.4295. Hall has a different
# animated background, so keep a separate conservative threshold.
MAIN_CHEST_THRESHOLD = 0.52
SCAN_SWIPE = (50, 82, 50, 48)
RETURN_TOP_SWIPE = (50, 48, 50, 82)
EDGE_CONFIRMATIONS = 2
CHEST_ABSENCE_CONFIRMATIONS = 2
SAME_DISTANCE = 24
CLAIM_THRESHOLD = 0.72
CLAIMED_THRESHOLD = 0.76
MAX_TAPS_PER_STALLED_CLAIM = 3

# Outcomes consumed by the parent zone. DONE_1 deliberately is not a DB DONE:
# it defers this task until the next complete Claim Gifts invocation.
DONE = "done"
DONE_1 = "done_1"
PENDING = "pending"

FLOW = ExactFlow()


def _button_crop(screen, center, reference_size):
    scale = screen.shape[1] / 396
    width = max(1, round(reference_size[0] * scale))
    height = max(1, round(reference_size[1] * scale))
    x0 = max(0, center[0] - width // 2)
    y0 = max(0, center[1] - height // 2)
    return screen[y0:min(screen.shape[0], y0 + height),
                  x0:min(screen.shape[1], x0 + width)]


def _colour_ratios(crop) -> tuple[float, float]:
    """Return (green-band ratio, low-saturation Claimed-band ratio)."""
    if crop.size == 0:
        return 0.0, 0.0
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    green = ((hsv[..., 0] >= 35) & (hsv[..., 0] <= 90) &
             (hsv[..., 1] >= 60) & (hsv[..., 2] >= 50))
    claimed = ((hsv[..., 1] <= 70) & (hsv[..., 2] >= 50))
    return float(green.mean()), float(claimed.mean())


def _is_green_claim(screen, center) -> bool:
    green, low_saturation = _colour_ratios(
        _button_crop(screen, center, (63, 25)))
    return green >= 0.22 and low_saturation < 0.45


def _is_gray_claimed(screen, center) -> bool:
    green, low_saturation = _colour_ratios(
        _button_crop(screen, center, (65, 24)))
    return green <= 0.08 and low_saturation >= 0.50


def _green_claims(bot, screen) -> list[tuple[int, int]]:
    return [point for point in find_all(
        bot, CLAIM, screen, threshold=CLAIM_THRESHOLD, region=REWARD_REGION)
            if _is_green_claim(screen, point)]


def _gray_claimed(bot, screen) -> list[tuple[int, int]]:
    return [point for point in find_all(
        bot, CLAIMED, screen, threshold=CLAIMED_THRESHOLD,
        region=REWARD_REGION) if _is_gray_claimed(screen, point)]


def _pending_controls(bot, screen) -> bool:
    return any(find(bot, name, screen, threshold=0.70,
                    region=REWARD_REGION) is not None
               for name in PENDING_CONTROLS)


def _main_open(bot, screen=None) -> bool:
    screen = bot.screenshot() if screen is None else screen
    return find(bot, CHALLENGE_QUEST, screen, threshold=0.78,
                region=(55, 30, 100, 55)) is not None


def _confirm_main_chest_absent(bot) -> bool:
    absent = 0
    for attempt in range(CHEST_ABSENCE_CONFIRMATIONS + 2):
        screen = bot.screenshot()
        on_main = _main_open(bot, screen)
        chest = find_reward_chest(bot, screen, region=MAIN_CHEST_REGION,
                                  threshold=MAIN_CHEST_THRESHOLD)
        absent = absent + 1 if on_main and chest is None else 0
        if absent >= CHEST_ABSENCE_CONFIRMATIONS:
            return True
        if attempt + 1 < CHEST_ABSENCE_CONFIRMATIONS + 2:
            bot.sleep(1)
    return False


def _claim_main_chests(bot) -> bool:
    """Claim Hall score chests until the user-marked region is empty."""
    while True:
        bot.check()
        screen = bot.screenshot()
        if not _main_open(bot, screen):
            bot.record("Gift Claims: Hall chưa xác nhận màn Challenge Quest")
            return False
        chest = find_reward_chest(bot, screen, region=MAIN_CHEST_REGION,
                                  threshold=MAIN_CHEST_THRESHOLD)
        if chest is None:
            return True
        bot.record("Gift Claims: Hall thấy rương trong vùng xanh; tap")
        bot.tap(*chest, delay=STEP_DELAY)
        bot.sleep(1)
        for attempt in range(6):
            popup = find(bot, CONGRATULATIONS, bot.screenshot(), threshold=0.78,
                         region=(0, 38, 100, 62))
            if popup is not None:
                bot.record("Gift Claims: Hall thấy Congratulations; Back rồi "
                           "kiểm tra rương tiếp")
                bot.back(delay=STEP_DELAY)
                break
            if attempt + 1 < 6:
                bot.sleep(1)
        else:
            bot.record("Gift Claims: Hall không thấy Congratulations; kiểm "
                       "tra lại vùng rương")
            if _confirm_main_chest_absent(bot):
                bot.record("Gift Claims: Hall rương đã biến mất; hoàn tất lượt")
                return True
            bot.record("Gift Claims: Hall chưa xác nhận rương đã hết; PENDING")
            return False


def _open_scores(bot) -> bool:
    # The score popup opens on Daily Tasks. Seasonal Quests is intentionally
    # outside this Gift Claims flow and is never selected or scanned.
    for attempt in range(4):
        screen = bot.screenshot()
        challenge = find(bot, CHALLENGE_QUEST, screen, threshold=0.78,
                         region=(0, 15, 100, 99))
        if challenge is not None:
            bot.record("Gift Claims: Hall of Historic Generals mở Challenge Quest")
            bot.tap(*challenge, delay=STEP_DELAY)
            break
        if attempt + 1 < 4:
            bot.sleep(STEP_DELAY)
    else:
        bot.record("Gift Claims: Hall of Historic Generals chưa thấy Challenge Quest")
        return False

    for attempt in range(4):
        if find(bot, SCORES_TITLE, bot.screenshot(), threshold=0.78,
                region=(10, 8, 90, 24)) is not None:
            return True
        if attempt + 1 < 4:
            bot.sleep(STEP_DELAY)
    bot.record("Gift Claims: Hall of Historic Generals chưa xác nhận How to Earn Scores")
    bot.back(delay=STEP_DELAY)
    return False


def _swipe(bot, gesture) -> int:
    before = bot.screenshot()
    bot.swipe_percent(*gesture, duration=SLOW_SWIPE_DURATION, delay=STEP_DELAY)
    after = bot.screenshot()
    return region_hamming_distance(before, after, REWARD_REGION)


def _swipe_to_top(bot) -> None:
    unchanged = 0
    while unchanged < EDGE_CONFIRMATIONS:
        bot.check()
        distance = _swipe(bot, RETURN_TOP_SWIPE)
        unchanged = unchanged + 1 if distance <= SAME_DISTANCE else 0
        bot.record("Gift Claims: Hall of Historic Generals về đầu vùng xanh, "
                   f"Hamming {distance}/{SAME_DISTANCE}, không đổi "
                   f"{unchanged}/{EDGE_CONFIRMATIONS}")


def _claim_current_view(bot) -> tuple[bool, bool, bool, bool]:
    """Return claimed_now, stuck, saw_claimed, saw_pending for one viewport."""
    claimed_now = False
    attempted: list[tuple[tuple[int, int], int]] = []

    def attempts_for(point):
        return next((count for old, count in attempted
                     if (point[0] - old[0]) ** 2 +
                     (point[1] - old[1]) ** 2 <= 30 ** 2), 0)

    def note_attempt(point):
        for index, (old, count) in enumerate(attempted):
            if ((point[0] - old[0]) ** 2 +
                    (point[1] - old[1]) ** 2 <= 30 ** 2):
                attempted[index] = (old, count + 1)
                return count + 1
        attempted.append((point, 1))
        return 1

    while True:
        bot.check()
        screen = bot.screenshot()
        green_claims = _green_claims(bot, screen)
        fresh = [point for point in green_claims if attempts_for(point) == 0]
        retry = next((point for point in green_claims
                      if 0 < attempts_for(point) < MAX_TAPS_PER_STALLED_CLAIM),
                     None)
        point = fresh[0] if fresh else retry
        if point is None:
            final = bot.screenshot()
            # Every green Claim in this viewport was offered a full set of
            # paced taps.  We only report it stuck after first trying every
            # other Claim in the same viewport; a lagged line never aborts
            # the rest of this turn's work.
            return (claimed_now, bool(green_claims),
                    bool(_gray_claimed(bot, final)),
                    _pending_controls(bot, final))
        tap_number = note_attempt(point)
        bot.record("Gift Claims: Hall of Historic Generals thấy chữ Claim và "
                   f"dải xanh; tap nhận ({tap_number}/"
                   f"{MAX_TAPS_PER_STALLED_CLAIM} tại vị trí này)")
        bot.tap(*point, delay=STEP_DELAY)
        popup_closed = close_congratulations(bot, attempts=2)
        after = bot.screenshot()
        persists = any((candidate[0] - point[0]) ** 2 +
                       (candidate[1] - point[1]) ** 2 <= 30 ** 2
                       for candidate in _green_claims(bot, after))
        if not persists or popup_closed:
            claimed_now = True
            continue
        bot.record("Gift Claims: Hall of Historic Generals Claim chưa đổi; "
                   "tiếp tục tìm Claim khác trong cùng lượt trước")


def _scan_one_full_pass(bot) -> tuple[bool, bool, bool, bool]:
    """Return claimed_any, stuck, saw_claimed, saw_pending for one full pass."""
    _swipe_to_top(bot)
    claimed_any = False
    saw_claimed = False
    saw_pending = False
    unchanged = 0
    while True:
        bot.check()
        claimed, stuck, claimed_state, pending_state = _claim_current_view(bot)
        claimed_any = claimed_any or claimed
        saw_claimed = saw_claimed or claimed_state
        saw_pending = saw_pending or pending_state
        if stuck:
            bot.record("Gift Claims: Hall of Historic Generals còn Claim xanh "
                       "không bấm được; giữ PENDING")
            return claimed_any, True, saw_claimed, saw_pending
        if claimed:
            unchanged = 0

        distance = _swipe(bot, SCAN_SWIPE)
        unchanged = unchanged + 1 if distance <= SAME_DISTANCE else 0
        bot.record("Gift Claims: Hall of Historic Generals quét vùng xanh, "
                   f"Hamming {distance}/{SAME_DISTANCE}, không đổi "
                   f"{unchanged}/{EDGE_CONFIRMATIONS}")
        if unchanged < EDGE_CONFIRMATIONS:
            continue

        # Re-read the final viewport. A green Claim invalidates the edge until
        # it has been handled and the new layout reaches a stable bottom.
        claimed, stuck, claimed_state, pending_state = _claim_current_view(bot)
        claimed_any = claimed_any or claimed
        saw_claimed = saw_claimed or claimed_state
        saw_pending = saw_pending or pending_state
        if stuck:
            return claimed_any, True, saw_claimed, saw_pending
        if claimed:
            unchanged = 0
            continue
        break

    return claimed_any, False, saw_claimed, saw_pending


def _scan_rewards(bot) -> str:
    claimed_in_cycle = False
    while True:
        bot.check()
        claimed, stuck, saw_claimed, saw_pending = _scan_one_full_pass(bot)
        if stuck:
            return PENDING
        if claimed:
            claimed_in_cycle = True
            bot.record("Gift Claims: Hall of Historic Generals vừa nhận Claim; "
                       "quay lại biên đầu và quét toàn bộ lần nữa")
            continue

        # DONE_1 is allowed only after a complete top-to-bottom verification
        # pass found zero Claim buttons following one or more claiming passes.
        if claimed_in_cycle:
            bot.record("Gift Claims: Hall of Historic Generals đã quét sạch "
                       "từ đầu tới cuối, không còn Claim; DONE_1, kiểm tra lại "
                       "ở vòng Claim Gifts sau")
            return DONE_1
        if saw_claimed and not saw_pending:
            bot.record("Gift Claims: Hall of Historic Generals toàn bộ nút là "
                       "Claimed kèm dải xám; DONE")
            return DONE
        if saw_claimed or saw_pending:
            bot.record("Gift Claims: Hall of Historic Generals chưa phải toàn "
                       "bộ Claimed và lượt này không nhận Claim; giữ PENDING")
            return PENDING
        bot.record("Gift Claims: Hall of Historic Generals không nhận diện được "
                   "trạng thái hàng; giữ PENDING")
        return PENDING


def claim_opened(bot) -> str:
    """Process an already selected Hall tab and return DONE/DONE_1/PENDING."""
    if not _open_scores(bot):
        return PENDING
    outcome = _scan_rewards(bot)
    bot.back(delay=STEP_DELAY)
    if outcome == DONE_1:
        if not _main_open(bot):
            bot.record("Gift Claims: Hall Back nhưng chưa về màn Challenge Quest")
            return PENDING
        if not _claim_main_chests(bot):
            return PENDING
        bot.record("Gift Claims: Hall đã quét hết Claim và nhận/kiểm tra hết "
                   "rương; chuyển nhiệm vụ tiếp theo")
    return outcome


def run(bot) -> bool:
    if (not open_named(bot, GiftScreen.SUPER_VALUE_RETURN)
            or not select_carousel_tab(bot, PAGE, TAB)):
        return False
    outcome = claim_opened(bot)
    return_home(bot)
    return outcome == DONE


TASK = GiftTask(KEY, "Hall of Historic Generals", run)
