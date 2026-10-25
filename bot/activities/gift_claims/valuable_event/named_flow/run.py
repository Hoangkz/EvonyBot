"""Shared two-zone processing for Valuable Event and Super Value Return.

The top strip (roughly y=50..125) is navigation only.  Reward controls are
searched below y=125, so a decorative chest in the tab strip can never be
mistaken for a claim button.
"""
from dataclasses import dataclass
from typing import Callable

import cv2
import numpy as np

from ...common import (ClaimReport, TEXT_CLAIM_CONTROLS, back_if_close_x,
                       claim_fixed_controls, claim_sparkles,
                       close_congratulations, find, return_home,
                       select_carousel_tab, tap_claims)
from ...lobby import open_named

TOP_CAROUSEL = (0, 7, 100, 19)
# Fingerprint only the static task-name band. Artwork above it can animate
# while the horizontal carousel itself is stationary.
CAROUSEL_STABLE_BAND = (0, 12, 100, 18)
CAROUSEL_EDGE_CONFIRMATIONS = 2
CAROUSEL_SAME_DISTANCE = 16
# Task labels must be a strong visual match. A full carousel sweep that finds
# no label is counted by scan.run_zone; only three complete misses become DONE.
TASK_TAB_THRESHOLD = 0.82
# 125 / 704 = 17.75%. Keep the complete lower page, including bottom claims.
LOWER_CONTENT = (0, 18, 100, 99)
QUIET_ROUNDS = 3
STEP_DELAY = 1.0
SLOW_SWIPE_DURATION = 1.0


def carousel_signature(screen) -> bytes:
    """Animation-tolerant dHash of the task-name band in the top strip."""
    height, width = screen.shape[:2]
    x0, y0, x1, y1 = CAROUSEL_STABLE_BAND
    patch = cv2.cvtColor(
        screen[round(height * y0 / 100):round(height * y1 / 100),
               round(width * x0 / 100):round(width * x1 / 100)],
        cv2.COLOR_BGR2GRAY,
    )
    tiny = cv2.resize(patch, (49, 10), interpolation=cv2.INTER_AREA)
    return np.packbits(tiny[:, 1:] > tiny[:, :-1]).tobytes()


def same_carousel_position(before: bytes, after: bytes,
                           max_distance=CAROUSEL_SAME_DISTANCE) -> bool:
    """True when two settled label bands represent the same position."""
    old = np.frombuffer(before, dtype=np.uint8)
    new = np.frombuffer(after, dtype=np.uint8)
    return old.shape == new.shape and int(
        np.unpackbits(np.bitwise_xor(old, new)).sum()) <= max_distance


def carousel_moved(before, after) -> bool:
    """Return whether the named-tab strip moved between settled frames."""
    return not same_carousel_position(
        carousel_signature(before), carousel_signature(after))


@dataclass(frozen=True)
class ExactFlow:
    """Stable controls and terminal markers for one rotating event."""

    navigation: tuple[str, ...] = ()
    # Optional per-template tap offsets for navigation anchors. This lets a
    # text-only crop point at the control immediately above or beside it.
    navigation_offsets: tuple[tuple[int, int], ...] = ()
    navigation_first_match: bool = False
    claims: tuple[str, ...] = ()
    done: tuple[str, ...] = ()
    opened: tuple[str, ...] = ()
    congratulations_done: bool = False
    absence_done: bool = False
    claim_offset: tuple[int, int] = (0, 0)
    claim_region: tuple[int, int, int, int] = LOWER_CONTENT
    # Full-button captures can share most of their frame with adjacent paid
    # offers. Individual flows may require a stricter score before tapping.
    claim_threshold: float = 0.72
    fallback_tap: tuple[int, int] | None = None
    navigation_threshold: float = 0.72
    scroll_claims: bool = False
    # Per-event vertical list geometry.  Defaults preserve the older flows;
    # events with a bounded task panel can keep the whole gesture and the
    # movement check inside that panel.
    scroll_start: tuple[int, int] = (50, 90)
    scroll_end: tuple[int, int] = (50, 55)
    scroll_region: tuple[int, int, int, int] = LOWER_CONTENT
    max_scroll_pages: int = 6
    skip: bool = False
    # Optional page-specific setup which must be verified before claims.
    prepare: Callable[[object], bool] | None = None


def find_any(bot, templates: tuple[str, ...], screen=None, *,
             region=LOWER_CONTENT, threshold=0.72):
    """Return the first matched named template and its centre."""
    screen = bot.screenshot() if screen is None else screen
    for name in templates:
        pos = find(bot, name, screen, threshold=threshold, region=region)
        if pos is not None:
            return name, pos
    return None


