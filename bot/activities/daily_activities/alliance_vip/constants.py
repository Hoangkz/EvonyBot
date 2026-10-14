"""
constants.py — ảnh / hằng số của nhiệm vụ Daily "Alliance VIP" (mua VIP theo tháng và theo ngày ở Alliance Shop).
Ảnh nằm trong Images/DailyActivites/ActivitiesAllianceVip/, đo trên máy 21913 (396x704).
"""
from ...event.kings_path.black_market.constants import CONFIRM as CONFIRM_BUTTON
from ...event.kings_path.donate.constants import (
    ALLIANCE_BUTTON,
    ALLIANCE_SCROLL,
    NAV_MAX_STEPS,
    OUT_ALLIANCE,
)
from ..constants import ROOT

LABEL = "Alliance VIP"   # ô tích ở tab Daily Activities (mặc định tích), key trong settings
FOLDER = "ActivitiesAllianceVip"
FOLDER_PATH = f"{ROOT}/{FOLDER}"
# Dấu "xong hôm nay" riêng cho từng loại (daily_done): xong cả hai thì nhiệm vụ xong.
MONTH_KEY = "Alliance VIP: Monthly"
DAY_KEY = "Alliance VIP: Daily"

# Màn Liên minh: dòng "Alliance Shop" (150, 499): 1,00. Màn Alliance Shop: tiêu đề "Alliance Shop" (199, 23): 1,00 (0,72 ở màn Liên minh).
SHOP_ROW = f"{FOLDER_PATH}/ShopRow.png"
SHOP_TITLE = f"{FOLDER_PATH}/ShopTitle.png"
# Ảnh điều hướng tới màn Liên minh (dùng chung với Alliance Science): nút Liên minh, dòng cuộn, popup ngoài liên minh.
ALLIANCE_NAV = (ALLIANCE_BUTTON, ALLIANCE_SCROLL, OUT_ALLIANCE)
# Shop có nhiều nhóm xếp dọc: "Monthly Card Items" (trên cùng), "Daily Sale", "Weekly Sale"... Sách "100 VIP Points" có ở cả nhóm
# Monthly (206, 218: 1,00) và Daily Sale (82, 419: 0,91); khác <= 0,40 -> ngưỡng 0,85. Tiêu đề nhóm "Daily Sale" (199, 494): 1,00, ra khỏi
# màn khi cuộn (0,69). Sách ở TRÊN tiêu đề = Monthly, ở DƯỚI = Daily; không thấy tiêu đề mà đã cuộn = Daily.
VIP_ICON = f"{FOLDER_PATH}/VipIcon.png"
VIP_THRESHOLD = 0.85
DAILY_HEADER = f"{FOLDER_PATH}/DailySale.png"
WEEKLY_HEADER = f"{FOLDER_PATH}/WeeklySale.png"   # tiêu đề "Weekly Sale" (199, 543): 1,00, cuối nhóm Daily; nhóm Monthly: 0,64
# Nút giá dưới sách (dy so với tâm sách ≈ +70): xanh = mua được (độ bão hoà HSV 190..212); xám = không mua được, vd chưa có thẻ tháng (35).
PRICE_DY = 70
PRICE_BOX = (90, 22)          # rộng, cao khung xét màu
PRICE_MIN_SATURATION = 100
# Popup mua: thanh số lượng, bấm "+" PLUS_TAPS lần rồi bấm nút mua (xanh, dưới thanh, cách "+" ~96 px; tâm giữa màn). Ảnh "+": ảnh của
# Buy Stamina / Hammer (0,98).
PLUS = "DailyActivites/ActivitiesBuyDaily/plus.png"
PLUS_TAPS = 5
PLUS_WAIT = 0.5               # giây giữa hai lần bấm "+"
BUY_DY = 96
CONFIRM_CHECKS = 5            # bấm mua xong chờ hộp xác nhận (Confirm) tối đa chừng này giây; bấm Confirm mới là mua thật
BUY_WAIT = 3                  # giây chờ sau khi bấm mua
POPUP_CHECKS = 5              # bấm giá xong chờ 1 giây, chưa có popup thì chờ thêm tối đa chừng này lần (1 giây / lần); vẫn không có = coi như xong
SETTLE_TRIES = 3              # đầu trang chưa thấy sách Monthly: chụp lại chừng này lần (1 giây / lần) trước khi cuộn xuống
SCROLLS = 16                  # số lần cuộn xuống tối đa để tìm sách Daily
SWIPE = (50, 68, 50, 46)      # % màn hình: cuộn Alliance Shop xuống (~155 px mỗi lần; vuốt dài / nhanh thì shop trôi quá, lỡ sách)
SWIPE_DURATION = 1.2          # giây: vuốt chậm để không bị trôi thêm
BOTTOM_SWIPE = (50, 85, 50, 15)   # % màn hình: kéo thật nhanh xuống cuối trang (sách Daily luôn ở cuối, ngay trên tiêu đề Weekly Sale)
BOTTOM_SWIPE_DURATION = 0.15  # giây, không chờ giữa các lần
BOTTOM_SWIPES = 6
BOTTOM_SETTLE = 1.5           # giây chờ shop hết trôi sau khi kéo xuống cuối
