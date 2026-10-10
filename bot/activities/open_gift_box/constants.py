"""
constants.py — Open Gift Box image folders, limits and action names.
"""
SETUP = "OpenBox/Setup"

ITEMS = "Items"             # Items screen images: menu buttons, box icons
DONE = f"{ITEMS}/done"      # "nothing left to open" markers at the end of the list
# Hero-fragment items close the list. Their "done" images (a quill feather on the icon, one file per
# background colour: the same quill is on other items too) only count when the fragment's blue puzzle piece is next to them.
FRAGMENT_PREFIX = "fragment_"       # file names in the done folder
FRAGMENT = f"{ITEMS}/FragmentPuzzle.png"
FRAGMENT_NEAR = 8.5         # max distance feather -> puzzle piece, % of screen height
# After tapping a box: wait 1s for its Open / Use button, then up to this many more 1s waits.
BUTTON_EXTRA_WAITS = 5
KEY = "open_gift_box"       # daily_done key: every box opened today

# Checkbox label -> folder of box icons.
BOX_FOLDERS = {
    "Resource": f"{ITEMS}/resource",
    "Gold": f"{ITEMS}/gold",
    "Gems": f"{ITEMS}/gem",
    "Etc": f"{ITEMS}/etc",
}
ALL_BOXES = "All"

# One match threshold for every image of this activity (find_first's default is 0.9).
BOX_THRESHOLD = 0.8
# Tab bar of the Items list (% of screen): the Common tab image is only looked for here.
_TAB_BAR = (0, 8, 35, 32)
TAB_REGIONS = {f"{ITEMS}/CommonTab.png": _TAB_BAR, f"{ITEMS}/CommonIcon.png": _TAB_BAR}
# The list is a grid of 4 columns; icons whose centres differ by less than this (in y)  share a row.
ROW_TOLERANCE = 4.3        # % of screen height
# Boxes are only looked for below the Common tab (its position moves, e.g. with the promotion
# banner, so it is found on every scan) and above BOX_BOTTOM (% of screen height). Tapping one
# there opens the info panel under it without scrolling the list, so no unopened box is pushed
# out of view.
TAB_HALF_HEIGHT = 3.5     # % of screen height from the Common tab's centre to its bottom edge
BOX_BOTTOM = 70
# Scroll of about two rows, so the next scan overlaps the last one by a row.
LIST_SWIPE = (50, 62, 50, 36)

# What to do when each image is seen.
CONFIRM = "confirm"
BOX_LIST = "box_list"       # gift box list open -> tap the next wanted box
TAP = "tap"                 # item, Open or Use button: just tap it
BACK = "back"
