"""
constants.py — Viking Summon: ảnh, toạ độ, giới hạn, tên action.

Toạ độ đo trên màn 396x704 (tests/event_center/viking_summon/screens). Ảnh nằm ở Images/EventCenter/Viking.
"""
from ..constants import EC

FOLDER = f"{EC}/Viking"

# Icon dòng "Viking Challenge" trong tab Activities: khớp 1,00; dòng khác <= 0,52 -> 0,8.
ICON = f"{FOLDER}/icon.png"
ICON_THRESHOLD = 0.8
# Tiêu đề "Viking Challenge" (mọi màn của event, kể cả khi popup mờ phủ lên: 0,99+); màn khác thấp hơn nhiều.
TITLE = f"{FOLDER}/title.png"
TITLE_REGION = (20, 0, 80, 8)   # % màn hình

# ---- Chọn độ khó (chỉ hiện MỘT lần cho cả sự kiện) ------------------------------------------------------------
# Màn chọn: chữ "Select Difficulty Level:" (1,00; màn khác <= 0,36). Đã chọn rồi thì các lần sau vào thẳng màn
# Summon (không còn màn này) và KHÔNG đổi được nữa; sang event kế tiếp mới chọn lại.
SELECT_DIFFICULTY = f"{FOLDER}/selectDifficulty.png"
# Bốn huy hiệu xếp ngang, tên độ khó nằm ngay dưới huy hiệu (chữ không đổi khi chọn / không chọn; màn nào cũng thấy đủ bốn):
# tìm tên bằng ảnh rồi bấm vào huy hiệu cao hơn tên BADGE_ABOVE px (đo: tên y 427, huy hiệu bấm được ở y 385).
LEVELS = ("Easy", "Normal", "Hard", "Hell")
LEVEL_NAME = {level: f"{FOLDER}/level_{level.lower()}.png" for level in LEVELS}
LEVEL_NAME_REGION = (5, 55, 95, 65)   # % màn hình
BADGE_ABOVE = 42
DEFAULT_LEVEL = "Hard"
# Nút Confirm dưới màn chọn (1,00; popup mờ phủ lên 0,99).
CONFIRM = f"{FOLDER}/confirm.png"
CONFIRM_REGION = (20, 85, 80, 95)   # % màn hình
# Bấm Confirm -> hộp thoại giữa màn "Once the difficulty level is selected, it cannot be changed for this event.
# Select <Level> level?" (Cancel / Confirm). Dòng đầu 1,00, màn khác <= 0,29.
POPUP_TEXT = f"{FOLDER}/popupText.png"
POPUP_CONFIRM = f"{FOLDER}/popupConfirm.png"   # nút Confirm giống nút Confirm của màn chọn (0,79): chỉ tìm khi đã thấy POPUP_TEXT
POPUP_CANCEL = f"{FOLDER}/popupCancel.png"
POPUP_REGION = (0, 40, 100, 70)   # % màn hình: hộp thoại ở giữa màn
# Chữ "Select <Level> level?" trong hộp thoại: để biết độ khó đang được hỏi có đúng yêu cầu không. Mỗi ảnh 1,00 trên
# hộp thoại của nó; hộp thoại của độ khó khác <= 0,82 -> 0,92.
POPUP_LEVEL = {level: f"{FOLDER}/select_{level.lower()}.png" for level in LEVELS}
POPUP_LEVEL_THRESHOLD = 0.92
# Chờ một thứ hiện ra: mỗi lần 1 giây, tối đa WAIT_TRIES lần; không ra mới làm lại bước trước.
WAIT_SECONDS = 1
WAIT_TRIES = 5
# Bấm Summon / Go xong game về bản đồ thế giới khá lâu: chờ rời màn Viking mỗi lần 1 giây, tối đa MAP_WAIT_TRIES lần.
MAP_WAIT_TRIES = 10
# Số lần chọn độ khó (bấm huy hiệu -> Confirm -> hộp thoại đúng độ khó) thử lại trước khi bỏ cuộc.
SELECT_TRIES = 3
# Xác nhận độ khó xong hiện "Congratulations!" (nhận Viking Poleaxe) che nửa trên màn; bấm vào chính nó để đóng, vẫn còn thì BACK.
CONGRATULATIONS = f"{FOLDER}/congratulations.png"

