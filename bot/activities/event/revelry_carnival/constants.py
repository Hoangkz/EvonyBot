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
# Exact supplied marker shown after tapping Parade Mask when no mask remains.
# This—not an empty reward list—is the terminal signal for Revelry Carnival.
PARADE_MASK_DONE = f"{ROOT}/paradeMaskDone.png"
CLAIM_GREEN = f"{ROOT}/claimGreen.png"
CLAIM_GRAY = f"{ROOT}/claimGray.png"

TITLE_REGION = (15, 0, 85, 8)
HOW_TO_GET_REGION = (15, 0, 85, 8)
PARADE_MASK_DONE_REGION = (0, 12, 100, 90)
REWARD_REGION = (2, 67, 98, 98)

# Every endpoint stays strictly inside the user-marked green reward frame:
# x=2..98%, y=67..98% on the 396x704 reference screenshot.  Do not start a
# swipe over the Parade Mask controls or end it on the level/progress strip.
SCAN_SWIPE = (50, 95, 50, 71)
RETURN_TOP_SWIPE = (50, 71, 50, 95)
SLOW_SWIPE_DURATION = 1.0
STEP_DELAY = 1.0
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

