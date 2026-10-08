"""
constants.py — ảnh của nhiệm vụ Daily Activities "Offering" (thư mục ảnh ActivitiesOffer/).
"""
from ..constants import ROOT, OPEN, TAP

KEY = "daily_offering"   # key nhiệm vụ trong bot/worker/priority.py
LABEL = "Offering"   # ô tích ở tab Daily Activities, key daily_done
FOLDER = "ActivitiesOffer"
FOLDER_PATH = f"{ROOT}/{FOLDER}"
# Ảnh "đã xong" (thấy là nhiệm vụ hôm nay xong).
DONE_IMAGES = ("Offerdone.png", "Offerdone1.png", )
# (ảnh, action) theo thứ tự ưu tiên. Action chung (OPEN / TAP / ...) do common.run_task xử lý,
# action riêng (chuỗi) chuyển cho run.handle.
ACTIONS = (
    ("Offerfins.png", "finish_offer"),
    ("OfferGems.png", "offer_gems"),
    ("Offer1.png", "offer"),
    ("Offer.png", OPEN),
    ("Offer2.png", TAP),
)

# ---- Sau Go (giống Event, ../../event/kings_path/building.py open_building) --------------------
# Go -> về thành, Đền thờ (Shrine) ở giữa -> nhận ra theo ảnh mẫu civ (Event/Building/civ<N>/shrine,
# 0,97) -> bấm -> menu: icon "Offer" (Offer1.png, 0,98 tại (150, 216)) -> màn Offer (nút "Offer Gems"
# OfferGems.png 1,00 tại (108, 665); cạnh nó "Offer Tribute" dùng vật phẩm Tribute).
MENU_OFFER = f"{FOLDER_PATH}/Offer1.png"
OFFER_SCREEN = f"{FOLDER_PATH}/OfferGems.png"

# ---- Số lần Offer Gems (tab Daily Activities, ô "Offer Gems") ---------------------------------
# settings["Offer Gems"] = số lần bấm "Offer Gems" ở màn Offer (tốn kim cương mỗi lần). 0 = không offer,
# nhiệm vụ coi như xong hôm nay (không quay lại thử).
OFFER_GEMS_KEY = "Offer Gems"
OFFER_GEMS_CHOICES = (0, 3, 5, 10, 15, 20, 30)
OFFER_GEMS_DEFAULT = 10
OFFER_GEMS_WAIT = 2          # giây chờ sau mỗi lần bấm Offer Gems

# ---- Popup "Offer Gems" (bấm nút Offer Gems ở màn Offer) ---------------------------------------
# Ô số lượng bắt đầu ở 1 -> bấm "+" (số lần - 1) lần -> bấm "Offer". Game tự tính giá (Cost); tổng kim
# cương theo số lần: 1: 25, 2: 75, 3: 175, 4: 275, 5: 475, 10: 2675, 20: 15175, 30: 30175 (từ lần ~20
# mỗi lần 1500, xem OFFER_PRICE_TIERS). Ảnh đo trên tests/daily_activities/offering/screens/08_offer_gems_popup.png: tiêu đề
# 1,00 (màn khác <= 0,47), nút "+" 1,00 tại (324, 345), nút "Offer" 1,00 tại (198, 439) (màn khác <= 0,60).
POPUP_TITLE = f"{FOLDER_PATH}/PopupTitle.png"
POPUP_PLUS = f"{FOLDER_PATH}/PopupPlus.png"
POPUP_PLUS_REGION = (70, 44, 90, 54)   # % màn hình: chỉ nút "+" của popup
POPUP_OFFER = f"{FOLDER_PATH}/PopupOffer.png"
POPUP_WAIT = 3     # giây chờ popup hiện
BACKS_AFTER_OFFER = 2   # bấm Offer xong: Back 2 lần (đóng kết quả / màn Offer) về thành
PLUS_WAIT = 0.5    # giây giữa hai lần bấm "+"

# ---- Giá Offer Gems theo lượt trong ngày (offer_price / offer_total trong run.py) --------------
# (từ lượt thứ, giá mỗi lượt): 1: 25, 2: 50, 3-4: 100, 5-6: 200, 7-8: 400, 9-10: 600, 11-15: 1000,
# 16+: 1500. Đọc từ Cost thật (tests/daily_activities/offering/screens/*popup*): tổng 1: 25, 2: 75,
# 3: 175, 4: 275, 5: 475, 6: 675, 7: 1075, 8: 1475, 9: 2075, 10: 2675, 11: 3675, 20: 15175,
# 30: 30175, 42: 48175, 43: 49675, 94: 126175.
OFFER_PRICE_TIERS = ((1, 25), (2, 50), (3, 100), (5, 200), (7, 400), (9, 600), (11, 1000), (16, 1500))
POPUP_MINUS = f"{FOLDER_PATH}/PopupMinus.png"          # nút "-" (72, 345)
POPUP_MINUS_REGION = (10, 44, 30, 54)
POPUP_CLOSE = f"{FOLDER_PATH}/PopupClose.png"          # dấu X đỏ góc popup (363, 238)
