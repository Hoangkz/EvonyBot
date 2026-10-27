"""Use every Parade Mask and claim every green Revelry Carnival reward.

The reward list is searched and scrolled only inside the user-marked green
frame.  A Claim candidate must pass both template matching and an HSV green
test, so the visually similar grey Claim button is never pressed.
"""
import cv2
import numpy as np
import time

from ...daily_activities.alliance_vip.constants import MAX_SLIDER
from ..common import EVENT_OPENED, STOP, EventState, mark_done, run_task
from .constants import (
    CLAIM_GRAY,
    CLAIM_GREEN,
    CLAIM_THRESHOLD,
    CONGRATULATIONS,
    CONTROL_THRESHOLD,
    EDGE_CONFIRMATIONS,
    GREEN_HUE,
    GREEN_MIN_RATIO,
    GREEN_MIN_SATURATION,
    GREEN_MIN_VALUE,
    HOW_TO_GET,
    HOW_TO_GET_REGION,
    ICON,
    KEY,
    MAX_BAR_STILL_DIFF,
    MAX_BAR_WIDTH,
    MAX_BUTTON,
    MAX_CLAIMS_PER_VIEW,
    MAX_CROP_HALF_HEIGHT,
    MAX_CROP_LEFT,
    MAX_FULL_PASSES,
    MAX_SELECTED,
    MAX_SELECT_TRIES,
    NAME,
    PARADE_MASK,
    PARADE_MASK_DONE,
    PARADE_MASK_DONE_REGION,
    PARADE_MASK_EMPTY_MARKER,
    PARADE_MASK_OPEN_DELAY,
    PLUS,
    RETURN_TOP_SWIPE,
    RETURN_TOP_SWIPE_FALLBACKS,
    REWARD_REGION,
    REWARD_STATIC_REGION,
    REWARD_STATIC_SAME,
    SCAN_SWIPE,
    SCAN_SWIPE_FALLBACKS,
    SLOW_SWIPE_DURATION,
    STEP_DELAY,
    TITLE,
    TITLE_REGION,
    TITLE_THRESHOLD,
    USE_BUTTON,
    USE_DONE_KEY,
    WAIT_TIMEOUT,
)

ON_EVENT = "on_revelry_carnival"
ON_HOW_TO_GET = "on_how_to_get"
ON_PARADE_MASK_DONE = "on_parade_mask_done"


def _wait(bot, template, *, threshold=CONTROL_THRESHOLD,
          region=(0, 0, 100, 100), timeout=WAIT_TIMEOUT):
    end = time.monotonic() + timeout
    while True:
        pos = bot.find(template, threshold=threshold, region=region)
        if pos is not None:
            return pos
        if time.monotonic() >= end:
            return None
        bot.sleep(min(1, max(0, end - time.monotonic())))


def _wait_mask_result(bot):
    """Wait for either supplied empty-Mask marker or the quantity popup."""
    end = time.monotonic() + WAIT_TIMEOUT
    while True:
        screen = bot.screenshot()
        exhausted = bot.find(PARADE_MASK_DONE, threshold=TITLE_THRESHOLD,
                             screen=screen, region=PARADE_MASK_DONE_REGION)
        if exhausted is not None:
            return "done", exhausted
        empty_marker = bot.find(PARADE_MASK_EMPTY_MARKER,
                                threshold=CONTROL_THRESHOLD, screen=screen,
                                region=PARADE_MASK_DONE_REGION)
        if empty_marker is not None:
            return "done", empty_marker
        plus = bot.find(PLUS, threshold=CONTROL_THRESHOLD)
        if plus is not None:
            return "plus", plus
        how_to_get = bot.find(HOW_TO_GET, threshold=TITLE_THRESHOLD,
                              region=HOW_TO_GET_REGION)
        if how_to_get is not None:
            return "how_to_get", how_to_get
        if time.monotonic() >= end:
            return None, None
        bot.sleep(min(1, max(0, end - time.monotonic())))


