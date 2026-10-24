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
# Dấu "xong hôm nay" (daily_done) của VIP / Tribute ở Daily Sale; không mua Monthly (trên tiêu đề Daily Sale).
DAY_KEY = "Alliance VIP: Daily"
TRIBUTE_DAY_KEY = "Alliance VIP: Tribute Daily"

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
# Ba Truce dùng cùng hình con chim, chỉ khác màu nền. Sau khi khớp
# hình phải phân loại thêm histogram Hue: 8h=tím, 24h=cam, 3d=vàng.
TRUCE_COLOR_SATURATION_MIN = 80
TRUCE_COLOR_VALUE_MIN = 50
# Popup mua: tìm dấu +, bấm đầu thanh bên trái nó để chọn MAX rồi xác nhận ảnh thanh MAX.
PLUS = f"{FOLDER_PATH}/popup_plus.png"
MAX_SLIDER = f"{FOLDER_PATH}/popup_max_slider.png"
MAX_SELECTED = f"{FOLDER_PATH}/popup_max_selected.png"
POPUP_TEMPLATE_THRESHOLD = 0.86
MAX_CROP_LEFT = 50            # từ tâm dấu + sang trái, bao trọn đầu thanh tại x - 35
MAX_CROP_HALF_HEIGHT = 18
MAX_SELECT_TRIES = 3
MAX_BAR_WIDTH = 240           # từ tâm dấu + sang trái: cả thanh số lượng (so trước / sau khi bấm)
MAX_BAR_STILL_DIFF = 3        # chênh lệch trung bình < chừng này = thanh không đổi (chỉ còn 1 lượt, VD 100 Chips 1 / 1)
BUY_DY = 96
BUY_BUTTON_BOX = (130, 28)   # vùng quanh nút Buy trong popup số lượng
BUY_MIN_SATURATION = 100     # nút xanh/vàng hoạt động; nút xám không được bấm
BUY_WAIT = 3                  # giây chờ sau khi bấm Confirm (hộp mua tự đóng, không có ảnh để wait_for)
# Mọi lần chuyển màn đều wait_for ảnh của màn đích: 1 giây kiểm tra một lần, tối đa 6 lần.
WAIT_INTERVAL = 1
WAIT_TIMEOUT = 6 * WAIT_INTERVAL
SCROLLS = 32                  # trần an toàn lớn; dừng sớm chỉ khi xác nhận đáy thật
SWIPE = (50, 80, 50, 30)      # % màn hình: cuộn Alliance Shop xuống (50% màn, ~350 px mỗi lần; vuốt dài / nhanh thì shop trôi quá, lỡ sách)
SWIPE_UP = (50, 30, 50, 80)   # ngược SWIPE: cuộn lên (sau khi cuộn nhanh xuống VIP/Tribute)
SWIPE_DURATION = 1.0          # vuốt 1s + dừng quét 1s = tối đa 2s mỗi bước
UNFOCUS_TAP = (50, 3)         # % màn hình: bấm tiêu đề shop trước mỗi lần cuộn (lỡ bấm vật phẩm thì shop không cuộn được)
SCAN_SETTLE = 1.0
# Giới hạn cuộn xuống: Truce dưới tiêu đề Weekly Sale (hàng cuối); giới hạn cuộn lên: tiêu đề Daily Sale.
# Có tích VIP / Tribute: cuộn thật nhanh xuống tới chúng ở Daily Sale. Đo trên 21913: cú thứ 2 đã thấy cả hai ngay trên Weekly Sale.
FAST_SWIPE = (50, 90, 50, 20)
FAST_SWIPE_DURATION = 0.1
FAST_SWIPES = 3
