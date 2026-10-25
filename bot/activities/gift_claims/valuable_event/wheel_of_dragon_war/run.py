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


def _skip_checked(screen: np.ndarray) -> bool:
    """Recognise the green check only inside Wheel's Skip-animation box."""
    scale = screen.shape[1] / REFERENCE_WIDTH
    x0, y0, x1, y1 = (round(value * scale) for value in SKIP_BOX)
    area = screen[max(0, y0):min(screen.shape[0], y1),
                  max(0, x0):min(screen.shape[1], x1)]
    if area.size == 0:
        return False
    hsv = cv2.cvtColor(area, cv2.COLOR_BGR2HSV)
    green = cv2.inRange(hsv, np.array((35, 100, 80)),
                        np.array((95, 255, 255)))
    return int(cv2.countNonZero(green)) >= round(12 * scale * scale)


def ensure_skip_animation(bot) -> bool:
    """Enable Skip animation and require its green checked state."""
    for attempt in range(2):
        if _skip_checked(bot.screenshot()):
            bot.record("Gift Claims: Wheel of Dragon War đã bật Skip animation")
            return True
        if attempt == 0:
            bot.sleep(STEP_DELAY)

    screen = bot.screenshot()
    scale = screen.shape[1] / REFERENCE_WIDTH
    bot.record("Gift Claims: Wheel of Dragon War bật Skip animation")
    bot.tap(round(SKIP_TAP[0] * scale), round(SKIP_TAP[1] * scale),
            delay=STEP_DELAY)
    for attempt in range(SKIP_CHECK_ATTEMPTS):
        if _skip_checked(bot.screenshot()):
            return True
        if attempt + 1 < SKIP_CHECK_ATTEMPTS:
            bot.sleep(STEP_DELAY)
    bot.record("Gift Claims: Wheel of Dragon War không xác minh được Skip animation")
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
