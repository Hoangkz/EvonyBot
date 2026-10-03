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
# trong 1 phút (vùng x 336-383, y 228-254) để không lệch theo một khung hiệu ứng nào.
# tests/event/screens/event_center giữ 10 khung khác nhau nhất trong 60 khung đó.
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
# Nút event ngay dưới chữ "Event Center": lệch so với tâm chữ (x, y). Chỉ bấm vào đây khi không
# tìm thấy ruy băng nào (xem RIBBON_SEARCH).
EVENT_BUTTON_OFFSET = (10, 40)

# ---- Nút event (nút có ruy băng đỏ đếm ngược "3d 14:00") -------------------
# Đuôi trái ruy băng 7x7 (toàn phần đỏ, không dính nền lẫn chữ số); icon nút đổi theo mùa
# (ly rượu, ly bia...) và chữ trên ruy băng chạy liên tục nên chỉ đuôi là cố định. Đuôi phải
# hay bị mép màn hình cắt nên không dùng. Cắt từ x 250-256, y 170-176 (tâm (253, 173)) ảnh
# Screenshot_20261003-005902. Đo 2 máy x 60 khung trong 1 phút (tests/event/screens/ribbon:
# giữ 10 khung khác nhau nhất mỗi máy, 01-10 máy 21913, 11-20 máy 21923) + 129 ảnh màn chính trong tests: ruy băng
# thật 0,982..1,00 (vùng đuôi không đổi giữa các khung); ruy băng vương miện "2d 22:39" (không
# phải nút event) không khớp.
RIBBON_TAIL = f"{EV}/ribbonTail.png"
# Trên chính ảnh chụp vừa thấy nút "•••", tìm đuôi ở 2 vùng cố định (% màn hình): vùng nào trả về
# toạ độ thì vùng đó đúng -> MỘT nút duy nhất (cả 2 cùng thấy thì lấy chỗ khớp cao hơn; trên các
# ảnh đo chỉ 1 vùng có ruy băng). Mỗi vùng một dãy ngưỡng giảm dần: lần đầu ngưỡng đầu, không vùng
# nào đạt thì thử tiếp 3 ngưỡng thấp hơn; vẫn không thấy thì bấm Event Center + EVENT_BUTTON_OFFSET
# như trước.
# KHÔNG tìm nút trên cùng bên phải (đuôi (331, 105) = (83.6%, 14.9%), có trên mọi màn chính):
# không phải nút event.
#   Cột trái  x 60-70 %, y 12-40 % (x 237-277, y 84-281): đuôi (253, 105) / (253, 173);
#             chỗ khác cao nhất 0,794 -> sàn 0,80.
#   Cột phải  x 80-100 %, y 30-50 % (x 316-396, y 211-352): đuôi (331, 240) / (331, 308);
#             chỗ khác cao nhất 0,834 (ruy băng vương miện, (368, 309)) -> sàn 0,845.
RIBBON_SEARCH = [
    ((60, 12, 70, 40), (0.86, 0.84, 0.82, 0.80)),
    ((80, 30, 100, 50), (0.86, 0.855, 0.85, 0.845)),
]
# Bấm vào icon nút: lệch so với tâm đuôi ruy băng (đuôi (253, 173) -> icon (283, 145)).
RIBBON_BUTTON_OFFSET = (30, -28)
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
# Bấm nút event mà không vào được danh sách (không thấy tiêu đề "Wine Festival Event", cuộn hết
# không thấy icon -> Back): thử lại thêm EVENT_OPEN_RETRIES lần (về màn chính, bấm nút event lại);
# vẫn không được thì dừng nhiệm vụ, chuyển sang nhiệm vụ khác. Vào được danh sách (thấy tiêu đề) thì
# đếm lại từ 0; đã ở danh sách mà cuộn hết không thấy icon = event không có -> dừng luôn, không thử lại.
EVENT_OPEN_RETRIES = 2
# Tiêu đề màn danh sách event ("Wine Festival Event"; đổi theo đợt lễ hội, cố định khi cuộn): thấy =
# đã vào danh sách. Cắt cả khúc giữa thanh tiêu đề (60, 8) 276x30 để tên dài / ngắn hơn vẫn nằm trong
# ô. Khớp 1,00 trên 7 ảnh 04_event_list.png; 315 màn khác <= 0,49. Bấm nút event xong chờ tối đa
# EVENT_LIST_WAIT giây; không thấy (đổi đợt lễ hội / chưa tải) vẫn cuộn tìm icon (open_event).
EVENT_LIST_TITLE = f"{EV}/EventList/title.png"
# ---- Rương Login Rewards ở đầu danh sách event (claim_login_reward trong common.py) ----------
# Mỗi ngày kiểm 1 lần (daily_done LOGIN_REWARD_KEY, tới lần reset server): tìm đầu thanh tiến độ
# màu cam dưới hàng rương (progressTip.png, (122, 306) trên event_list_reward.png: 1,00; (68, 306)
# trên event_list_reward_opened.png: 0,99; màn khác <= 0,66). Rương của hôm nay nằm ngay trên đầu
# thanh: tìm rương đã mở (chestOpened.png, nắp mở) trong ô CHEST_FROM_TIP quanh đó — đã mở 1,00,
# chưa mở <= 0,43. Đã mở -> lưu DB, bỏ qua. Chưa mở -> bấm (đầu thanh x, y - 35) -> lưu DB (bấm xong
# không có popup, vẫn ở danh sách event -> tìm icon tiếp). Bấm đúng y của đầu thanh (trên thanh tiến
# độ) không nhận được (thử thật máy 21923: (48, 306) không nhận; (48, 266) trên rương thì nhận).
# Không thấy đầu thanh -> không lưu (lần sau kiểm lại).
LOGIN_REWARD_KEY = "event_login_reward"
PROGRESS_TIP = f"{EV}/EventList/progressTip.png"
PROGRESS_TIP_THRESHOLD = 0.85
PROGRESS_TIP_REGION = (0, 40, 100, 48)   # % màn hình: thanh tiến độ (y ~306)
CHEST_OPENED = f"{EV}/EventList/chestOpened.png"
CHEST_OPENED_THRESHOLD = 0.75
CHEST_FROM_TIP = (-40, -70, 70, 50)   # (dx, dy, w, h) ô tìm rương so với tâm đầu thanh
CHEST_TAP = (0, -35)                  # bấm (đầu thanh x, đầu thanh y - 35): lên rương hôm nay
CHEST_WAIT = 2   # sau khi bấm rương (mọi bước chờ 2-3 s)
# ---- Voyage to Civilizations trong danh sách event (open_voyage trong common.py) -----------
# Mỗi ngày bấm Free 1 lần (daily_done VOYAGE_KEY, tới lần reset server; không xét chấm đỏ): hôm nay
# đã bấm Free thì không vào. Chưa bấm: thấy icon Voyage (phần dưới trái icon con tàu, bỏ góc chấm đỏ: 1,00 trên mọi màn danh
# sách có Voyage, icon event khác <= 0,56) -> bấm vào -> màn Voyage to Civilizations:
# 1. Ô "Skip animation" (281, 622) chưa tích -> bấm tích.
# 2. Nút "Voyage Once" có chữ "Free" -> bấm 1 lần (mỗi ngày 1 lượt miễn phí).
# 3. Đã bấm Free -> lưu VOYAGE_KEY. Không thấy Free -> KHÔNG lưu (vẫn tính là chưa bấm, lần sau vào
#    kiểm lại). Back về danh sách event (tối đa VOYAGE_BACKS lần, tới khi thấy
#    tiêu đề danh sách). Sau khi bấm Free: popup "Congratulations" (voyage_congrats.png) -> Back 1 đóng
#    popup, về màn Voyage hết Free (voyage_no_free.png) -> Back 2 về danh sách.
VOYAGE_ICON = f"{EV}/Voyage/icon.png"
VOYAGE_THRESHOLD = 0.8
VOYAGE_KEY = "event_voyage"
# Tiêu đề "Voyage to Civilizations" (198, 23): 1,00; màn khác <= 0,39.
VOYAGE_TITLE = f"{EV}/Voyage/title.png"
# Ô Skip animation: chưa tích (skipOff) / đã tích (skipOn) 1,00, khớp chéo 0,75 -> ngưỡng 0,9.
VOYAGE_SKIP_OFF = f"{EV}/Voyage/skipOff.png"
VOYAGE_SKIP_THRESHOLD = 0.9
VOYAGE_SKIP_REGION = (60, 84, 80, 93)   # % màn hình: quanh ô (281, 622)
# Chữ "Free" dưới "Voyage Once" (287, 684): 1,00; màn khác <= 0,54. Bấm vào nút (giữa nút).
VOYAGE_FREE = f"{EV}/Voyage/free.png"
VOYAGE_FREE_REGION = (50, 92, 100, 100)
VOYAGE_ONCE_DY = -14   # bấm giữa nút "Voyage Once": chữ Free (287, 684) -> (287, 670)
VOYAGE_SCREEN_WAIT = 10   # giây chờ màn Voyage sau khi bấm icon
VOYAGE_WAIT = 3           # sau mỗi lần bấm trong màn Voyage
VOYAGE_STEP_WAIT = 2      # sau khi màn Voyage hiện / sau mỗi lần Back
VOYAGE_BACKS = 3
# Không dùng ngưỡng 1: đúng màn 1,00, màn khác <= 0,49 -> 0,8 vẫn cách xa mà chịu được sai khác nhỏ.
EVENT_LIST_TITLE_THRESHOLD = 0.8
EVENT_LIST_WAIT = 10
# Icon event Gather Troops trong danh sách: khớp 1,00 tại (50, 362); 126 màn khác <= 0,23.
GATHER_TROOPS_ICON = f"{EV}/GatherTroops/icon.png"
# Icon event King's Path (hộp quà, không lấy chấm đỏ góc trên phải) trong danh sách event:
# khớp 1,00 tại (45, 512) (tests/event/kings_path/screens/04_event_list.png); màn khác <= 0,47.
KINGS_PATH_ICON = f"{EV}/KingsPath/icon.png"
# Ngưỡng tìm icon event trong danh sách. Icon Gather Troops có chấm đỏ thông báo (còn thưởng chưa
# nhận) đè góc trên phải ảnh mẫu: chỉ còn 0,89 - 0,94 (dưới ngưỡng mặc định 0,9 -> lúc thấy lúc
# không); icon event khác / màn khác <= 0,47.
EVENT_ICON_THRESHOLD = 0.8

