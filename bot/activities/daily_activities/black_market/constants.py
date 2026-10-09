"""
constants.py — ảnh của nhiệm vụ Daily Activities "Black Market" (thư mục ảnh ActivitiesBuyMarket/).
"""
from ..constants import ROOT, OPEN, TAP

KEY = "daily_black_market"   # key nhiệm vụ trong bot/worker/priority.py
LABEL = "Black Market"   # ô tích ở tab Daily Activities, key daily_done
FOLDER = "ActivitiesBuyMarket"
FOLDER_PATH = f"{ROOT}/{FOLDER}"
# Ảnh "đã xong" (thấy là nhiệm vụ hôm nay xong).
DONE_IMAGES = ("BlackMarketFinishCurrent.png", "BlackMarketFinish.png", )
# (ảnh, action) theo thứ tự ưu tiên. Action chung (OPEN / TAP / ...) do common.run_task xử lý,
# action riêng (chuỗi) chuyển cho run.handle.
ACTIONS = (
    ("Confirm.png", TAP),
    ("Market.png", "buy"),
    ("Market1.png", "buy"),
    ("BuyMarket.png", "market"),
    ("ActivitiesBlackMarket.png", OPEN),
)

# ---- Luồng mới sau Go (run.after_go), giống hệt King's Path Black Market sau Go --------------------
# Go -> về thành, Chợ ở giữa -> menu "Black Market" -> event/kings_path/black_market buy_items: mua các món không
# trả bằng kim cương (mua hết bộ thì Instant Refresh) cho đủ BUY_GOAL lần.
# Nhiệm vụ có nhiều mốc: "Buy ... for 1 time(s)" xong thì ra "for 3 time(s)" (tối đa 3 lần) -> mua luôn 3 lần trong một
# lượt, không theo số đang ghi trên dòng.
BUY_GOAL = 3
