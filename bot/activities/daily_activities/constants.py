"""
constants.py — Daily Activities: thư mục ảnh, tên action và key daily_done dùng chung mọi nhiệm vụ.
Ảnh riêng của từng nhiệm vụ nằm trong constants.py của nhiệm vụ đó.
"""
ROOT = "DailyActivites"
USE_ALL = f"{ROOT}/UseAllActivities"

# Action chung của vòng lặp run_task (common.py). Action riêng của nhiệm vụ là chuỗi khác (VD "tax"),
# được chuyển cho handler của nhiệm vụ.
DONE, BACK, TAP, SCROLL, OPEN = "done", "back", "tap", "scroll", "open"
OPEN_MONSTER_FIRST, OPEN_MONSTER_SECOND = "open_monster_first", "open_monster_second"
VERIFY_COLLECTING, OPEN_COLLECTING_HELPER = "verify_collecting", "open_collecting_helper"
# Kết quả open_task_row.
ROW_OPENED, ROW_COMPLETE, ROW_MOVED = "opened", "complete", "moved"
# Ảnh tiêu đề dòng nhiệm vụ: find_first trả góc trên trái (dòng Go tính từ đó, như bản C#).
ROW_ANCHORS = frozenset({OPEN, OPEN_MONSTER_FIRST, OPEN_MONSTER_SECOND,
                         VERIFY_COLLECTING, OPEN_COLLECTING_HELPER,
                         "claim", "donate", "crystal", "compose"})

