"""
constants.py — ảnh của nhiệm vụ Daily Activities "Trade Carriage" (thư mục ảnh ActivitiesTradeCarriage/).
"""
from ..constants import ROOT

KEY = "daily_trade_carriage"   # key nhiệm vụ trong bot/worker/priority.py
LABEL = "Trade Carriage"   # ô tích ở tab Daily Activities, key daily_done
FOLDER = "ActivitiesTradeCarriage"
FOLDER_PATH = f"{ROOT}/{FOLDER}"

# ---- Sau Go (run.after_go) --------------------------------------------------------------------
# Go -> ra thẳng màn Trade Carriage (tab My Carriage). Có hộp quà nổi trên xe (xe đã tới nơi) -> bấm nhận trước.
# Dispatch -> bảng hàng hoá: nút Refresh Goods còn dòng "First Refresh Free" thì bấm (lượt free duy nhất):
#   - hiện popup "...quality. Refreshing may reduce its quality. Refresh anyway?" -> Back (không đổi hàng);
#   - không hiện gì -> hàng đã đổi.
# rồi Select Formation -> xe xuất phát, hiện bảng xe vừa đi -> bấm tab My Carriage (REVIEW_CLOSE) về màn My Carriage.
# Lặp tối đa DISPATCH_MAX lần (mỗi ngày game cho 4 lượt, "Transports Left Today").
TRADE_TITLE = f"{FOLDER_PATH}/TradeCarriageTitle.png"   # tiêu đề màn Trade Carriage
DISPATCH = f"{FOLDER_PATH}/Dispatch.png"                # nút Dispatch dưới cùng màn My Carriage
GIFT_BOXES = (f"{FOLDER_PATH}/GiftBox.png", f"{FOLDER_PATH}/GiftBox2.png")   # GiftBox2: rương trong bong bóng kem, dưới nút Packages (21913: tâm (342, 266), 1,00; khác <= 0,39)
GIFT_BOX = GIFT_BOXES[0]                 # hộp quà nổi trên xe đã tới nơi (bấm nhận ngay, không hiện popup)
# Popup nhận quà xong: chữ "Congratulations!" dùng chung (CollectionActivities, 0,999) — CHƯA kiểm tra trên màn Trade Carriage thật (TODO.md).
GIFT_POPUP = f"{ROOT}/CollectionActivities/CongratulationsCurrent.png"
GIFT_POPUP_WAITS = 6               # sau 1 giây đầu chưa thấy popup: chờ thêm chừng này lần (1 giây / lần) rồi bỏ qua quà
GIFT_MAX = 6                       # số hộp quà tối đa nhận liên tiếp mỗi lần
REFRESH_FREE = f"{FOLDER_PATH}/RefreshFree.png"         # "First Refresh Free" trên nút Refresh Goods
REFRESH_CONFIRM = f"{FOLDER_PATH}/RefreshConfirm.png"   # chữ "quality. Refresh anyway?" của popup hỏi lại
SELECT_FORMATION = f"{FOLDER_PATH}/SelectFormation.png"
MARCH_BUTTON = f"{FOLDER_PATH}/MarchButton.png"         # Select Formation mở màn March: bấm nút March cam dưới cùng
THRESHOLD = 0.8                    # ngưỡng khớp mọi ảnh của nhiệm vụ
REVIEW_CLOSE = (26, 11)            # % màn hình, tab My Carriage: bấm để đóng bảng xe sau March, về màn My Carriage
DISPATCH_TRIES = 5                 # số lần bấm Dispatch (mỗi lần chờ POPUP_WAIT giây bảng hàng) trước khi coi là hết lượt
DISPATCH_MAX = 4                   # số lần Dispatch tối đa mỗi ngày
SCREEN_WAIT = 8                    # giây chờ màn Trade Carriage sau Go
POPUP_WAIT = 8                     # giây chờ bảng hàng hoá / popup hiện
MARCH_WAIT = 10                     # giây chờ màn March sau khi bấm Select Formation
RESULT_WAIT = 2                    # giây chờ sau mỗi lần bấm
BACKS_AFTER = 4                    # xong: Back (tối đa chừng này lần) tới khi về thành
