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
    LIST_HASH_DISTANCE,
    MAX_BAR_STILL_DIFF,
    MAX_BAR_WIDTH,
    MAX_BUTTON,
    MAX_CLAIMS_PER_VIEW,
    MAX_CROP_HALF_HEIGHT,
    MAX_CROP_LEFT,
    MAX_FULL_PASSES,
    MAX_SCROLLS,
    MAX_SELECTED,
    MAX_SELECT_TRIES,
    NAME,
    PARADE_MASK,
    PLUS,
    RETURN_TOP_SWIPE,
    REWARD_REGION,
    SCAN_SWIPE,
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
    """Prefer ``How to get``; otherwise return '+' only as a slider anchor."""
    end = time.monotonic() + WAIT_TIMEOUT
    while True:
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


def _use_parade_masks(bot) -> bool | None:
    """Use all masks; None means there are no masks, not that rewards are DONE."""
    screen = bot.screenshot()
    if bot.find(CONGRATULATIONS, threshold=CONTROL_THRESHOLD,
                screen=screen) is not None:
        bot.record(f"{NAME}: còn Congratulations từ bước Use trước; Back đúng một lần")
        bot.back(delay=STEP_DELAY)
        return True if _wait_after_congratulations(bot) else False

    plus = bot.find(PLUS, threshold=CONTROL_THRESHOLD, screen=screen)
    if plus is None:
        mask = bot.find(PARADE_MASK, threshold=CONTROL_THRESHOLD,
                        screen=screen)
        if mask is None:
            bot.record(f"{NAME}: không thấy Parade Mask; giữ PENDING")
            return False
        bot.record(f"{NAME}: tap Parade Mask")
        bot.tap(*mask, delay=STEP_DELAY)
        result, plus = _wait_mask_result(bot)
        if result == "how_to_get":
            bot.record(f"{NAME}: thấy How to get; không còn Parade Mask để Use; tiếp tục quét Claim")
            bot.back(delay=STEP_DELAY)
            return None
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
        return False
    use = _wait(bot, USE_BUTTON)
    if use is None:
        bot.record(f"{NAME}: không thấy nút Use sau khi chọn tối đa; giữ PENDING")
        bot.back(delay=STEP_DELAY)
        return False
    bot.record(f"{NAME}: tap Use")
    bot.tap(*use, delay=STEP_DELAY)
    if not _close_congratulations_once(bot):
        bot.record(f"{NAME}: chưa thấy Congratulations sau Use; giữ PENDING")
        return False
    return True


def _reward_signature(screen) -> bytes:
    """Animation-tolerant dHash of only the green reward-list frame."""
    height, width = screen.shape[:2]
    x0, y0, x1, y1 = REWARD_REGION
    patch = screen[round(height * y0 / 100):round(height * y1 / 100),
                   round(width * x0 / 100):round(width * x1 / 100)]
    gray = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
    tiny = cv2.resize(gray, (49, 12), interpolation=cv2.INTER_AREA)
    return np.packbits(tiny[:, 1:] > tiny[:, :-1]).tobytes()


def _same_reward_position(before, after) -> bool:
    old = np.frombuffer(_reward_signature(before), dtype=np.uint8)
    new = np.frombuffer(_reward_signature(after), dtype=np.uint8)
    return old.shape == new.shape and int(
        np.unpackbits(np.bitwise_xor(old, new)).sum()) <= LIST_HASH_DISTANCE


def _swipe_to_top(bot) -> bool:
    unchanged = 0
    for _ in range(MAX_SCROLLS):
        before = bot.screenshot()
        bot.swipe_percent(*RETURN_TOP_SWIPE,
                          duration=SLOW_SWIPE_DURATION, delay=STEP_DELAY)
        after = bot.screenshot()
        unchanged = unchanged + 1 if _same_reward_position(before, after) else 0
        if unchanged >= EDGE_CONFIRMATIONS:
            return True
    bot.record(f"{NAME}: chưa xác nhận được đầu danh sách quà")
    return False


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
    for position in range(MAX_SCROLLS + 1):
        bot.record(f"{NAME}: quét vùng quà vị trí "
                   f"{position + 1}/{MAX_SCROLLS + 1}")
        claimed, stuck = _claim_current_view(bot)
        saw_claim = saw_claim or claimed
        if stuck:
            return saw_claim, True, False
        if position >= MAX_SCROLLS:
            break
        before = bot.screenshot()
        bot.swipe_percent(*SCAN_SWIPE,
                          duration=SLOW_SWIPE_DURATION, delay=STEP_DELAY)
        after = bot.screenshot()
        unchanged = unchanged + 1 if _same_reward_position(before, after) else 0
        if unchanged >= EDGE_CONFIRMATIONS:
            return saw_claim, False, True
    return saw_claim, False, False


def _claim_rewards(bot) -> bool:
    """DONE only after a complete top-to-bottom pass with no green Claim."""
    for pass_number in range(1, MAX_FULL_PASSES + 1):
        bot.record(f"{NAME}: bắt đầu lượt quét quà đầy đủ "
                   f"{pass_number}/{MAX_FULL_PASSES}")
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
            bot.record(f"{NAME}: đã quét từ đầu tới cuối, không còn Claim xanh; DONE")
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
    screen = bot.screenshot()
    green_claims = _green_claims(bot, screen)
    gray_claim = _gray_claim_visible(bot, screen)

    if green_claims:
        bot.record(f"{NAME}: vùng quà đã có {len(green_claims)} Claim xanh; "
                   "nhận quà trước, không bấm Parade Mask")
    elif gray_claim and bot.is_daily_done(USE_DONE_KEY):
        bot.log(f"{NAME}: chỉ thấy Claim xám nhưng Parade Mask đã xử lý trong DB; "
                "tiếp tục quét đủ hai biên")
    elif gray_claim:
        bot.record(f"{NAME}: vùng quà chỉ có Claim xám; bắt đầu dùng Parade Mask")
        used = _use_parade_masks(bot)
        if used is False:
            return False
        # Both a successful Use and the explicit How-to-get state mean there
        # is no more mask work in this daily run. Neither one completes the
        # task: every green Claim still has to be exhausted below.
        bot.mark_daily_done(USE_DONE_KEY)
        bot.record(f"{NAME}: DB DONE {USE_DONE_KEY}")
    else:
        bot.record(f"{NAME}: khung hiện tại chưa có Claim xanh/xám; "
                   "vẫn quét từ biên đầu tới biên cuối")
    return _claim_rewards(bot)


def run(bot, task: dict, state: EventState):
    def handle(action, pos, screen):
        if action == ON_HOW_TO_GET:
            bot.record(f"{NAME}: thấy How to get; đóng popup rồi tiếp tục quét Claim")
            bot.back(delay=STEP_DELAY)
            bot.mark_daily_done(USE_DONE_KEY)
            if _run_opened(bot):
                mark_done(bot, KEY)
            return STOP
        if action in (EVENT_OPENED, ON_EVENT):
            if _run_opened(bot):
                mark_done(bot, KEY)
            return STOP
        return None

    run_task(bot, state, NAME, ICON, handle,
             targets=[(HOW_TO_GET, ON_HOW_TO_GET), (TITLE, ON_EVENT)],
             regions={HOW_TO_GET: HOW_TO_GET_REGION, TITLE: TITLE_REGION},
             thresholds={HOW_TO_GET: TITLE_THRESHOLD, TITLE: TITLE_THRESHOLD})

