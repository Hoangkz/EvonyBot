"""Scan the two lobby notification zones and classify opened inner screens."""
import cv2
import numpy as np

from ...ocr.find_valuable_event import find_valuable_event as find_valuable_caption
from .common import (REFERENCE_WIDTH, find, find_all, find_super_value_return,
                     return_home, swipe_around)
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
VALUABLE_LAUNCH_ATTEMPTS = 3
# The city launcher rotates through animated event artwork. Emulator 21503
# exposed the valid Empire Depot frame only on capture 10 in a live run, so
# sample a full ten-second window instead of treating four frames as absence.
SUPER_VALUE_LAUNCH_ATTEMPTS = 50
SUPER_VALUE_LAUNCH_INTERVAL = 0.2
PARENT_EDGE_CONFIRMATIONS = 2
PARENT_SAME_DISTANCE = 16
IGNORED_RIGHT_LAUNCHERS = ("FollowUs/facebook_icon",)
EVENT_CENTER_LAUNCHERS = ("EventCenter/launcher_side", "EventCenter/launcher")
FIXED_PARENT_LAUNCHERS = {
    GiftScreen.BACK_TO_TERRITORY: (
        ("EventCenter/BackToTerritory/title",), REGIONS[RIGHT]),
}
PARENT_ANCHOR_TABS = {
    GiftScreen.VALUABLE_EVENT: (
        "ValuableEvent/ResourceConsumptionSprint/tab", "ValuableEvent/LimitedOffer/tab_icon"),
    GiftScreen.SUPER_VALUE_RETURN: ("SuperValueReturn/EmpireDepot/tab_current", "SuperValueReturn/EmpireDepot/tab"),
}


def _parent_carousel_signature(screen) -> bytes:
    """dHash only the stable task-name band of the parent carousel."""
    height, width = screen.shape[:2]
    patch = cv2.cvtColor(
        screen[round(height * 12 / 100):round(height * 18 / 100), :],
        cv2.COLOR_BGR2GRAY,
    )
    tiny = cv2.resize(patch, (49, 10), interpolation=cv2.INTER_AREA)
    return np.packbits(tiny[:, 1:] > tiny[:, :-1]).tobytes()


def _parent_carousel_moved(before, after) -> bool:
    old = np.frombuffer(_parent_carousel_signature(before), dtype=np.uint8)
    new = np.frombuffer(_parent_carousel_signature(after), dtype=np.uint8)
    distance = int(np.unpackbits(np.bitwise_xor(old, new)).sum())
    return old.shape != new.shape or distance > PARENT_SAME_DISTANCE


def _switch_parent_carousel(bot, expected) -> bool:
    """Switch between Valuable Event and Super Value Return by a named tab."""
    current = identify(bot, bot.screenshot())
    if current not in (GiftScreen.VALUABLE_EVENT, GiftScreen.SUPER_VALUE_RETURN):
        return False
    anchors = PARENT_ANCHOR_TABS.get(expected, ())
    # Prove the real first edge, then scan to the real final edge. There is no
    # fixed swipe ceiling; bot.check() remains the shared deadline/Stop guard.
    for phase, start_x, end_x in (("rewind", 20, 85), ("scan", 85, 55)):
        unchanged = 0
        while True:
            bot.check()
            screen = bot.screenshot()
            if identify(bot, screen) == expected:
                return True
            target = next((find(bot, name, screen, threshold=0.70,
                                region=(0, 7, 100, 20))
                           for name in anchors
                           if find(bot, name, screen, threshold=0.70,
                                   region=(0, 7, 100, 20)) is not None), None)
            if target is not None:
                bot.tap(*target, delay=1)
                if identify(bot, bot.screenshot()) == expected:
                    return True
            before = bot.screenshot()
            bot.swipe_percent(start_x, 14, end_x, 14,
                              duration=0.5, delay=1)
            after = bot.screenshot()
            if _parent_carousel_moved(before, after):
                unchanged = 0
                continue
            unchanged += 1
            if unchanged >= PARENT_EDGE_CONFIRMATIONS:
                bot.record("Gift Claims: carousel cha đã xác nhận biên "
                           f"{'đầu' if phase == 'rewind' else 'cuối'} sau "
                           f"{PARENT_EDGE_CONFIRMATIONS} cú không đổi")
                break
    return False


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


