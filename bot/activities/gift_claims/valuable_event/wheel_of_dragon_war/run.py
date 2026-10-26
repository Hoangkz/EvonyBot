"""Claim the free spin in Wheel of Dragon War."""
import cv2
import numpy as np

from ...common import GiftTask
from ...screens import GiftScreen
from ..named_flow import ExactFlow, STEP_DELAY, run_carousel_exact

KEY = "gift_wheel_of_dragon_war"
REFERENCE_WIDTH = 396
SKIP_TAP = (267, 584)
SKIP_BOX = (250, 568, 284, 601)
SKIP_CHECK_ATTEMPTS = 3


def _skip_checked(screen: np.ndarray, box=SKIP_BOX) -> bool:
    """Recognise the green check only inside the Skip-animation `box` (Wheel's by default)."""
    scale = screen.shape[1] / REFERENCE_WIDTH
    x0, y0, x1, y1 = (round(value * scale) for value in box)
    area = screen[max(0, y0):min(screen.shape[0], y1),
                  max(0, x0):min(screen.shape[1], x1)]
    if area.size == 0:
        return False
    hsv = cv2.cvtColor(area, cv2.COLOR_BGR2HSV)
    green = cv2.inRange(hsv, np.array((35, 100, 80)),
                        np.array((95, 255, 255)))
    return int(cv2.countNonZero(green)) >= round(12 * scale * scale)


def ensure_skip_animation(bot, tap=SKIP_TAP, box=SKIP_BOX,
                          label="Wheel of Dragon War") -> bool:
    """Enable Skip animation and require its green checked state. Other
    events pass their own checkbox `tap` point and `box`."""
    for attempt in range(2):
        if _skip_checked(bot.screenshot(), box):
            bot.record(f"Gift Claims: {label} đã bật Skip animation")
            return True
        if attempt == 0:
            bot.sleep(STEP_DELAY)

    screen = bot.screenshot()
    scale = screen.shape[1] / REFERENCE_WIDTH
    bot.record(f"Gift Claims: {label} bật Skip animation")
    bot.tap(round(tap[0] * scale), round(tap[1] * scale),
            delay=STEP_DELAY)
    for attempt in range(SKIP_CHECK_ATTEMPTS):
        if _skip_checked(bot.screenshot(), box):
            return True
        if attempt + 1 < SKIP_CHECK_ATTEMPTS:
            bot.sleep(STEP_DELAY)
    bot.record(f"Gift Claims: {label} không xác minh được Skip animation")
    return False


FLOW = ExactFlow(
    prepare=ensure_skip_animation,
    claims=("ValuableEvent/WheelOfDragonWar/button_spin_once_free",),
    claim_threshold=0.86,
    # DONE only when Spin Once Free is no longer visible.
    absence_done=True,
)


def run(bot):
    return run_carousel_exact(
        bot,
        GiftScreen.VALUABLE_EVENT,
        "ValuableEvent/title",
        "ValuableEvent/WheelOfDragonWar/tab_icon",
        FLOW,
    )


TASK = GiftTask(KEY, "Wheel of Dragon War", run)
