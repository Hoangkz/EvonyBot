"""
constants.py — Black Market image folders and limits.
"""
BM = "Black Market"
BUY = f"{BM}/buy"

MIN_GOLD = 2_000_000
BUY_THRESHOLD = 0.85
GEMS_MIN_Y = 240            # gem price tags above this are not market slots
# (x, y, w, h) compared before/after Refresh to tell when the market changed.
MARKET_REGION = (45, 330, 120, 400)
