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
TRIBUTE_MONTH_KEY = "Alliance VIP: Tribute Monthly"
TRIBUTE_DAY_KEY = "Alliance VIP: Tribute Daily"
ALL_DONE_KEY = "Alliance VIP: All selected items"

# Màn Liên minh: dòng "Alliance Shop" (150, 499): 1,00. Màn Alliance Shop: tiêu đề "Alliance Shop" (199, 23): 1,00 (0,72 ở màn Liên minh).
SHOP_ROW = f"{FOLDER_PATH}/ShopRow.png"
SHOP_TITLE = f"{FOLDER_PATH}/ShopTitle.png"
# Ảnh điều hướng tới màn Liên minh (dùng chung với Alliance Science): nút Liên minh, dòng cuộn, popup ngoài liên minh.
ALLIANCE_NAV = (ALLIANCE_BUTTON, ALLIANCE_SCROLL, OUT_ALLIANCE)
# Tiêu đề chia vùng Monthly / Daily / Weekly trong cùng một phiên cuộn.
DAILY_HEADER = f"{FOLDER_PATH}/DailySale.png"
WEEKLY_HEADER = f"{FOLDER_PATH}/WeeklySale.png"   # tiêu đề "Weekly Sale" (199, 543): 1,00, cuối nhóm Daily; nhóm Monthly: 0,64
# Nút giá dưới sách (dy so với tâm sách ≈ +70): xanh = mua được (độ bão hoà HSV 190..212); xám = không mua được, vd chưa có thẻ tháng (35).
PRICE_DY = 70
PRICE_BOX = (90, 22)          # rộng, cao khung xét màu
PRICE_MIN_SATURATION = 100
ITEM_THRESHOLD = 0.86
LOCKED_ITEM_THRESHOLD = 0.90  # ngưỡng cao; so viền/góc, bỏ vùng ổ khóa giữa icon
# Popup mua: tìm dấu +, bấm đầu thanh bên trái nó để chọn MAX rồi xác nhận ảnh thanh MAX.
PLUS = f"{FOLDER_PATH}/popup_plus.png"
MAX_SLIDER = f"{FOLDER_PATH}/popup_max_slider.png"
MAX_SELECTED = f"{FOLDER_PATH}/popup_max_selected.png"
POPUP_TEMPLATE_THRESHOLD = 0.86
MAX_CROP_LEFT = 50            # từ tâm dấu + sang trái, bao trọn đầu thanh tại x - 35
MAX_CROP_HALF_HEIGHT = 18
MAX_SELECT_TRIES = 3
BUY_DY = 96
BUY_BUTTON_BOX = (130, 28)   # vùng quanh nút Buy trong popup số lượng
BUY_MIN_SATURATION = 100     # nút xanh/vàng hoạt động; nút xám không được bấm
CONFIRM_CHECKS = 5            # bấm mua xong chờ hộp xác nhận (Confirm) tối đa chừng này giây; bấm Confirm mới là mua thật
BUY_WAIT = 3                  # giây chờ sau khi bấm mua
POPUP_CHECKS = 5              # bấm giá xong chờ 1 giây, chưa có popup thì chờ thêm tối đa chừng này lần (1 giây / lần); vẫn không có = coi như xong
SCROLLS = 32                  # trần an toàn lớn; dừng sớm chỉ khi xác nhận đáy thật
SWIPE = (50, 68, 50, 46)      # % màn hình: cuộn Alliance Shop xuống (~155 px mỗi lần; vuốt dài / nhanh thì shop trôi quá, lỡ sách)
SWIPE_DURATION = 1.0          # vuốt 1s + dừng quét 1s = tối đa 2s mỗi bước
SCAN_SETTLE = 1.0
BOTTOM_CONFIRMATIONS = 3      # phải đứng yên 3 lần liên tiếp sau khi đã thấy Weekly Sale
BOTTOM_SIGNATURE_DISTANCE = 10  # dHash vùng nội dung <= ngưỡng này coi như không dịch chuyển
TOP_SWIPE = (50, 25, 50, 85)  # đưa carousel dọc về đầu trước mỗi lượt tìm ưu tiên
TOP_SWIPES = 6
TOP_SWIPE_DURATION = 0.35
TOP_SETTLE = 1.5
