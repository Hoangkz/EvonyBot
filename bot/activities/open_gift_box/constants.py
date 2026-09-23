"""
constants.py — Open Gift Box image folders, limits and action names.
"""
SETUP = "OpenBox/Setup"

# "Selection Gift Box" checkbox -> folder of box images (C# ListGiftBox 1..6).
BOX_FOLDERS = {
    "Gift Box Alliance": "OpenBox/Alliance",
    "Gift Box Boss": "OpenBox/Boss",
    "Gift Box Resource": "OpenBox/BoxResource",
    "Gems": "OpenBox/Gems",
    "Gold": "OpenBox/Gold",
    "Etc": "OpenBox/etc",
}
ALL_BOXES = "All Gift Box"

BOX_THRESHOLD = 0.8
# Boxes whose top edge is below this are behind the bottom bar: scroll instead.
MAX_BOX_Y = 650

# What to do when each image is seen.
CONFIRM = "confirm"
BOX_LIST = "box_list"       # gift box list open -> tap the next wanted box
MAX = "max"                 # quantity dialog -> Max, then Use
TAP = "tap"
USE = "use"                 # tap, and skip waiting for "success" after the next Max
BACK = "back"