def _event_center_dot(bot, screen, dots):
    """Return the right-rail badge attached to Event Center, if visible."""
    scale = screen.shape[1] / REFERENCE_WIDTH
    for template in EVENT_CENTER_LAUNCHERS:
        for icon in find_all(bot, template, screen, threshold=0.68,
                             region=REGIONS[RIGHT]):
            candidates = [dot for dot in dots
                          if abs(dot[0] - icon[0]) <= 55 * scale
                          and icon[1] - 35 * scale <= dot[1]
                          <= icon[1] + 40 * scale]
            if candidates:
                return min(candidates,
                           key=lambda dot: abs(dot[0] - icon[0]) +
                                           abs(dot[1] - icon[1]))
    return None


def open_next(bot, boundary: str, attempted: list[tuple[int, int]]):
    """Open the next unvisited red-dot icon in one boundary."""
    if not return_home(bot):
        bot.record("Gift Claims: không về được màn chính; chưa được coi là hết vùng")
        return None
    bot.sleep(1)
    screen = bot.screenshot()
    dots = red_dots(screen, boundary)
    ignored = _ignored_right_dots(bot, screen) if boundary == RIGHT else set()
    if boundary == RIGHT:
        priority = _event_center_dot(bot, screen, dots)
        if priority is not None:
            dots = [priority] + [point for point in dots if point != priority]
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


def find_valuable_event(bot, screen):
    """Chỗ chữ "Valuable Event" dưới nút ở màn chính (bot/ocr/find_valuable_event: mẫu chữ "Event" rồi OCR), quy về cùng chỗ hàm
    cũ trả: cao hơn tâm chữ "Event" 10 px; nơi gọi bấm cao hơn 20 px nữa = lên icon."""
    pos = find_valuable_caption(screen)
    return None if pos is None else (pos[0], pos[1] - round(10 * screen.shape[1] / REFERENCE_WIDTH))


