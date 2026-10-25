"""Shared navigation and safe claim helpers for the post-daily gift flows.

The screenshots supplied for these rotating events use a 396 px reference width.
Templates are scaled to the current emulator width before matching so the existing
396x704 test/device layout is supported as well.
"""
from dataclasses import dataclass
from typing import Callable

import cv2
import numpy as np

from ...common import go_home
from ..event.common import find_event_center as find_project_event_center, swipe_around
from ..event_center.constants import EVENT_CENTER_TAP_OFFSET

ROOT = "GiftClaims"
REFERENCE_WIDTH = 396
MAIN_MARKER = "Server/listActivity.png"
MAX_HOME_STEPS = 7
MAX_TAB_SWIPES = 7
EVENT_CENTER_WAIT_ATTEMPTS = 6
FIXED_CONTROL_THRESHOLDS = {
    "Common/button_daily_free_text": 0.62,
    "Common/button_claim_text": 0.65,
    "Common/button_free_text": 0.70,
    "Common/button_claim_all_text": 0.70,
}

TEXT_CLAIM_CONTROLS = (
    "Common/button_claim_text",
    "Common/button_claim_all_text",
    "Common/button_claimable",
    "Common/button_claimable_alt",
    "Common/button_daily_free_text",
    "Common/button_free_text",
)

@dataclass(frozen=True)
class GiftTask:
    key: str
    label: str
    run: Callable

    def __post_init__(self):
        """Make a standalone event task persist its own successful result."""
        action = self.run

        def persisted(bot, *args, **kwargs):
            if bot.is_daily_done(self.key):
                return True
            completed = action(bot, *args, **kwargs)
            if completed:
                mark_task_done(bot, self.key)
            return completed

        object.__setattr__(self, "run", persisted)


@dataclass(frozen=True)
class ClaimReport:
    """Result of safe reward controls, separating taps from real claims."""
    attempted: int = 0
    verified: int = 0

    @property
    def acted(self) -> bool:
        return self.attempted > 0

    @property
    def claimed(self) -> bool:
        return self.verified > 0


def mark_task_done(bot, key: str) -> None:
    """Persist one completed gift event without completing the combined task."""
    if not bot.is_daily_done(key):
        bot.mark_daily_done(key)
        bot.record(f"Gift Claims: DB DONE {key}")


SKIPPED_ATTR = "_gift_claims_skipped_for_run"


def skip_for_run(bot, key: str) -> None:
    """Bỏ hoạt động `key` trong lần chạy này: ghi trên context (tạo mới mỗi lần Start), không ghi DB."""
    skipped = getattr(bot, SKIPPED_ATTR, None)
    if not isinstance(skipped, set):
        skipped = set()
        setattr(bot, SKIPPED_ATTR, skipped)
    skipped.add(key)


def skipped_for_run(bot, key: str) -> bool:
    skipped = getattr(bot, SKIPPED_ATTR, None)
    return isinstance(skipped, set) and key in skipped


def path(name: str) -> str:
    return f"{ROOT}/{name}.png"


def _scaled_template(bot, name: str, screen: np.ndarray) -> np.ndarray:
    template = bot._template(path(name))
    scale = screen.shape[1] / REFERENCE_WIDTH
    if abs(scale - 1.0) < 0.005:
        return template
    width = max(1, round(template.shape[1] * scale))
    height = max(1, round(template.shape[0] * scale))
    interpolation = cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC
    return cv2.resize(template, (width, height), interpolation=interpolation)


def find(bot, name: str, screen=None, threshold: float = 0.82, region=None):
    screen = bot.screenshot() if screen is None else screen
    return bot.find(_scaled_template(bot, name, screen), threshold=threshold,
                    screen=screen, region=region)


