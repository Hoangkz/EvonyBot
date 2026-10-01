"""
constants.py — Event image folders, limits and action names.
"""
EV = "Event"

# ---- Quà đăng nhập (Login Gifts) ---------------------------------------
# Icon dấu tích của nút "Login Gifts" trên màn hình chính (cột phải và góc dưới trái
# đều có; nút biến mất khi đã nhận). Khớp 1,00 trên màn chính; tab "Login Gifts" trong
# màn Super Value Return cũng khớp 0,88 -> LOGIN_GIFT_TITLE được xét trước để màn đó
# không bị nhận nhầm là màn chính.
LOGIN_GIFT_ICON = f"{EV}/LoginGift/icon.png"
# Chữ vàng "Login Gifts" trên banner màn Super Value Return (khớp 0,96 tại (56, 141);
# màn khác cao nhất 0,60).
LOGIN_GIFT_TITLE = f"{EV}/LoginGift/title.png"
# Hộp quà tròn ngay dưới chữ "Login Gifts" trên banner (bấm để nhận quà ngày hiện tại),
# tính từ tâm chữ "Login Gifts": (56, 141) -> hộp quà (37, 197). Đo trên ảnh Day 5 và Day 6
# (cùng vị trí, không phụ thuộc ngày).
LOGIN_GIFT_REWARD_OFFSET = (-19, 56)

# ---- Màn hình chính -----------------------------------------------------
# Nút "•••" ở cột phải màn hình chính (dùng chung với get_server): khớp 0,96 trên mọi
# ảnh màn chính, màn khác <= 0,59. Thấy nút này mới đi tìm Event Center.
MAIN_SCREEN = "Server/listActivity.png"

# ---- Event Center ------------------------------------------------------
# Chữ "Event Center" ở cột phải màn hình chính; nút event nằm ngay dưới. Icon cúp có
# hiệu ứng lấp lánh nên chỉ lấy phần chữ, và ảnh là TRUNG VỊ của 60 khung hình chụp
# trong 1 phút (tests/event/screens/event_center, vùng x 336-383, y 228-254) để không
# lệch theo một khung hiệu ứng nào.
EVENT_CENTER = f"{EV}/eventCenter.png"
# Vị trí không cố định (bị đẩy lên/xuống theo số nút phía trên) nhưng luôn ở góc trên
# bên phải: chỉ tìm trong vùng này (% màn hình). Đã gặp: y 161 / 229 / ~310 trên 704.
EVENT_CENTER_REGION = (60, 0, 100, 50)
# Tìm lần lượt trên CÙNG một ảnh chụp, ngưỡng giảm dần (cùng ảnh thì điểm khớp cố định:
# ngưỡng trước không thấy thì chỉ còn ý nghĩa thử ngưỡng thấp hơn).
# Đo 80 ảnh màn chính (2 máy, nhiều nền, ảnh 2025) / 57 màn khác:
#   0,85 / 0,80 -> thấy 80/80 (thấp nhất 0,883), không khớp nhầm màn nào.
#   0,75 .. 0,65: dự phòng nền hay hiệu ứng lạ; màn khác cao nhất 0,436.
EVENT_CENTER_THRESHOLDS = (0.85, 0.80, 0.75, 0.70, 0.65)
# Nút event ngay dưới chữ "Event Center": bấm lệch so với tâm chữ (x, y).
EVENT_BUTTON_OFFSET = (10, 40)
# Không thấy Event Center trên màn chính: kéo màn hình rồi quét lại. Toạ độ % màn hình
# (x1, y1, x2, y2) của một lần vuốt; mỗi chiều vuốt 3 lần.
SWIPE_RIGHT = (30, 50, 70, 50)   # ngón tay kéo từ trái sang phải
SWIPE_UP = (50, 70, 50, 30)      # ngón tay kéo từ dưới lên
SWIPE_TIMES = 3

