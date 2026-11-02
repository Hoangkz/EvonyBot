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
# y=486..673.  Keep Claim recognition strictly *inside* it: x=4..96%,
# y=70..95%.  This excludes the green border itself while retaining every
# reward row.
REWARD_REGION = (4, 70, 96, 95)
# The left level-number strip scrolls with the reward list but contains no
# sparkling reward art, lock animation, or Claim glow.  Use only this static
# image band when deciding whether a swipe actually moved the list.
REWARD_STATIC_REGION = (4, 71, 16, 94)
REWARD_STATIC_SAME = 0.85

# Every endpoint stays safely inside the measured green reward frame.  On the
# 21503 device, the former 147 px gesture (y=93 -> 72%) did not move the list;
# the measured 170 px gesture from y=94.5 -> 70.5% does.  Do not start over
# Parade Mask controls or finish on the level/progress strip or green border.
#
# Reward icons swallow vertical gestures.  Drag only on the fixed LV-label
# column, at x=63 on the 396px reference screen (15.9%), which stays inside
# the static level strip and not on an icon or Claim control.  Both endpoint
# confirmations deliberately repeat this same reliable column.
# 15.91% is truncated by InputMixin to exactly x=63 at 396px wide.
LV_COLUMN_SWIPE_X = 15.91
SCAN_SWIPE = (LV_COLUMN_SWIPE_X, 94.5, LV_COLUMN_SWIPE_X, 70.5)
RETURN_TOP_SWIPE = (LV_COLUMN_SWIPE_X, 70.5, LV_COLUMN_SWIPE_X, 94.5)
SCAN_SWIPE_FALLBACKS = ()
RETURN_TOP_SWIPE_FALLBACKS = ()
# The reward list needs a short settle after an ADB swipe before its static LV
# strip is compared.  A live 21503 scan has 19 positions; the old 1.2s swipe
# plus 0.4s wait consumed almost the entire 100s window before the upward
# verification began.  The fast 0.3s gesture needs 0.4s to settle: live 21503
# scores were 0.493 at 0.2s (false movement at the real edge) and 0.9995 at
# 0.4s.  Claim/pop-up timing keeps the normal, safer STEP_DELAY below.
SLOW_SWIPE_DURATION = 0.3
REWARD_SCROLL_DELAY = 0.4
STEP_DELAY = 1.0
# The game may take a moment to open the Mask quantity panel.  Do not decide
# that there is no Use/DONE result from the first immediately-following frame.
PARADE_MASK_OPEN_DELAY = 2.0
EDGE_CONFIRMATIONS = 2
# One clean audit means two complete directional scans: down to the confirmed
# bottom, then immediately up to the confirmed top while still detecting and
# claiming.  Empty rows do not end either scan; the edge detector must observe
# two unchanged swipes at that endpoint.
CLEAN_CLAIM_AUDIT_PASSES = 1
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