def open_named(bot, expected):
    """Open a named parent through image recognition, never a fixed position."""
    if not return_home(bot):
        return False
    launcher = None
    launcher_is_tap_target = False
    if expected == GiftScreen.VALUABLE_EVENT:
        # The launcher moves with the city and its glow/badge is animated.
        # Check fresh frames and re-centre the city between misses instead of
        # turning one unlucky screenshot into another 120-second retry.
        for attempt in range(VALUABLE_LAUNCH_ATTEMPTS):
            screen = bot.screenshot()
            if identify(bot, screen) == expected:
                return True
            launcher = find_valuable_event(bot, screen)
            if launcher is not None:
                break
            if attempt + 1 < VALUABLE_LAUNCH_ATTEMPTS:
                bot.log(
                    "Gift Claims: chưa thấy launcher ValuableEvent; "
                    f"điều chỉnh màn thành ({attempt + 1}/"
                    f"{VALUABLE_LAUNCH_ATTEMPTS - 1})")
                swipe_around(bot)
        if launcher is None:
            # Approved city-layout fallback for the 396x704 reference screen.
            # Verify the inner title after tapping; a coordinate tap alone is
            # never accepted as proof that the correct page opened.
            scale = screen.shape[1] / REFERENCE_WIDTH
            fixed_target = (round(255 * scale), round(566 * scale))
            bot.record(
                "Gift Claims: không thấy launcher ValuableEvent; "
                "bấm fallback x=255 y=566")
            bot.tap(*fixed_target, delay=1)
            for attempt in range(OPEN_WAIT_ATTEMPTS):
                if identify(bot, bot.screenshot()) == expected:
                    return True
                if attempt + 1 < OPEN_WAIT_ATTEMPTS:
                    bot.sleep(1)
            bot.record(
                "Gift Claims: fallback x=255 y=566 không mở được "
                "ValuableEvent")

            # Some city layouts expose only the Super Value Return launcher,
            # although Valuable Event is still another tab in the same upper
            # carousel.  Use the launcher that is actually visible, then move
            # to a known Valuable Event tab instead of waiting 120 seconds for
            # a city launcher which may never be present.
            bot.record(
                "Gift Claims: không thấy launcher ValuableEvent; "
                "thử mở qua SuperValueReturn")
            if open_named(bot, GiftScreen.SUPER_VALUE_RETURN):
                if _switch_parent_carousel(bot, expected):
                    bot.record(
                        "Gift Claims: đã chuyển SuperValueReturn -> ValuableEvent")
                    return True
                bot.record(
                    "Gift Claims: đã mở SuperValueReturn nhưng không chuyển "
                    "được sang ValuableEvent")
            else:
                bot.record(
                    "Gift Claims: không mở được SuperValueReturn để đi vòng "
                    "sang ValuableEvent")
            return_home(bot)
    elif expected == GiftScreen.SUPER_VALUE_RETURN:
        # Animation changes the launcher artwork every few frames. Sample
        # several fresh screenshots and use the dedicated multi-template
        # detector. Never replace a miss with a hard-coded tap.
        for attempt in range(SUPER_VALUE_LAUNCH_ATTEMPTS):
            screen = bot.screenshot()
            if identify(bot, screen) == expected:
                return True
            launcher = find_super_value_return(bot, screen)
            if launcher is not None:
                launcher_is_tap_target = True
                break
            if attempt + 1 < SUPER_VALUE_LAUNCH_ATTEMPTS:
                bot.log("Gift Claims: chưa thấy launcher SuperValueReturn; "
                        f"chụp lại frame animation ({attempt + 1}/"
                        f"{SUPER_VALUE_LAUNCH_ATTEMPTS - 1})")
                bot.sleep(SUPER_VALUE_LAUNCH_INTERVAL)
        if launcher is None:
            bot.record("Gift Claims: không nhận diện được launcher "
                       f"SuperValueReturn sau {SUPER_VALUE_LAUNCH_ATTEMPTS} "
                       "frame; không mở ValuableEvent và không bấm tọa độ cứng")
            return False
    else:
        screen = bot.screenshot()
        if identify(bot, screen) == expected:
            return True
        launcher_spec = FIXED_PARENT_LAUNCHERS.get(expected)
        if launcher_spec is not None:
            templates, region = launcher_spec
            for template in templates:
                launcher = find(bot, template, screen, threshold=0.66,
                                region=region)
                if launcher is not None:
                    break
    if launcher is None:
        bot.log(f"Gift Claims: không tìm thấy launcher {expected.value} bằng ảnh/tên")
        return False
    bot.record(f"Gift Claims: mở {expected.value} bằng ảnh launcher")
    if launcher_is_tap_target:
        bot.tap(*launcher, delay=1)
    else:
        # Generic templates contain the caption; the icon body above is the
        # click target and follows the carousel if its slot moves.
        bot.tap(launcher[0], max(0, launcher[1] - 20), delay=1)
    for attempt in range(OPEN_WAIT_ATTEMPTS):
        screen = bot.screenshot()
        if identify(bot, screen) == expected:
            return True
        if attempt + 1 < OPEN_WAIT_ATTEMPTS:
            bot.sleep(1)
    if (expected != GiftScreen.SUPER_VALUE_RETURN
            and _switch_parent_carousel(bot, expected)):
        return True
    bot.log(f"Gift Claims: launcher ảnh không mở {expected.value}")
    return_home(bot)
    return False