# ---- Danh sách event (màn mở ra sau khi bấm nút dưới Event Center) -----
# VD màn "Wine Festival Event": Login Rewards rồi danh sách event (Gather Troops,
# Historic General Summoning, ...). Không thấy icon event cần tìm thì cuộn xuống,
# quá EVENT_LIST_MAX_SCROLLS lần vẫn không thấy thì BACK.
EVENT_LIST_SWIPE = (50, 80, 50, 50)   # % màn hình, ngón tay kéo lên = cuộn danh sách xuống
EVENT_LIST_MAX_SCROLLS = 4
# Icon event Gather Troops trong danh sách: khớp 1,00 tại (50, 362); 126 màn khác <= 0,23.
GATHER_TROOPS_ICON = f"{EV}/GatherTroops/icon.png"
# Icon event King's Path trong danh sách. TODO: chưa có ảnh -> nhiệm vụ King's Path bỏ qua
# (xem kings_path/path_task.py) cho tới khi cắt ảnh này từ màn danh sách event.
KINGS_PATH_ICON = f"{EV}/KingsPath/icon.png"

# ---- Màn một event (Gather Troops, King's Path, ...) -------------------
# Nút "Claim All" ở cuối màn event: thấy là bấm trước mọi thứ khác. Khớp 1,00;
# màn khác <= 0,66 (nút "Claimed").
CLAIM_ALL = f"{EV}/claimAll.png"
# Lỗi game: bấm Claim All mà nút không mất. Bấm liên tiếp quá CLAIM_ALL_MAX_TAPS lần (không
# gặp màn nào khác xen giữa) -> Back, đếm lại từ 0, vòng lặp chạy tiếp.
CLAIM_ALL_MAX_TAPS = 10
# Nút "Go" của mỗi dòng nhiệm vụ (cột phải, x ~335): khớp 0,99; màn khác <= 0,60.
GO_BUTTON = f"{EV}/goButton.png"
GO_REGION = (70, 35, 100, 100)   # % màn hình: cột nút dưới hàng tab
# Tiến độ "300 / 500" của dòng nhiệm vụ, căn phải ngay trên nút Go: vùng cắt (dx, dy, w, h)
# tính từ tâm nút Go (đo: tâm Go (335, 344) -> chữ x 315-374, y 297-309). Đọc bằng
# bot.ocr.read_progress (font Images/OCR/Progress).
PROGRESS_FROM_GO = (-70, -48, 111, 14)

# Ổ khoá trên tab "Day N" chưa mở (hàng tab Day 1..Day 5, y ~209). Ngày khoá luôn là các
# ngày cuối: đếm được N ổ khoá thì DAY_TABS - N + 1 .. DAY_TABS đang khoá (VD 4 -> Day 2..5).
# Đo trên King's Path (Day 4, Day 5 khoá): Day 4 khớp 1,00, Day 5 0,74 (nền tab lệch);
# hàng tab không khoá <= 0,43, 148 màn khác <= 0,57 -> ngưỡng 0,7, chỉ tìm ở hàng tab.
DAY_LOCK = f"{EV}/dayLock.png"
DAY_LOCK_THRESHOLD = 0.7
DAY_TABS_REGION = (0, 26, 100, 33)   # % màn hình: hàng tab Day
DAY_TABS = 5

# Ngưỡng riêng của ảnh dùng chung; nhiệm vụ ghép thêm ngưỡng của mình
# ({**THRESHOLDS, ...} trong constants.py của nhiệm vụ).
THRESHOLDS = {
    LOGIN_GIFT_TITLE: 0.85,
}

# ---- Actions -----------------------------------------------------------
CLAIM_LOGIN_GIFT = "claim_login_gift"
OPEN_LOGIN_GIFT = "open_login_gift"
ON_MAIN_SCREEN = "on_main_screen"
BACK, TAP = "back", "tap"
CLAIM = "claim_all"   # nút Claim All (đếm số lần bấm liên tiếp, xem CLAIM_ALL_MAX_TAPS)