# ---- Summon ---------------------------------------------------------------------------------------------------
# Màn Summon: nhãn "Summoning Cost:" (1,00; màn khác <= 0,56) và nút Summon (1,00; màn khác <= 0,35). Nút Summon cũng
# khớp 1,00 khi popup Congratulations phủ lên -> xét Congratulations trước.
SUMMON_COST = f"{FOLDER}/summonCost.png"
SUMMON = f"{FOLDER}/summon.png"
SUMMON_REGION = (40, 55, 90, 70)   # % màn hình: nút Summon
# Boss của mình chưa bị hạ thì nút Summon được thay bằng nút "Go" (đi tới boss; 10_live_end.png): không Summon, không bấm Go (boss đã
# được chia sẻ lúc Summon), chờ lượt sau. Go: 1,00 trên màn của nó; màn Summon 0,3.
GO = f"{FOLDER}/go.png"
# Nhãn độ khó đã chọn ở đầu màn Summon (mới chụp được "Easy": 1,00 trên màn Summon).
LEVEL_LABEL = {"Easy": f"{FOLDER}/easyLabel.png"}
LEVEL_LABEL_REGION = (55, 42, 75, 48)

# Số màn hình tối đa một lượt ở màn Viking.
MAX_STEPS = 15

# ---- Cửa sổ sự kiện và lịch ----------------------------------------------------------------------------------
# Summon chỉ dùng được từ giờ reset (mặc định 14:00) thứ 2 tới giờ reset thứ 5 (3 ngày).
WINDOW_START_WEEKDAY = 0   # thứ 2
WINDOW_DAYS = 3
# Chạy lại mỗi INTERVAL_MINUTES phút trong cửa sổ (boss bị hạ thì nút Summon hiện ngay).
INTERVAL_MINUTES = 10
TRIED_KEY = "viking_summon_tried"    # daily_done: lúc thử gần nhất
ERROR_KEY = "viking_summon"          # save_errors

# ---- Sau Summon ----------------------------------------------------------------------------------------------
# Bấm Summon xong game về bản đồ thế giới, camera dừng ở boss Viking vừa gọi (boss ở giữa màn, nhãn "1 Viking" + "Remaining
# Time:" ngay dưới chân). Tìm chữ "Viking" của nhãn bằng ảnh (1,00 trên 3 khung hình bản đồ; màn event <= 0,53); trên bản đồ
# có thể có Viking của người khác -> lấy cái gần giữa màn hình nhất. Chia sẻ bằng run._share_boss (bấm nhãn -> Share ->
# liên minh -> Confirm; không đọc toạ độ).
# Hình boss Viking (cắt nửa trái của sprite, tránh nhãn boss khác đè lên): sprite có hoạt ảnh nên 0,83..1,00 trên các khung hình
# (0,90 khi đang chạy animation); màn event / bản đồ không có Viking <= 0,35 -> 0,75.
BOSS_ICON = f"{FOLDER}/bossIcon.png"
BOSS_ICON_THRESHOLD = 0.75
BOSS_NAME = f"{FOLDER}/bossName.png"
BOSS_NAME_THRESHOLD = 0.85
BOSS_NAME_TRIES = 3   # tìm nhãn: mỗi lần 1 giây (bản đồ còn đang tải sau Summon); không thấy cả 3 lần thì bấm giữa màn hình (boss ở giữa)
VIKING_NAME = "Viking"

# ---- Actions -----------------------------------------------------------
ON_VIKING = "on_viking"
DONE = "done"