def _template_matches(bot, screen, template, *, threshold, region):
    """Return non-overlapping template centres, in top-to-bottom order."""
    tpl = bot._template(template)
    height, width = screen.shape[:2]
    x0, y0, x1, y1 = region
    left, top = round(width * x0 / 100), round(height * y0 / 100)
    area = screen[top:round(height * y1 / 100),
                  left:round(width * x1 / 100)]
    if area.shape[0] < tpl.shape[0] or area.shape[1] < tpl.shape[1]:
        return []
    scores = cv2.matchTemplate(area, tpl, cv2.TM_CCOEFF_NORMED)
    th, tw = tpl.shape[:2]
    matches = []
    while True:
        _, score, _, (x, y) = cv2.minMaxLoc(scores)
        if score < threshold:
            break
        matches.append((left + x + tw // 2, top + y + th // 2))
        cv2.rectangle(scores,
                      (max(0, x - tw), max(0, y - th)),
                      (min(scores.shape[1] - 1, x + tw),
                       min(scores.shape[0] - 1, y + th)),
                      -1.0, thickness=-1)
    return sorted(matches, key=lambda point: (point[1], point[0]))


def _green_claim(bot, screen, center) -> bool:
    """Classify the matched Claim by colour, independently of its text."""
    tpl = bot._template(CLAIM_GREEN)
    height, width = tpl.shape[:2]
    crop = bot.crop(screen, center[0] - width // 2,
                    center[1] - height // 2, width, height)
    if crop.size == 0:
        return False
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    green = ((hsv[..., 0] >= GREEN_HUE[0]) &
             (hsv[..., 0] <= GREEN_HUE[1]) &
             (hsv[..., 1] >= GREEN_MIN_SATURATION) &
             (hsv[..., 2] >= GREEN_MIN_VALUE))
    ratio = float(green.mean())
    saturation = float(hsv[..., 1].mean())
    bot.log(f"{NAME}: Claim green ratio {ratio:.2f}, saturation {saturation:.0f}")
    return ratio >= GREEN_MIN_RATIO


def _green_claims(bot, screen):
    candidates = _template_matches(
        bot, screen, CLAIM_GREEN, threshold=CLAIM_THRESHOLD,
        region=REWARD_REGION)
    return [point for point in candidates if _green_claim(bot, screen, point)]


def _gray_claim_visible(bot, screen) -> bool:
    """True only for a grey Claim inside the user-approved reward frame."""
    return bot.find(CLAIM_GRAY, threshold=CLAIM_THRESHOLD, screen=screen,
                    region=REWARD_REGION) is not None


def _wait_after_congratulations(bot, timeout=WAIT_TIMEOUT) -> bool:
    """Wait after one Back until the reward page is no longer obscured.

    The popup is closed exactly once.  Afterwards we wait for either its
    disappearance or a crisp green/grey Claim control; we never press Back a
    second time and accidentally leave Revelry Carnival.
    """
    end = time.monotonic() + timeout
    while True:
        screen = bot.screenshot()
        popup = bot.find(CONGRATULATIONS, threshold=CONTROL_THRESHOLD,
                         screen=screen)
        claims_visible = bool(_green_claims(bot, screen) or
                              _gray_claim_visible(bot, screen))
        if popup is None or claims_visible:
            bot.record(f"{NAME}: Congratulations đã đóng; danh sách quà đã rõ")
            return True
        if time.monotonic() >= end:
            bot.record(f"{NAME}: Congratulations vẫn che danh sách sau khi Back; giữ PENDING")
            return False
        bot.sleep(min(1, max(0, end - time.monotonic())))


def _close_congratulations_once(bot) -> bool:
    """Press Back once for a visible Congratulations and wait for it to clear."""
    if _wait(bot, CONGRATULATIONS, timeout=3) is None:
        return False
    bot.record(f"{NAME}: thấy Congratulations; Back đúng một lần")
    bot.back(delay=STEP_DELAY)
    return _wait_after_congratulations(bot)


def _select_max(bot, plus=None) -> bool:
    """Use the Max button first, then Alliance VIP's slider-end fallback."""
    for attempt in range(1, MAX_SELECT_TRIES + 1):
        screen = bot.screenshot()
        if bot.find(MAX_SELECTED, threshold=CONTROL_THRESHOLD,
                    screen=screen) is not None:
            bot.record(f"{NAME}: đã xác nhận thanh số lượng ở mức tối đa")
            return True

        maximum = bot.find(MAX_BUTTON, threshold=CONTROL_THRESHOLD,
                           screen=screen)
        if maximum is not None:
            bot.record(f"{NAME}: tap nút Max")
            bot.tap(*maximum, delay=STEP_DELAY)
            continue

        # Same measured fallback as Alliance VIP. The '+' may load after the
        # first wait, so refresh it here; its absence earlier is not terminal.
        plus = (bot.find(PLUS, threshold=CONTROL_THRESHOLD,
                         screen=screen) or plus)
        if plus is None:
            bot.record(f"{NAME}: chưa thấy dấu + để dùng thanh trượt "
                       f"({attempt}/{MAX_SELECT_TRIES}); vẫn tiếp tục flow Max")
            bot.sleep(STEP_DELAY)
            continue
        left = max(0, plus[0] - MAX_CROP_LEFT)
        top = max(0, plus[1] - MAX_CROP_HALF_HEIGHT)
        crop = bot.crop(screen, left, top, MAX_CROP_LEFT,
                        MAX_CROP_HALF_HEIGHT * 2)
        slider = bot.find(MAX_SLIDER, threshold=CONTROL_THRESHOLD,
                          screen=crop)
        if slider is None:
            bot.record(f"{NAME}: chưa thấy Max hoặc đầu thanh "
                       f"({attempt}/{MAX_SELECT_TRIES})")
            bot.sleep(STEP_DELAY)
            continue
        bar = (max(0, plus[0] - MAX_BAR_WIDTH), top,
               MAX_BAR_WIDTH, MAX_CROP_HALF_HEIGHT * 2)
        before = bot.crop(screen, *bar)
        bot.record(f"{NAME}: dùng vị trí đầu thanh theo logic Alliance VIP")
        bot.tap(left + slider[0], top + slider[1], delay=STEP_DELAY)
        after = bot.screenshot()
        if bot.find(MAX_SELECTED, threshold=CONTROL_THRESHOLD,
                    screen=after) is not None:
            return True
        if (attempt >= 2 and before.shape == bot.crop(after, *bar).shape and
                float(cv2.absdiff(before, bot.crop(after, *bar)).mean()) <
                MAX_BAR_STILL_DIFF):
            bot.record(f"{NAME}: thanh không đổi; số lượng hiện tại đã là tối đa")
            return True
    return False


def _use_parade_masks(bot) -> str:
    """Tap Parade Mask once: return ``done``, ``used`` or ``pending``.

    A clear reward list never completes Revelry.  Only the exact exhausted
    marker shown after this tap completes the task.
    """
    screen = bot.screenshot()
    if bot.find(CONGRATULATIONS, threshold=CONTROL_THRESHOLD,
                screen=screen) is not None:
        bot.record(f"{NAME}: còn Congratulations từ bước Use trước; Back đúng một lần")
        bot.back(delay=STEP_DELAY)
        return "used" if _wait_after_congratulations(bot) else "pending"

    plus = bot.find(PLUS, threshold=CONTROL_THRESHOLD, screen=screen)
    if plus is None:
        mask = bot.find(PARADE_MASK, threshold=CONTROL_THRESHOLD,
                        screen=screen)
        if mask is None:
            bot.record(f"{NAME}: không thấy Parade Mask để kiểm tra dấu DONE; giữ PENDING")
            return "pending"
        bot.record(f"{NAME}: tap Parade Mask; chờ {PARADE_MASK_OPEN_DELAY:g}s "
                   "để kiểm tra popup Use/DONE tải xong")
        bot.tap(*mask, delay=PARADE_MASK_OPEN_DELAY)
        result, plus = _wait_mask_result(bot)
        if result == "done":
            bot.record(f"{NAME}: sau khi bấm Parade Mask thấy dấu hết Mask; DONE")
            return "done"
        if result == "how_to_get":
            bot.record(f"{NAME}: chỉ thấy title How to get nhưng chưa thấy ảnh dấu DONE; giữ PENDING")
            bot.back(delay=STEP_DELAY)
            return "pending"
        if result == "plus":
            bot.record(f"{NAME}: popup số lượng đã mở (thấy dấu +)")
        else:
            # Only How to get is a terminal result. If it is absent, continue
            # the ordinary Max/Use flow even when '+' was not recognized.
            plus = None
            bot.record(f"{NAME}: không thấy How to get; tiếp tục flow Max/Use")

    if not _select_max(bot, plus):
        bot.record(f"{NAME}: chưa xác nhận được mức tối đa; giữ PENDING")
        bot.back(delay=STEP_DELAY)
        return "pending"
    use = _wait(bot, USE_BUTTON)
    if use is None:
        bot.record(f"{NAME}: không thấy nút Use sau khi chọn tối đa; giữ PENDING")
        bot.back(delay=STEP_DELAY)
        return "pending"
    bot.record(f"{NAME}: tap Use")
    bot.tap(*use, delay=STEP_DELAY)
    if not _close_congratulations_once(bot):
        bot.record(f"{NAME}: chưa thấy Congratulations sau Use; giữ PENDING")
        return "pending"
    return "used"


def _check_parade_mask_done(bot) -> bool:
    """Re-open Parade Mask after a clean sweep and require its exact text."""
    screen = bot.screenshot()
    mask = bot.find(PARADE_MASK, threshold=CONTROL_THRESHOLD, screen=screen)
    if mask is None:
        bot.record(f"{NAME}: không thấy Parade Mask để kiểm tra dấu DONE; giữ PENDING")
        return False
    bot.record(f"{NAME}: quà đã sạch; bấm lại Parade Mask để tìm dòng "
               "'You can get items from:' hoặc marker hết Mask")
    bot.tap(*mask, delay=PARADE_MASK_OPEN_DELAY)
    result, _pos = _wait_mask_result(bot)
    if result == "done":
        bot.record(f"{NAME}: sau lượt Claim đã thấy marker hết Parade Mask; DONE")
        return True
    bot.record(f"{NAME}: bấm lại Parade Mask nhưng chưa thấy "
               "marker hết Mask; giữ PENDING")
    bot.back(delay=STEP_DELAY)
    return False


def _reward_static_similarity(before, after) -> float:
    """Similarity of the non-animated level strip at the left of the list.

    Live testing on 21513 showed a stationary LV3/LV4 list with a full-frame
    hash change of 139 bits because locks and rewards animate.  The level strip
    remained 0.92 similar, while a true LV1/LV2 -> LV3/LV4 scroll scored 0.49.
    """
    if before.shape[:2] != after.shape[:2]:
        return 0.0
    height, width = before.shape[:2]
    x0, y0, x1, y1 = REWARD_STATIC_REGION
    left, top = round(width * x0 / 100), round(height * y0 / 100)
    right, bottom = round(width * x1 / 100), round(height * y1 / 100)
    old = before[top:bottom, left:right]
    new = after[top:bottom, left:right]
    if old.size == 0 or old.shape != new.shape:
        return 0.0
    return float(np.nan_to_num(
        cv2.matchTemplate(old, new, cv2.TM_CCOEFF_NORMED)[0, 0], nan=0.0))


def _same_reward_position(before, after) -> bool:
    return _reward_static_similarity(before, after) >= REWARD_STATIC_SAME


def _scroll_reward_frame(bot, direction: str, primary, fallbacks) -> bool:
    """Scroll inside the green frame; recover from a swallowed centre swipe.

    A stationary primary gesture alone is not an edge.  Some Revelry rows
    intercept the finger at x=50 on particular levels, even though the list
    below remains scrollable.  Test each measured alternate path in the same
    green frame before reporting that this one edge-check did not move.
    """
    gestures = (primary, *fallbacks)
    for probe, gesture in enumerate(gestures, 1):
        bot.check()
        before = bot.screenshot()
        bot.swipe_percent(*gesture, duration=SLOW_SWIPE_DURATION,
                          delay=STEP_DELAY)
        after = bot.screenshot()
        similarity = _reward_static_similarity(before, after)
        moved = similarity < REWARD_STATIC_SAME
        bot.record(f"{NAME}: lướt {direction} trong khung quà {gesture}, "
                   f"ảnh tĩnh LV {similarity:.3f}/{REWARD_STATIC_SAME:.2f}, đường "
                   f"{probe}/{len(gestures)} {'đã di chuyển' if moved else 'không đổi'}")
        if moved:
            return True
    return False


def _swipe_to_top(bot) -> bool:
    unchanged = 0
    swipe = 0
    while unchanged < EDGE_CONFIRMATIONS:
        bot.check()
        swipe += 1
        moved = _scroll_reward_frame(
            bot, "lên", RETURN_TOP_SWIPE, RETURN_TOP_SWIPE_FALLBACKS)
        unchanged = 0 if moved else unchanged + 1
        bot.record(f"{NAME}: kiểm tra đầu danh sách lần {swipe}; không đổi "
                   f"{unchanged}/{EDGE_CONFIRMATIONS}")
    bot.record(f"{NAME}: đã xác nhận đầu danh sách quà")
    return True


def _claim_current_view(bot):
    claimed = False
    for tap_number in range(1, MAX_CLAIMS_PER_VIEW + 1):
        bot.check()
        screen = bot.screenshot()
        claims = _green_claims(bot, screen)
        if not claims:
            # Keep an explicit grey lookup in diagnostics. It never authorizes
            # a tap and therefore cannot be confused with the green state.
            if bot.find(CLAIM_GRAY, threshold=CLAIM_THRESHOLD, screen=screen,
                        region=REWARD_REGION) is not None:
                bot.log(f"{NAME}: chỉ thấy Claim xám trong khung, bỏ qua")
            return claimed, False
        point = claims[0]
        claimed = True
        bot.record(f"{NAME}: tap Claim xanh trong vùng giới hạn "
                   f"({tap_number}/{MAX_CLAIMS_PER_VIEW})")
        bot.tap(*point, delay=STEP_DELAY)
        if not _close_congratulations_once(bot):
            # A lagging button may disappear without the popup being matched.
            # Re-scan a fresh frame, but do not blindly press the same point.
            bot.record(f"{NAME}: chưa xác nhận được Congratulations sau Claim; chụp lại danh sách")

    remains = bool(_green_claims(bot, bot.screenshot()))
    return claimed, remains


def _scan_full_list(bot):
    saw_claim = False
    unchanged = 0
    position = 0
    while True:
        bot.check()
        position += 1
        bot.record(f"{NAME}: quét vùng quà vị trí {position}")
        claimed, stuck = _claim_current_view(bot)
        saw_claim = saw_claim or claimed
        if stuck:
            return saw_claim, True, False
        moved = _scroll_reward_frame(
            bot, "xuống", SCAN_SWIPE, SCAN_SWIPE_FALLBACKS)
        unchanged = 0 if moved else unchanged + 1
        bot.record(f"{NAME}: kiểm tra cuối danh sách; không đổi "
                   f"{unchanged}/{EDGE_CONFIRMATIONS}")
        if unchanged >= EDGE_CONFIRMATIONS:
            return saw_claim, False, True


def _claim_rewards(bot) -> bool:
    """Return only when a complete pass has no green Claim; not task DONE."""
    for pass_number in range(1, MAX_FULL_PASSES + 1):
        if pass_number == 1:
            # Opening Revelry already presents a valid reward viewport.  Do
            # not waste it by first dragging upward: detect and claim the
            # visible green controls immediately, then continue downward only
            # if this viewport is clear.
            bot.record(f"{NAME}: vừa vào màn; quét Claim ngay ở khung hiện tại "
                       "trước khi lướt")
        else:
            bot.record(f"{NAME}: bắt đầu lượt quét lại {pass_number}/{MAX_FULL_PASSES}; "
                       "trở về đầu danh sách")
            if not _swipe_to_top(bot):
                return False
        saw_claim, stuck, bottom = _scan_full_list(bot)
        if stuck:
            bot.record(f"{NAME}: Claim xanh vẫn còn sau giới hạn bấm; giữ PENDING")
            return False
        if not bottom:
            bot.record(f"{NAME}: chưa xác nhận được cuối danh sách quà; giữ PENDING")
            return False
        if not saw_claim:
            bot.record(f"{NAME}: đã quét từ đầu tới cuối, không còn Claim xanh; "
                       "tiếp tục kiểm tra Parade Mask")
            return True
        bot.record(f"{NAME}: vừa nhận quà; quét lại toàn bộ trước khi DONE")
    bot.record(f"{NAME}: chưa có lượt quét sạch Claim xanh; giữ PENDING")
    return False


def _run_opened(bot) -> bool:
    if _wait(bot, TITLE, threshold=TITLE_THRESHOLD,
             region=TITLE_REGION) is None:
        bot.record(f"{NAME}: icon đã bấm nhưng không thấy đúng title; giữ PENDING")
        bot.back(delay=STEP_DELAY)
        return False
    bot.record(f"{NAME}: đã xác nhận đúng title")
    # Always sweep the complete green reward frame first.  A grey button in
    # the first viewport does not prove there is no green Claim farther down.
    if not _claim_rewards(bot):
        return False

    if bot.is_daily_done(USE_DONE_KEY):
        return _check_parade_mask_done(bot)

    outcome = _use_parade_masks(bot)
    if outcome == "done":
        return True
    if outcome != "used":
        return False
    bot.mark_daily_done(USE_DONE_KEY)
    bot.record(f"{NAME}: DB DONE {USE_DONE_KEY}")

    # A successful Max/Use can reveal rewards farther down.  Exhaust them
    # before tapping Parade Mask again for the only terminal marker.
    if not _claim_rewards(bot):
        return False
    return _check_parade_mask_done(bot)


def run(bot, task: dict, state: EventState):
    def handle(action, pos, screen):
        if action in (ON_PARADE_MASK_DONE, ON_HOW_TO_GET):
            # A stale popup (or one the player opened manually) is not proof
            # that this run has swept every green Claim and then re-opened
            # Parade Mask.  Return to the event and perform that full
            # verification path; only _check_parade_mask_done may finish it.
            bot.record(f"{NAME}: thấy popup Parade Mask ngoài flow kiểm tra; "
                       "không DONE trực tiếp, quay lại quét Claim rồi xác nhận lại")
            bot.back(delay=STEP_DELAY)
            if _run_opened(bot):
                mark_done(bot, KEY)
            return STOP
        if action in (EVENT_OPENED, ON_EVENT):
            if _run_opened(bot):
                mark_done(bot, KEY)
            return STOP
        return None

    run_task(bot, state, NAME, ICON, handle,
             targets=[(PARADE_MASK_DONE, ON_PARADE_MASK_DONE),
                      (HOW_TO_GET, ON_HOW_TO_GET), (TITLE, ON_EVENT)],
             regions={PARADE_MASK_DONE: PARADE_MASK_DONE_REGION,
                      HOW_TO_GET: HOW_TO_GET_REGION, TITLE: TITLE_REGION},
             thresholds={PARADE_MASK_DONE: TITLE_THRESHOLD,
                         HOW_TO_GET: TITLE_THRESHOLD, TITLE: TITLE_THRESHOLD})

