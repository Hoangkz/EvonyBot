"""
constants.py — Event image folders, limits and action names.
"""
from . import milestones

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
# Icon event King's Path (hộp quà, không lấy chấm đỏ góc trên phải) trong danh sách event:
# khớp 1,00 tại (45, 512) (tests/event/kings_path/screens/04_event_list.png); màn khác <= 0,47.
KINGS_PATH_ICON = f"{EV}/KingsPath/icon.png"

# Tiêu đề màn event (đầu màn, tâm (199, 23)): thấy là đang ở sẵn bảng event đó.
# "Gather Troops": 1,00 trên 20 màn Gather Troops trong tests; màn khác (cả King's Path) <= 0,50.
GATHER_TROOPS_TITLE = f"{EV}/GatherTroops/title.png"
# "King's Path": 1,00 trên mọi màn King's Path; màn khác <= 0,74 (xem kings_path/constants.py).
KINGS_PATH_TITLE = f"{EV}/KingsPath/title.png"
EVENT_TITLE_REGION = (20, 0, 80, 8)   # % màn hình: thanh tiêu đề

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
# Số lớn bị xuống dòng (chỉ gặp ở nhiệm vụ train lính, VD "23,530 /" + "50,000"): dòng 1 cao hơn
# ~5 px, dòng 2 ngay dưới. Đọc bằng read_progress.run_two_lines khi đọc 1 dòng lỗi.
PROGRESS_LINE1_FROM_GO = (-70, -53, 111, 13)
PROGRESS_LINE2_FROM_GO = (-70, -41, 111, 13)

# Ổ khoá trên tab "Day N" chưa mở (hàng tab Day 1..Day 5, y ~209). Ngày khoá luôn là các
# ngày cuối: đếm được N ổ khoá thì DAY_TABS - N + 1 .. DAY_TABS đang khoá (VD 4 -> Day 2..5).
# Đo trên King's Path (Day 4, Day 5 khoá): Day 4 khớp 1,00, Day 5 0,74 (nền tab lệch);
# hàng tab không khoá <= 0,43, 148 màn khác <= 0,57 -> ngưỡng 0,7, chỉ tìm ở hàng tab.
DAY_LOCK = f"{EV}/dayLock.png"
DAY_LOCK_THRESHOLD = 0.7
DAY_TABS_REGION = (0, 26, 100, 33)   # % màn hình: hàng tab Day
DAY_TABS = 5

# ---- Nhận thưởng theo chấm đỏ (claim.py) -----------------------------------------
# Chấm đỏ ở góc trên phải tab Day / tab phụ = còn thưởng chưa nhận. Nhận theo MÀU (template
# trượt trên hàng tab phụ vì nền sau chấm khác nhau): điểm ảnh R > 150, G < 70, B < 60, khối
# liền DOT_AREA px. Đo trên 10 màn King's Path + màn Gather Troops: tâm chấm hàng Day y 191
# (x 77 / 153 / 228 ...), hàng tab phụ y 234..235 (x 128 / 253 / 379), diện tích 16..21 px.
# Màn khác có nhiều khối đỏ -> chỉ quét 2 hàng này khi đang ở màn event.
DOT_DAY_Y = 191
DOT_TAB_Y = 235
DOT_ROW_HALF = 8           # quét y +- mức này quanh mỗi hàng
DOT_AREA = (12, 30)        # diện tích khối đỏ (px) được coi là chấm
# Bấm vào tab có chấm: lệch từ tâm chấm vào trong tab (chấm ở góc trên phải tab).
DOT_TAP_OFFSET = (-25, 14)
CLAIM_MAX_STEPS = 30       # số bước tối đa của một lượt nhận thưởng

# Rương mốc trên đầu màn Gather Troops: (tâm icon, mốc ghi dưới icon). Con số MỐC để riêng ở
# milestones.py (sửa ở đó khi game đổi mốc); ở đây chỉ là vị trí 5 rương trái -> phải.
# Rương nhận được = mốc <= số đã làm ở dòng "Progress:12 / 70" (OCR bot.ocr.read_milestone,
# vùng cắt MILESTONE_BOX) và chưa có dấu tích. Nhận xong rương có dấu tích.
GATHER_CHEST_POSITIONS = [(70, 83), (122, 83), (173, 83), (224, 83), (275, 83)]
GATHER_CHESTS = list(zip(GATHER_CHEST_POSITIONS, milestones.GATHER_TROOPS, strict=True))
MILESTONE_BOX = (100, 121, 160, 14)   # (x, y, w, h) cả dòng "Progress:12 / 70"
# Dấu tích xanh trên rương đã nhận (tâm lệch (+1, -1) so với tâm icon): rương 5 1,00, rương 10
# vừa nhận 0,86 (gather_chest_claimed.png); rương chưa nhận <= 0,57 -> 0,8.
CHEST_TICK = f"{EV}/chestTick.png"
CHEST_TICK_THRESHOLD = 0.8
CHEST_HALF = 18   # tìm dấu tích trong ô 36x36 quanh tâm icon
# Bấm rương -> băng "Congratulations!" giữa màn (199, 319) che các dòng nhiệm vụ (cả nút Go):
# chờ băng mất (tối đa CONGRATS_WAIT giây) rồi mới bấm tiếp. 1,00; màn khác <= 0,45.
CONGRATULATIONS = f"{EV}/congratulations.png"
CONGRATS_WAIT = 5

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
