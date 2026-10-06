"""Scan the two lobby notification zones and classify opened inner screens."""
import cv2
import numpy as np

from .common import REFERENCE_WIDTH, return_home
from .screens import GiftScreen, identify

BOTTOM = "bottom"
RIGHT = "right"
BOUNDARIES = (BOTTOM, RIGHT)
REGIONS = {
    BOTTOM: (0, 70, 85, 91),
    # The right rail may grow downwards as rotating icons are added.
    RIGHT: (58, 4, 100, 75),
}
MAX_OPENS_PER_BOUNDARY = 16
OPEN_WAIT_ATTEMPTS = 6


def _red_mask(screen):
    hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
    low_red = cv2.inRange(hsv, np.array((0, 110, 45)),
                          np.array((12, 255, 235)))
    high_red = cv2.inRange(hsv, np.array((170, 110, 45)),
                           np.array((179, 255, 235)))
    return cv2.morphologyEx(low_red | high_red, cv2.MORPH_CLOSE,
                            np.ones((3, 3), np.uint8))


def red_dots(screen, boundary: str) -> list[tuple[int, int]]:
    """Find round red notification fills inside one user-defined boundary."""
    height, width = screen.shape[:2]
    x0, y0, x1, y1 = REGIONS[boundary]
    left, top = int(width * x0 / 100), int(height * y0 / 100)
    right, bottom = int(width * x1 / 100), int(height * y1 / 100)
    area = _red_mask(screen)[top:bottom, left:right]
    _, _, stats, _ = cv2.connectedComponentsWithStats(area)
    scale = width / REFERENCE_WIDTH
    points = []
    for x, y, box_width, box_height, pixels in stats[1:]:
        if not (6 * scale <= box_width <= 30 * scale
                and 6 * scale <= box_height <= 30 * scale
                and 35 * scale * scale <= pixels <= 500 * scale * scale
                and 0.55 <= box_width / box_height <= 1.8):
            continue
        center = (left + x + box_width // 2, top + y + box_height // 2)
        if boundary == BOTTOM:
            # Dots sit at the upper-right of each bottom icon. This excludes
            # red letters/artwork lower in the same strip.
            if center[1] > top + (bottom - top) * 0.48 or pixels < 80 * scale * scale:
                continue
        else:
            on_right_rail = center[0] >= width * 0.90 and pixels >= 90 * scale * scale
            on_top_row = (center[0] >= width * 0.72
                          and center[1] <= height * 0.15
                          and pixels >= 90 * scale * scale)
            if not (on_right_rail or on_top_row):
                continue
        points.append(center)
    return sorted(points, key=lambda point: (point[1], point[0]))


def _already_attempted(point, attempted, width) -> bool:
    tolerance = 20 * width / REFERENCE_WIDTH
    return any(abs(point[0] - old[0]) <= tolerance
               and abs(point[1] - old[1]) <= tolerance for old in attempted)


def open_next(bot, boundary: str, attempted: list[tuple[int, int]]):
    """Open the next unvisited red-dot icon in one boundary."""
    if not return_home(bot):
        return None
    bot.sleep(0.7)
    screen = bot.screenshot()
    dots = red_dots(screen, boundary)
    dot = next((point for point in dots
                if not _already_attempted(point, attempted, screen.shape[1])), None)
    if dot is None:
        bot.log(f"Gift Claims: vùng {boundary} đã hết chấm đỏ chưa xét")
        return None
    attempted.append(dot)

    scale = screen.shape[1] / REFERENCE_WIDTH
    # A notification is attached to the icon's upper-right corner.
    target = (max(0, round(dot[0] - 25 * scale)),
              min(screen.shape[0] - 1, round(dot[1] + 16 * scale)))
    bot.tap(*target, delay=1)

    name = None
    for attempt in range(OPEN_WAIT_ATTEMPTS):
        opened = bot.screenshot()
        name = identify(bot, opened)
        if name is not None:
            break
        if attempt + 1 < OPEN_WAIT_ATTEMPTS:
            bot.sleep(1)
    name = name or GiftScreen.UNKNOWN
    bot.log(f"Gift Claims: vùng {boundary}, chấm đỏ {dot} mở {name.value}")
    return name


def open_named(bot, expected):
    """Search both boundaries until a red-dot icon opens the expected title."""
    for boundary in BOUNDARIES:
        attempted = []
        for _ in range(MAX_OPENS_PER_BOUNDARY):
            name = open_next(bot, boundary, attempted)
            if name is None:
                break
            if name == expected:
                return True
            return_home(bot)
    return False
