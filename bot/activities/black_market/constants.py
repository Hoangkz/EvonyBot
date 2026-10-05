"""
constants.py — Black Market image folders and limits.
"""
BM = "Black Market"
BUY = f"{BM}/buy"

MIN_GOLD = 2_000_000
BUY_THRESHOLD = 0.85
BALANCE_RETRIES = 2          # C# goldTemp: tolerate two unreadable wallet frames
# Price-button centers.  Currency icons are searched only inside these boxes;
# the old full-screen templates also matched item art and the wallet row.
MARKET_SLOTS = ((80, 365), (200, 365), (320, 365),
                (80, 522), (200, 522), (320, 522))
PRICE_HALF = (48, 18)
GEM_ICONS = (f"{BM}/gems.png", "Event/KingsPath/BlackMarket/gem.png")
GOLD_ICONS = (f"{BM}/goldCheck.png", f"{BM}/gold.png")
GEM_ICON_THRESHOLD = 0.70
GOLD_ICON_THRESHOLD = 0.68
# (x, y, w, h) compared before/after Refresh to tell when the market changed.
MARKET_REGION = (45, 330, 120, 400)