# ---- Mở nhiệm vụ, phiên bản giao diện MỚI (common.open_task) ---------------------------------
# Màn chính (nút "•••", 0,96) -> nút Quests góc dưới trái (0,97) -> popup Quests -> tab Activity
# (1,00) -> danh sách Activity (ngôi sao Activity, 0,99) -> cuộn tìm tiêu đề dòng nhiệm vụ -> Go của
# dòng đó. Thấy Claim All (0,99; Claim All của Chapter Quests chỉ 0,37) thì bấm trước.
# Ảnh đo trên tests/daily_activities/screens/ (396x704).
MAIN_MORE = "Server/listActivity.png"                    # nút "•••" của màn chính
QUESTS_BUTTON = f"{USE_ALL}/Click_Activities.png"        # nút Quests (cuộn giấy) góc dưới trái
QUESTS_BUTTON_REGION = (0, 70, 25, 100)                  # % màn hình
ACTIVITY_TAB = f"{USE_ALL}/Click_Activities1.png"        # chữ tab "Activity" (chọn hay chưa đều khớp)
ACTIVITY_LIST = f"{USE_ALL}/Click_ActivitiesLight.png"   # ngôi sao điểm Activity: đang ở danh sách
GO_BUTTON = f"{USE_ALL}/Go.png"
CLAIM_BUTTON = f"{ROOT}/ActivitiesSourceCollecting/Claim.png"   # dòng đã xong, chưa nhận
CLAIM_ALL = f"{ROOT}/CollectionActivities/Claim_All.png"
# Ảnh tiêu đề dòng cắt từ danh sách thật (396x704) trong thư mục ảnh của nhiệm vụ: chỉ phần chữ cố
# định, bỏ số lượng / "for N time(s)" (khác theo tài khoản, lần). Dòng đúng 1,00; dòng khác <= 0,78.
# Resource Gathering = dòng "Gather ... resources from resource fields in the City" (thu mỏ trong thành).
ROW_TITLE = "Title.png"
# Nút Go / Claim nằm dưới tâm tiêu đề dòng ROW_BUTTON_DY px (Offer 434 -> 475, Tax 526 -> 568,
# Research 356 -> Claim 399), lệch tối đa ROW_BUTTON_TOLERANCE.
ROW_BUTTON_DY = 42
ROW_BUTTON_TOLERANCE = 10
# Nút của dòng phải nằm trên thanh Claim All (y ~638, che nút Go của dòng sát đáy, VD Levy tiêu đề
# y 621): tiêu đề thấp hơn ROW_TITLE_MAX_Y thì coi như chưa thấy, cuộn tiếp (LIST_SWIPE ~105 px) để
# cả dòng lên trên thanh.
ROW_TITLE_MAX_Y = 580
LIST_SWIPE = (70, 70, 55, 55)        # % màn hình: ngón tay kéo lên = cuộn danh sách xuống
LIST_MAX_SCROLLS = 12
# Lướt hết danh sách không thấy nhiệm vụ: Back (đóng bảng Activity) rồi mở lại từ đầu, tìm thêm
# LIST_RETRIES lần (lần cuộn trước có thể trượt qua dòng) rồi mới coi là không có (TASK_NOT_FOUND).
LIST_RETRIES = 2
# Bảng Activity đã mở sẵn (có thể đang ở giữa danh sách): Back rồi mở lại từ đầu. Không bao giờ cuộn lên.
LIST_END_SAME = 0.99                 # vùng danh sách trước / sau khi cuộn giống cỡ này = hết danh sách
OPEN_ACTIVITY_TRIES = 8
# ---- Mở nhiệm vụ, phiên bản giao diện CŨ (common.open_task) -----------------------------------
# Màn chính không có nút Quests góc dưới trái -> bấm "•••" -> bảng chức năng -> "Activity" (0,91; màn
# khác <= 0,74) -> màn "Activity" (tiêu đề 1,00; màn khác <= 0,36): lưới thẻ nhiệm vụ 3 cột -> lướt
# tìm thẻ của nhiệm vụ (<thư mục ảnh>/Card.png: icon thẻ, 1,00; thẻ khác <= 0,49) -> bấm thẻ -> popup
# -> Go (0,99; màn khác <= 0,65). Sau Go hai phiên bản giống nhau.
OLD_MENU_ACTIVITY = "Black Market/activites.png"
OLD_MENU_THRESHOLD = 0.85
OLD_ACTIVITY_TITLE = "Black Market/DaiLyActivites.png"
OLD_CARD = "Card.png"                       # tên ảnh thẻ trong thư mục ảnh của nhiệm vụ
OLD_CARD_THRESHOLD = 0.85
OLD_POPUP_GO = "Black Market/goto.png"
OLD_POPUP_WAIT = 2                          # giây chờ popup sau khi bấm thẻ
OLD_POPUP_TIMEOUT = 4                       # giây chờ tối đa nút Go của popup
# Thẻ nhiệm vụ đã đủ 100%: icon đổi thành hộp quà (có hiệu ứng, không dùng làm ảnh mẫu) -> nhận ra bằng
# chữ "100%" ở góc trên trái thẻ (OLD_DONE_BADGE: 1,00; thẻ "0%" / màn khác <= 0,68) rồi bấm giữa thẻ
# (OLD_DONE_TAP: lệch so với tâm chữ "100%" (30, 272) -> tâm thẻ (75, 325)) để nhận, như Claim All của bản
# mới. Bấm mà thẻ vẫn "100%" ở đúng chỗ (lỗi game) -> bỏ qua tới hết lượt này. Thẻ chưa nhận chỉ nằm ở
# đầu lưới: chỉ bấm khi chưa cuộn; đã cuộn mà thấy "100%" là thẻ đã nhận rồi -> bỏ qua.
OLD_DONE_BADGE = f"{USE_ALL}/Old100.png"
OLD_DONE_THRESHOLD = 0.85
OLD_DONE_TAP = (45, 53)
OLD_DONE_WAIT = 2
# Bấm nhận thẻ "100%" -> popup "Congratulations!" (danh sách phần thưởng) che lưới, không tự tắt, bấm vào
# không đóng -> Back đóng (vẫn ở lưới). Chữ "Congratulations!" 0,999; màn khác <= 0,43.
OLD_CONGRATS = f"{ROOT}/CollectionActivities/CongratulationsCurrent.png"
# Thẻ đã nhận thưởng: chuyển xuống cuối lưới, icon cũ có dấu tích xanh + chữ "Completed". Mỗi nhiệm vụ một ảnh
# <thư mục ảnh>/Done.png (icon + tích, cắt cùng chỗ với Card.png): thấy -> nhiệm vụ xong hôm nay, không bấm thẻ.
# Đo trên tests/daily_activities/screens/23..30: thẻ đã xong của chính nhiệm vụ 0,89..1,00 (khác cột / bị header
# che một chút còn 0,89); cùng thẻ chưa nhận <= 0,77; Done của nhiệm vụ khác <= 0,53 -> ngưỡng 0,85.
OLD_DONE_CARD = "Done.png"
OLD_DONE_CARD_THRESHOLD = 0.85
# Kết quả open_task.
TASK_OPENED, TASK_DONE, TASK_NOT_FOUND, TASK_NO_LIST = "opened", "done", "not_found", "no_list"
# Thấy tiêu đề dòng mà không nhận ra nút nào (không Go / Claim / tích V): không đoán là xong.
TASK_UNKNOWN = "unknown"
# open_task(tap_go=False): dòng / popup còn Go (nhiệm vụ chưa xong) nhưng không bấm (chỉ kiểm tra).
TASK_HAS_GO = "has_go"
# Dấu tích V của dòng đã nhận thưởng (cắt từ danh sách Activity máy 21913, dòng Tax / Levy / Offer đã xong): khớp
# 1,00; tích V ở tab Chapter Quests 0,96 (chỉ tìm ngay dưới tiêu đề dòng nên không nhầm). Tích nằm dưới tâm tiêu đề
# TICK_DY px (đo 32 .. 33), không phải ROW_BUTTON_DY như Go / Claim.
TICK_BUTTON = f"{USE_ALL}/Tick.png"
TICK_DY = 33

REWARDS = "Activity Rewards"   # key trong daily_done cho bước nhận thưởng cuối
REWARDS_KEY = "daily_rewards"   # key của bước nhận thưởng cuối trong bot/worker/priority.json
GENERAL = "General"
BUY_STAMINA = "General: Buy Stamina"
BUY_HAMMERS = "General: Buy All Hammers"
