"""
constants.py — Battlefield Shop image folders and limits.
"""
BS = "BattlefieldShop"
BM = "Black Market"         # shared buttons (Refresh, confirm, Daily Activities...)
BUY = f"{BS}/buy"

BUY_THRESHOLD = 0.8
MIN_MEDALS = 310            # below this (next to tien2.png) a Refresh can't be paid
MEDALS_WIDTH = 80           # width of the medal counter right of tien2.png
# (x, y, w, h) compared before/after Refresh to tell when the shop changed.
SHOP_REGION = (45, 330, 120, 400)