# Tiêu đề màn event (đầu màn, tâm (199, 23)): thấy là đang ở sẵn bảng event đó.
# "Gather Troops": 1,00 trên 20 màn Gather Troops trong tests; màn khác (cả King's Path) <= 0,50.
GATHER_TROOPS_TITLE = f"{EV}/GatherTroops/title.png"
# "King's Path": 1,00 trên mọi màn King's Path; màn khác <= 0,74 (xem kings_path/constants.py).
KINGS_PATH_TITLE = f"{EV}/KingsPath/title.png"
EVENT_TITLE_REGION = (20, 0, 80, 8)   # % màn hình: thanh tiêu đề

# ---- Tự cập nhật ảnh tiêu đề (open_event trong common.py) --------------------------------
# Không thấy tiêu đề danh sách event (VD đổi đợt lễ hội: "Wine Festival Event" -> tên khác) sau
# khi bấm nút event: vẫn cuộn tìm icon như thường, chỉ nhớ là không thấy (biến tạm, không lưu DB);
# gặp icon King's Path / Gather Troops = đúng là danh sách event -> chụp màn, cắt ô tiêu đề
# EVENT_LIST_TITLE_BOX (x, y, w, h — đúng chỗ đã cắt ảnh mẫu) ghi đè ảnh mẫu. Chỉ ghi khi ảnh cắt
# khác ảnh mẫu (điểm < TITLE_SAME) và không phải vùng trơn (độ lệch chuẩn >= TITLE_MIN_STD, VD màn
# đen lúc đang tải).
EVENT_LIST_TITLE_BOX = (60, 8, 276, 30)
REFRESH_TITLE_ICONS = (GATHER_TROOPS_ICON, KINGS_PATH_ICON)
TITLE_SAME = 0.9
TITLE_MIN_STD = 10

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
ON_EVENT_LIST = "on_event_list"   # đang ở sẵn danh sách event (thấy tiêu đề danh sách)
BACK, TAP = "back", "tap"
CLAIM = "claim_all"   # nút Claim All (đếm số lần bấm liên tiếp, xem CLAIM_ALL_MAX_TAPS)