def find_all(bot, name: str, screen=None, threshold: float = 0.82,
             region=(0, 0, 100, 100)) -> list[tuple[int, int]]:
    """Return non-overlapping matches for a small, exact UI marker."""
    screen = bot.screenshot() if screen is None else screen
    template = _scaled_template(bot, name, screen)
    height, width = screen.shape[:2]
    x0, y0, x1, y1 = region
    left, top = int(width * x0 / 100), int(height * y0 / 100)
    area = screen[top:int(height * y1 / 100), left:int(width * x1 / 100)]
    if area.shape[0] < template.shape[0] or area.shape[1] < template.shape[1]:
        return []
    scores = cv2.matchTemplate(area, template, cv2.TM_CCOEFF_NORMED)
    matches = []
    template_height, template_width = template.shape[:2]
    while True:
        _, score, _, location = cv2.minMaxLoc(scores)
        if score < threshold:
            break
        x, y = location
        matches.append((left + x + template_width // 2,
                        top + y + template_height // 2))
        cv2.rectangle(scores,
                      (max(0, x - template_width), max(0, y - template_height)),
                      (min(scores.shape[1] - 1, x + template_width),
                       min(scores.shape[0] - 1, y + template_height)),
                      -1.0, thickness=-1)
    return sorted(matches, key=lambda point: (point[1], point[0]))


def on_main(bot, screen=None) -> bool:
    screen = bot.screenshot() if screen is None else screen
    return bot.find(MAIN_MARKER, threshold=0.7, screen=screen) is not None


def return_home(bot) -> bool:
    """Back out until the city/world screen is visible."""
    for _ in range(MAX_HOME_STEPS):
        screen = bot.screenshot()
        if bot.find("exit/1escEvony.png", threshold=0.82, screen=screen,
                    region=(45, 50, 85, 70)) is not None:
            bot.tap_percent(34, 59, delay=0.7)  # Cancel
            continue
        if on_main(bot, screen):
            return True
        go_home(bot, screen)
        bot.sleep(1)
    bot.log("Gift Claims: could not return to the main screen")
    return False


def open_launcher(bot, launcher: str | tuple[str, ...]):
    """Open a red-dot launcher from the main screen; return its first screen."""
    if not return_home(bot):
        return None
    screen = bot.screenshot()
    launchers = (launcher,) if isinstance(launcher, str) else launcher
    match = next(((name, pos) for name in launchers
                  if (pos := find(bot, name, screen, threshold=0.70)) is not None), None)
    pos = None if match is None else match[1]
    if pos is None:
        bot.log(f"Gift Claims: {' / '.join(launchers)} has no claim indicator")
        return None
    bot.tap(pos[0], max(0, pos[1] - round(20 * screen.shape[1] / REFERENCE_WIDTH)), delay=1)
    return bot.screenshot()


def open_event_center(bot):
    """Open Event Center through the project's authoritative image finder."""
    for launch_attempt in range(3):
        if not return_home(bot):
            return None
        lobby = bot.screenshot()
        launcher = find_project_event_center(bot, lobby)
        if launcher is None:
            bot.log("Gift Claims: project find_event_center chưa thấy Event Center; kéo để tìm lại")
            if launch_attempt < 2:
                swipe_around(bot)
            continue
        dx, dy = EVENT_CENTER_TAP_OFFSET
        bot.tap(launcher[0] + dx, launcher[1] + dy, delay=1)
        for attempt in range(EVENT_CENTER_WAIT_ATTEMPTS):
            screen = bot.screenshot()
            if find(bot, "EventCenter/title", screen, threshold=0.72,
                    region=(0, 0, 100, 13)) is not None:
                return screen
            if back_if_close_x(bot, screen):
                bot.record("Gift Claims: popup che Event Center; đóng và thử launcher lại")
                break
            if attempt + 1 < EVENT_CENTER_WAIT_ATTEMPTS:
                bot.sleep(1)
    bot.log("Gift Claims: Event Center did not open")
    return_home(bot)
    return None


def select_carousel_tab(bot, page_title: str, tab: str, screen=None) -> bool:
    """Select a tab after its fixed parent screen has already been identified."""
    screen = bot.screenshot() if screen is None else screen
    if find(bot, page_title, screen, threshold=0.72, region=(0, 0, 100, 13)) is None:
        bot.log(f"Gift Claims: current screen is not {page_title}")
        return False

    for direction in (-1, 1):
        for _ in range(MAX_TAB_SWIPES + 1):
            screen = bot.screenshot()
            pos = find(bot, tab, screen, threshold=0.74, region=(0, 7, 100, 20))
            if pos is not None:
                bot.tap(*pos, delay=1)
                return True
            if direction < 0:
                bot.swipe_percent(85, 14, 20, 14, duration=0.5, delay=1)
            else:
                bot.swipe_percent(20, 14, 85, 14, duration=0.5, delay=1)
    bot.log(f"Gift Claims: tab {tab} not found or has no red dot")
    return False


def open_event_center_event(bot, row: str, page_title: str) -> bool:
    """Open one visible named Event Center row, independent of red badges."""
    screen = open_event_center(bot)
    if screen is None:
        return False
    row_pos = find(bot, row, screen, threshold=0.80, region=(15, 15, 70, 98))
    if row_pos is None:
        bot.log(f"Gift Claims: không thấy hàng cố định {row}")
        return_home(bot)
        return False
    bot.tap_percent(52, row_pos[1] * 100 / screen.shape[0], delay=1)
    opened = bot.screenshot()
    if find(bot, page_title, opened, threshold=0.72, region=(0, 0, 100, 13)) is not None:
        return True
    return_home(bot)
    return False


def tap_claims(bot, templates: tuple[str, ...], *, max_taps: int = 6,
               initial_wait_attempts: int = 5, region=None) -> int:
    """Tap each known free/claim control at most once per screen flow.

    Some event pages leave a claim-looking control visible after it is tapped.
    Remembering the template prevents an unchanged page from being tapped in a
    loop while still allowing a flow with several distinct safe controls.
    """
    count = 0
    waits = 0
    attempted = set()
    attempted_positions = []
    while count < max_taps:
        screen = bot.screenshot()
        hit = None
        for name in templates:
            if name in attempted:
                continue
            pos = find(bot, name, screen, threshold=0.76, region=region)
            if pos is not None:
                # Several modules keep a full-button fallback plus a stable
                # text-only template (for example Claimable). Treat aliases
                # that resolve to the same control as one tap.
                tolerance = 42 * screen.shape[1] / REFERENCE_WIDTH
                if any((pos[0] - old[0]) ** 2 + (pos[1] - old[1]) ** 2
                       <= tolerance ** 2 for old in attempted_positions):
                    attempted.add(name)
                    continue
                hit = name, pos
                break
        if hit is None:
            # The selected tab can appear several seconds before its content.
            # Do not treat an unloaded page as "no free reward" immediately.
            if count == 0 and waits < initial_wait_attempts:
                waits += 1
                bot.sleep(1)
                continue
            break
        name, pos = hit
        attempted.add(name)
        attempted_positions.append(pos)
        bot.record(f"Gift Claims: tap {name}")
        bot.tap(*pos, delay=1)
        count += 1
        after = bot.screenshot()
        change = float(cv2.absdiff(screen, after).mean())
        if change < 0.5:
            bot.log(f"Gift Claims: screen unchanged after {name}; will not tap it again")
    return count


def close_congratulations(bot, *, attempts: int = 3) -> bool:
    """Close the common reward popup and report a verified claim."""
    for attempt in range(attempts):
        screen = bot.screenshot()
        if find(bot, "SuperValueReturn/LoginGifts/congratulations", screen, threshold=0.78,
                region=(0, 38, 100, 62)) is not None:
            bot.back(delay=0.8)
            return True
        if attempt + 1 < attempts:
            bot.sleep(0.4)
    return False


def claim_fixed_controls(bot, templates: tuple[str, ...], *, max_taps: int = 6,
                         initial_wait_attempts: int = 2, region=None) -> ClaimReport:
    """Tap only fixed reward controls and verify every successful claim.

    A tap is verified by Congratulations or by that control disappearing near
    the tapped point. Multiple identical buttons are handled one-by-one. A
    stubborn/non-reward control is skipped locally so another real reward on
    the same page can still be claimed.
    """
    blocked_positions: list[tuple[int, int]] = []
    attempted_count = verified_count = waits = 0
    while attempted_count < max_taps:
        bot.check()
        before = bot.screenshot()
        hit = None
        for name in templates:
            threshold = FIXED_CONTROL_THRESHOLDS.get(name, 0.76)
            tolerance = 30 * before.shape[1] / REFERENCE_WIDTH
            positions = find_all(bot, name, before, threshold=threshold,
                                 region=region or (0, 0, 100, 100))
            for pos in positions:
                if any((pos[0] - old[0]) ** 2 + (pos[1] - old[1]) ** 2
                       <= tolerance ** 2 for old in blocked_positions):
                    continue
                hit = name, pos, len(positions)
                break
            if hit is not None:
                break
        if hit is None:
            if attempted_count == 0 and waits < initial_wait_attempts:
                waits += 1
                bot.sleep(1)
                continue
            break

        name, pos, before_count = hit
        attempted_count += 1
        bot.record(f"Gift Claims: tap fixed claim {name}")
        bot.tap(*pos, delay=1)

        if close_congratulations(bot):
            verified_count += 1
            bot.record(f"Gift Claims: verified Congratulations after {name}")
            continue

        after = bot.screenshot()
        threshold = FIXED_CONTROL_THRESHOLDS.get(name, 0.76)
        tolerance = 30 * after.shape[1] / REFERENCE_WIDTH
        remaining = find_all(bot, name, after, threshold=threshold,
                             region=region or (0, 0, 100, 100))
        if (len(remaining) < before_count or
                not any((candidate[0] - pos[0]) ** 2 +
                        (candidate[1] - pos[1]) ** 2 <= tolerance ** 2
                        for candidate in remaining)):
            verified_count += 1
            bot.record(f"Gift Claims: verified control disappeared after {name}")
            continue

        blocked_positions.append(pos)
        bot.log(f"Gift Claims: {name} vẫn còn và không có Congratulations; "
                "bỏ qua đúng vị trí này và tìm nút khác")
    return ClaimReport(attempted_count, verified_count)


def sparkle_point(before: np.ndarray, after: np.ndarray,
                   region=(0, 20, 100, 88)) -> tuple[int, int] | None:
    """Locate one small, bright animated sparkle in the lower content area.

    Large animated backgrounds (fire, treasure piles, characters) are rejected;
    only compact high-difference highlights are eligible. The bottom purchase
    strip and the top carousel are outside the default region.
    """
    height, width = before.shape[:2]
    x0, y0, x1, y1 = region
    left, top = int(width * x0 / 100), int(height * y0 / 100)
    right, bottom = int(width * x1 / 100), int(height * y1 / 100)
    old = before[top:bottom, left:right]
    new = after[top:bottom, left:right]
    if old.size == 0 or old.shape != new.shape:
        return None
    delta = cv2.cvtColor(cv2.absdiff(old, new), cv2.COLOR_BGR2GRAY)
    value = cv2.cvtColor(new, cv2.COLOR_BGR2HSV)[:, :, 2]
    mask = ((delta >= 32) & (value >= 190)).astype(np.uint8) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    count, _, stats, centers = cv2.connectedComponentsWithStats(mask)
    scale = width / REFERENCE_WIDTH
    best = None
    for index in range(1, count):
        x, y, box_width, box_height, pixels = stats[index]
        if not (2 * scale * scale <= pixels <= 150 * scale * scale
                and box_width <= 24 * scale and box_height <= 24 * scale):
            continue
        component = delta[y:y + box_height, x:x + box_width]
        score = float(component.mean()) * pixels
        if best is None or score > best[0]:
            cx, cy = centers[index]
            best = score, (round(left + cx), round(top + cy))
    return None if best is None else best[1]


def tap_sparkle(bot, *, region=(0, 20, 100, 88)) -> bool:
    """Sample animation twice and tap one safe compact sparkle if present."""
    before = bot.screenshot()
    bot.sleep(0.4)
    after = bot.screenshot()
    point = sparkle_point(before, after, region)
    if point is None:
        return False
    bot.record(f"Gift Claims: không thấy nút cố định, tap sparkle {point}")
    bot.tap(*point, delay=1)
    return True


def claim_sparkle(bot, *, region=(0, 20, 100, 88)) -> ClaimReport:
    """Tap one safe sparkle and count it only when reward popup is verified."""
    if not tap_sparkle(bot, region=region):
        return ClaimReport()
    verified = int(close_congratulations(bot))
    if not verified:
        bot.log("Gift Claims: sparkle không sinh Congratulations; không tính là đã nhận")
    return ClaimReport(1, verified)


def claim_sparkles(bot, *, region=(0, 20, 100, 88), attempts=4) -> ClaimReport:
    """Check an intermittent glow several times, then stop the child safely.

    Animated reward highlights are not visible in every frame.  Four bounded
    samples make them much harder to miss while ensuring a decorative glow can
    never keep the task in an infinite loop.
    """
    attempted = verified = 0
    for index in range(attempts):
        bot.check()
        report = claim_sparkle(bot, region=region)
        attempted += report.attempted
        verified += report.verified
        if report.claimed:
            bot.record(f"Gift Claims: sparkle lần {index + 1}/{attempts} đã nhận quà")
        else:
            bot.log(f"Gift Claims: sparkle lần {index + 1}/{attempts} không có quà xác minh")
    bot.record(f"Gift Claims: đã kiểm tra sparkle đủ {attempts} lần; kết thúc mục hiện tại")
    return ClaimReport(attempted, verified)


def back_if_close_x(bot, screen=None) -> bool:
    """Use Android Back when an opened reward panel exposes the supplied X."""
    screen = bot.screenshot() if screen is None else screen
    close = find(bot, "Common/button_close_x", screen, threshold=0.78,
                 region=(0, 0, 100, 35)) is not None
    if not close:
        # Some rotating sales use a bright red diagonal X instead of the
        # round gold X supplied by the user.  Restrict this fallback to the
        # extreme top-right corner so red event artwork is never actionable.
        height, width = screen.shape[:2]
        corner = screen[:max(1, round(height * 0.06)),
                        max(0, round(width * 0.90)):]
        hsv = cv2.cvtColor(corner, cv2.COLOR_BGR2HSV)
        bright_red = ((cv2.inRange(hsv, np.array((0, 170, 145)),
                                   np.array((12, 255, 255))) |
                       cv2.inRange(hsv, np.array((170, 170, 145)),
                                   np.array((179, 255, 255)))))
        close = cv2.countNonZero(bright_red) >= max(20, round(width * height * 0.00025))
    if not close:
        return False
    bot.record("Gift Claims: thấy nút X; dùng Back để thoát mục")
    bot.back(delay=0.8)
    return True


