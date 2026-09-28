"""
constants.py — Join Monster War images, limits and action names.
"""
JB = "JoinBoss"
JOIN = f"{JB}/thamgia.png"
MARCH = f"{JB}/hanhquan.png"
TROOP_CHECK = f"{JB}/checkLocam.png"
LOCATION = f"{JB}/location.png"
# Optional general selection in the march screen (C# selectGeneral ->
# chooseDevelopment -> chooseFavorite -> Select).
SELECT_GENERAL = f"{JB}/selectGeneral.png"
CHOOSE_DEVELOPMENT = f"{JB}/chooseDevelopment.png"
CHOOSE_FAVORITE = f"{JB}/chooseFavorite.png"
SELECT = f"{JB}/Select.png"
CERBERUS = f"{JB}/Boss/cerberus.png"
STAMINA_ITEM = f"{JB}/theluc.png"
USE_STAMINA = f"{JB}/usetheluc.png"
PLUS = f"{JB}/plus.png"

JOIN_MIN_Y, JOIN_MAX_Y = 262, 615   # "Join" buttons outside this band are ignored
NOT_JOIN_LIMIT = 30                 # rallies remembered as already handled
SAME_SPOT = 10                      # px: two positions closer than this are the same rally

# What to do when each image is seen.
OUT_OF_STAMINA = "out_of_stamina"
MARCH_SCREEN = "march_screen"
JOIN_LIST = "join_list"
SCROLL = "scroll"
JOINED = "joined"
TAP = "tap"
BACK = "back"
ALLIANCE = "alliance"
LEAVE_ALLIANCE_POPUP = "leave_alliance_popup"
