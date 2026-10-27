"""Images and measured controls for Revelry Carnival."""

KEY = "revelry_carnival"
USE_DONE_KEY = "revelry_carnival_parade_masks_used"
NAME = "Revelry Carnival"
ROOT = "GiftClaims/Event/RevelryCarnival"

ICON = f"{ROOT}/icon.png"
TITLE = f"{ROOT}/title.png"
PARADE_MASK = f"{ROOT}/paradeMask.png"
PLUS = f"{ROOT}/plus.png"
MAX_BUTTON = f"{ROOT}/max.png"
MAX_SELECTED = f"{ROOT}/maxSelected.png"
USE_BUTTON = f"{ROOT}/use.png"
CONGRATULATIONS = f"{ROOT}/congratulations.png"
HOW_TO_GET = f"{ROOT}/howToGet.png"
# Exact ``You can get items from:`` text shown after the *post-claim* Parade
# Mask tap when no mask remains.  This—not an empty reward list—is the
# terminal signal for Revelry Carnival.
PARADE_MASK_DONE = f"{ROOT}/paradeMaskDone.png"
# Alternative empty-Mask marker supplied as Screenshot_20261027-203351.  It
# is accepted only after this flow itself has tapped Parade Mask.
PARADE_MASK_EMPTY_MARKER = f"{ROOT}/paradeMaskEmptyMarker.png"
CLAIM_GREEN = f"{ROOT}/claimGreen.png"
CLAIM_GRAY = f"{ROOT}/claimGray.png"

TITLE_REGION = (15, 0, 85, 8)
HOW_TO_GET_REGION = (15, 0, 85, 8)
PARADE_MASK_DONE_REGION = (0, 12, 100, 90)
# The supplied 396x705 screenshot has a green outer border at x=13..382 and
# y=486..673.  Keep recognition strictly *inside* it: x=4..96%, y=70..95%.
# This excludes the green border itself while retaining every reward row.
REWARD_REGION = (4, 70, 96, 95)

# Every endpoint stays safely inside the measured green reward frame.  On the
# 21503 device, the former 147 px gesture (y=93 -> 72%) did not move the list;
# the measured 170 px gesture from y=94.5 -> 70.5% does.  Do not start over
# Parade Mask controls or finish on the level/progress strip or green border.
#
# On 21513 at LV7/8, the centre path could be swallowed by a reward row and
# produce two identical frames even though levels remained below.  The user
# selected x=45 px (11.36%) for the left fallback: y=665 -> 496 px remains
# exactly inside the green frame.  The right and slightly-raised centre paths
# are retained as later probes.  They are fallback probes, not extra broad
# gestures: every endpoint remains within this green frame.
SCAN_SWIPE = (50, 94.5, 50, 70.5)
RETURN_TOP_SWIPE = (50, 70.5, 50, 94.5)
SCAN_SWIPE_FALLBACKS = (
    (11.36, 94.5, 11.36, 70.5),  # (45, 665) -> (45, 496) at 396x704
    (80, 94.5, 80, 70.5),
    (50, 93.5, 50, 70.5),
)
RETURN_TOP_SWIPE_FALLBACKS = (
    (11.36, 70.5, 11.36, 94.5),  # (45, 496) -> (45, 665) at 396x704
    (80, 70.5, 80, 94.5),
    (50, 70.5, 50, 93.5),
)
SLOW_SWIPE_DURATION = 1.2
STEP_DELAY = 1.0
# The game may take a moment to open the Mask quantity panel.  Do not decide
# that there is no Use/DONE result from the first immediately-following frame.
PARADE_MASK_OPEN_DELAY = 2.0
EDGE_CONFIRMATIONS = 2
MAX_FULL_PASSES = 3
MAX_CLAIMS_PER_VIEW = 6

TITLE_THRESHOLD = 0.82
CONTROL_THRESHOLD = 0.82
CLAIM_THRESHOLD = 0.76
GREEN_HUE = (35, 90)
GREEN_MIN_SATURATION = 70
GREEN_MIN_VALUE = 45
GREEN_MIN_RATIO = 0.25

WAIT_TIMEOUT = 8
MAX_SELECT_TRIES = 3
MAX_CROP_LEFT = 50
MAX_CROP_HALF_HEIGHT = 18
MAX_BAR_WIDTH = 240
MAX_BAR_STILL_DIFF = 3.0
LIST_HASH_DISTANCE = 24

