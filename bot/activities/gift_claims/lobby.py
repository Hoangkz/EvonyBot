"""Scan the two lobby notification zones and classify opened inner screens."""
import cv2
import numpy as np

from ...context.errors import YieldToBoss
from .common import REFERENCE_WIDTH, find_all, return_home
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
IGNORED_RIGHT_LAUNCHERS = ("FollowUs/facebook_icon",)


def _red_mask(screen):
    hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
    low_red = cv2.inRange(hsv, np.array((0, 110, 45)),
                          np.array((12, 255, 235)))
    high_red = cv2.inRange(hsv, np.array((170, 110, 45)),
                           np.array((179, 255, 235)))
    return cv2.morphologyEx(low_red | high_red, cv2.MORPH_CLOSE,
                            np.ones((3, 3), np.uint8))


def _bottom_circle_dots(screen, bounds, scale):
    """Use circle geometry to separate badges from red/orange icon artwork."""
    left, top, right, bottom = bounds
    gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 1)
    circles = cv2.HoughCircles(
        gray[top:bottom, left:right], cv2.HOUGH_GRADIENT, dp=1,
        minDist=max(8, round(18 * scale)), param1=80, param2=14,
        minRadius=max(4, round(7 * scale)), maxRadius=max(8, round(16 * scale)))
    if circles is None:
        return []
    hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
    low_y = top + (bottom - top) * 0.20
    high_y = top + (bottom - top) * 0.55
    points = []
    for x, y, _ in circles[0]:
        center = (round(left + x), round(top + y))
        hue, saturation, _ = hsv[center[1], center[0]]
        if (low_y <= center[1] <= high_y
                and saturation >= 220
                and (hue <= 12 or hue >= 170)):
            points.append(center)
    return sorted(points, key=lambda point: point[0])


def _dedupe_right_dots(points, scale):
    """Collapse red artwork fragments belonging to the same right-rail icon."""
    remaining = list(points)
    result = []
    while remaining:
        seed = remaining.pop(0)
        cluster = [seed]
        changed = True
        while changed:
            changed = False
            for point in remaining[:]:
                if any(abs(point[0] - member[0]) <= 35 * scale
                       and abs(point[1] - member[1]) <= 18 * scale
                       for member in cluster):
                    cluster.append(point)
                    remaining.remove(point)
                    changed = True
        # A real notification badge is attached to the icon's upper-right.
        result.append(max(cluster, key=lambda point: (point[0], -point[1])))
    return sorted(result, key=lambda point: (point[1], point[0]))


def red_dots(screen, boundary: str) -> list[tuple[int, int]]:
    """Find round red notification fills inside one user-defined boundary."""
    height, width = screen.shape[:2]
    x0, y0, x1, y1 = REGIONS[boundary]
    left, top = int(width * x0 / 100), int(height * y0 / 100)
    right, bottom = int(width * x1 / 100), int(height * y1 / 100)
    scale = width / REFERENCE_WIDTH
    if boundary == BOTTOM:
        return _bottom_circle_dots(screen, (left, top, right, bottom), scale)
    area = _red_mask(screen)[top:bottom, left:right]
    _, _, stats, _ = cv2.connectedComponentsWithStats(area)
    points = []
    for x, y, box_width, box_height, pixels in stats[1:]:
        if not (6 * scale <= box_width <= 30 * scale
                and 6 * scale <= box_height <= 30 * scale
                and 35 * scale * scale <= pixels <= 500 * scale * scale
                and 0.55 <= box_width / box_height <= 1.8):
            continue
        center = (left + x + box_width // 2, top + y + box_height // 2)
        on_right_rail = center[0] >= width * 0.90 and pixels >= 90 * scale * scale
        if not on_right_rail:
            continue
        points.append(center)
    return _dedupe_right_dots(points, scale)


def _already_attempted(point, attempted, width) -> bool:
    tolerance = 20 * width / REFERENCE_WIDTH
    return any(abs(point[0] - old[0]) <= tolerance
               and abs(point[1] - old[1]) <= tolerance for old in attempted)


def _ignored_right_dots(bot, screen) -> set[tuple[int, int]]:
    """Map Facebook/Follow Us launchers to their attached notification dot."""
    dots = red_dots(screen, RIGHT)
    ignored = set()
    scale = screen.shape[1] / REFERENCE_WIDTH
    for template in IGNORED_RIGHT_LAUNCHERS:
        icons = find_all(bot, template, screen, threshold=0.68,
                         region=REGIONS[RIGHT])
        for icon in icons:
            # One Facebook launcher can yield several red connected components
            # (badge, frame highlight, caption edge). Ignore every component
            # over that icon, but stop before the next launcher below it.
            for dot in dots:
                if (abs(dot[0] - icon[0]) <= 48 * scale
                        and icon[1] - 20 * scale <= dot[1]
                        <= icon[1] + 35 * scale):
                    ignored.add(dot)
    return ignored


def open_next(bot, boundary: str, attempted: list[tuple[int, int]]):
    """Open the next unvisited red-dot icon in one boundary."""
    if not return_home(bot):
        bot.record("Gift Claims: không về được màn chính; chưa được coi là hết vùng")
        raise YieldToBoss
    bot.sleep(0.7)
    screen = bot.screenshot()
    dots = red_dots(screen, boundary)
    ignored = _ignored_right_dots(bot, screen) if boundary == RIGHT else set()
    dot = None
    for point in dots:
        if _already_attempted(point, attempted, screen.shape[1]):
            continue
        if point in ignored:
            attempted.append(point)
            bot.record("Gift Claims: bỏ qua biểu tượng Facebook/Follow Us ở vùng right")
            continue
        dot = point
        break
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