def _wait_any(bot, templates: tuple[str, ...], *, attempts=4,
              region=LOWER_CONTENT, threshold=0.72):
    if not templates:
        return None
    for attempt in range(attempts):
        hit = find_any(bot, templates, region=region, threshold=threshold)
        if hit is not None:
            return hit
        if attempt + 1 < attempts:
            bot.sleep(STEP_DELAY)
    return None


def _done(bot, flow: ExactFlow) -> bool:
    return _wait_any(bot, flow.done, attempts=1) is not None


def _tap_navigation(bot, flow: ExactFlow) -> bool:
    """Open each supplied lower-page subview, using the one approved fallback."""
    acted = False
    for index, template in enumerate(flow.navigation):
        hit = _wait_any(bot, (template,), attempts=4,
                        threshold=flow.navigation_threshold)
        if hit is None:
            continue
        bot.record(f"Gift Claims: tap navigation {hit[0]}")
        offset = (flow.navigation_offsets[index]
                  if index < len(flow.navigation_offsets) else (0, 0))
        screen = bot.screenshot()
        scale = screen.shape[1] / 396
        target = (round(hit[1][0] + offset[0] * scale),
                  round(hit[1][1] + offset[1] * scale))
        bot.tap(*target, delay=STEP_DELAY)
        acted = True
        if flow.navigation_first_match:
            break
    if not acted and flow.fallback_tap is not None:
        bot.record("Gift Claims: không thấy nút điều hướng; dùng fallback được cấu hình "
                   f"x={flow.fallback_tap[0]} y={flow.fallback_tap[1]}")
        bot.tap(*flow.fallback_tap, delay=STEP_DELAY)
        acted = True
    return acted


def process_exact(bot, flow: ExactFlow) -> bool:
    """Run one selected lower panel and return only on its explicit DONE rule."""
    if flow.skip:
        bot.record("Gift Claims: sự kiện được cấu hình bỏ qua; DONE hôm nay")
        return True

    opened_missing = bool(flow.opened and
                          _wait_any(bot, flow.opened, attempts=4) is None)
    if opened_missing:
        bot.log("Gift Claims: tab đã tap nhưng chưa thấy dấu hiệu trang con")

    if flow.prepare is not None and not flow.prepare(bot):
        return False

    if _done(bot, flow):
        return True
    navigated = _tap_navigation(bot, flow)
    if _done(bot, flow):
        return True

    pages = flow.max_scroll_pages if flow.scroll_claims else 1
    saw_claim = False
    reached_scroll_end = not flow.scroll_claims
    for page in range(pages):
        blocked: set[tuple[str, int, int]] = set()
        while True:
            bot.check()
            screen = bot.screenshot()
            hit = find_any(bot, flow.claims, screen, region=flow.claim_region,
                           threshold=flow.claim_threshold)
            if hit is None:
                break
            name, pos = hit
            signature = (name, round(pos[0] / 20), round(pos[1] / 20))
            if signature in blocked:
                break
            blocked.add(signature)
            saw_claim = True
            bot.record(f"Gift Claims: tap exact claim {name}")
            scale = screen.shape[1] / 396
            target = (round(pos[0] + flow.claim_offset[0] * scale),
                      round(pos[1] + flow.claim_offset[1] * scale))
            bot.tap(*target, delay=STEP_DELAY)
            if close_congratulations(bot, attempts=3):
                bot.record(f"Gift Claims: {name} -> Congratulations")
                if flow.congratulations_done:
                    return True
            if _done(bot, flow):
                return True

        if not flow.scroll_claims or page + 1 >= pages:
            break
        before = bot.screenshot()
        bot.swipe_percent(*flow.scroll_start, *flow.scroll_end,
                          duration=SLOW_SWIPE_DURATION, delay=STEP_DELAY)
        # Re-check at every list position. A terminal row may be visible only
        # midway through the green reward frame and would otherwise be scrolled
        # past.
        if _done(bot, flow):
            return True
        after = bot.screenshot()
        height, width = before.shape[:2]
        x0, y0, x1, y1 = flow.scroll_region
        left, top = round(width * x0 / 100), round(height * y0 / 100)
        right, bottom = round(width * x1 / 100), round(height * y1 / 100)
        before_list = before[top:bottom, left:right]
        after_list = after[top:bottom, left:right]
        if float(cv2.absdiff(before_list, after_list).mean()) < 0.5:
            reached_scroll_end = True
            bot.record("Gift Claims: danh sách đã tới cuối; dừng lướt")
            break

    if _done(bot, flow):
        return True
    if (flow.absence_done and reached_scroll_end
            and _wait_any(bot, flow.claims, attempts=2,
                          region=flow.claim_region,
                          threshold=flow.claim_threshold) is None):
        bot.record("Gift Claims: không còn nút nhận trong vùng được cấu hình; DONE")
        return True
    if flow.scroll_claims and not reached_scroll_end:
        bot.record("Gift Claims: đã chạm giới hạn lướt nhưng chưa xác nhận đáy; giữ PENDING")
    if flow.scroll_claims and saw_claim:
        # A list can finish with its terminal Go/Continue below the current
        # viewport. Return to the top once and verify it rather than guessing.
        bot.swipe_percent(50, 55, 50, 90,
                          duration=SLOW_SWIPE_DURATION, delay=STEP_DELAY)
        if _done(bot, flow):
            return True
    if navigated or opened_missing:
        # Đã đi vào một lớp con nhưng không nhận diện được trạng thái kết thúc: chỉ Back đúng một
        # lần về trang event cha. Không gọi return_home ở đây, để vòng carousel tiếp tục xử lý các
        # nhiệm vụ còn lại mà không thoát ra ngoài thành rồi mở lại.
        bot.record("Gift Claims: không nhận diện được trạng thái nhiệm vụ; Back một lần về trang event")
        bot.back(delay=STEP_DELAY)
    return False


