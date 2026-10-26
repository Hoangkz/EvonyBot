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
CLAIM_GREEN = f"{ROOT}/claimGreen.png"
CLAIM_GRAY = f"{ROOT}/claimGray.png"

TITLE_REGION = (15, 0, 85, 8)
HOW_TO_GET_REGION = (15, 0, 85, 8)
REWARD_REGION = (2, 66, 98, 98)

# Every list gesture stays inside the green rectangle supplied by the user.
SCAN_SWIPE = (50, 94, 50, 73)
RETURN_TOP_SWIPE = (50, 73, 50, 94)
SLOW_SWIPE_DURATION = 1.0
STEP_DELAY = 1.0
MAX_SCROLLS = 12
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