def run_carousel_exact(bot, screen_name, page: str, tab: str,
                       flow: ExactFlow) -> bool:
    """Standalone exact task entry used by tests and manual task runs."""
    if not open_named(bot, screen_name):
        return False
    if not select_carousel_tab(bot, page, tab):
        bot.record("Gift Claims: không nhận diện được tab nhiệm vụ; Back đúng một lần")
        bot.back(delay=STEP_DELAY)
        return False
    completed = process_exact(bot, flow)
    # Khi PENDING, process_exact đã Back một lớp nếu có trang con. Không return_home rồi mở lại,
    # tránh bật tắt Valuable Event liên tục. Chỉ nhiệm vụ đã DONE mới kết thúc entry độc lập ở home.
    if completed:
        return_home(bot)
    return completed


def process_lower(bot, navigation: tuple[str, ...],
                  claims: tuple[str, ...]) -> tuple[ClaimReport, int]:
    """Claim known controls first and re-check them after each glow probe."""
    navigated = (tap_claims(bot, navigation, max_taps=len(navigation),
                            initial_wait_attempts=2, region=LOWER_CONTENT)
                 if navigation else 0)
    controls = tuple(dict.fromkeys((*claims, *TEXT_CLAIM_CONTROLS)))
    total = ClaimReport()
    empty_rounds = 0
    rounds = 0
    while empty_rounds < QUIET_ROUNDS and rounds < 12:
        rounds += 1
        fixed = claim_fixed_controls(
            bot, controls, max_taps=16,
            initial_wait_attempts=2 if rounds == 1 else 0,
            region=LOWER_CONTENT,
        )
        total = ClaimReport(total.attempted + fixed.attempted,
                            total.verified + fixed.verified)

        # A known launcher may reveal a detail layer. Close a supplied X and
        # continue from the parent instead of ending before glow inspection.
        back_if_close_x(bot)
        sparkle = claim_sparkles(bot, region=LOWER_CONTENT, attempts=1)
        total = ClaimReport(total.attempted + sparkle.attempted,
                            total.verified + sparkle.verified)
        if fixed.claimed or sparkle.claimed:
            empty_rounds = 0
        else:
            empty_rounds += 1
        bot.log("Gift Claims: Valuable Event vòng kiểm tra "
                f"{rounds}, không phản hồi {empty_rounds}/{QUIET_ROUNDS}")

    if empty_rounds >= QUIET_ROUNDS:
        bot.record("Gift Claims: Valuable Event không còn quà xác minh sau "
                   f"{QUIET_ROUNDS} vòng; bỏ qua phần lấp lánh/trả phí và "
                   "coi mục đã xét xong")
    return total, navigated


def run_carousel_claim(bot, screen_name, page: str, tab: str,
                       claims: tuple[str, ...], *,
                       navigation: tuple[str, ...] = ()) -> bool:
    if not open_named(bot, screen_name):
        return False
    if not select_carousel_tab(bot, page, tab):
        return_home(bot)
        return False
    report, _ = process_lower(bot, navigation, claims)
    bot.log(f"Gift Claims: claims {report.verified}/{report.attempted} verified")
    return_home(bot)
    return True
