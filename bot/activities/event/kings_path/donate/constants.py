"""
constants.py — ảnh riêng của nhiệm vụ Donate (King's Path, Day 2).
"""
from ..constants import KP

# Ô chọn ở group King's Path: {"value": mục tiêu, "day": 2}.
KEY = "kings_path_donate"
DAY = 2   # ngày mở nhiệm vụ (dùng khi settings thiếu "day")

# Tab phụ "Teamwork" (thứ 3, bên phải), dòng nhiệm vụ "Donate to the Alliance N time(s)".
TAB = f"{KP}/Tab/teamwork.png"
TAB_SELECTED = f"{KP}/Tab/teamworkSelected.png"
TAB_INDEX = 2

# Tab phụ có cả Patrol và Donate: tìm dòng theo chữ "Donate to the Alliance" đầu tiêu đề.
ROW_TITLE = f"{KP}/Title/donate.png"

# ---- Màn Alliance Science (mở ra sau khi bấm Go) ---------------------------------------
# Mỗi lần bấm "Donate" = 1 lần donate. Hết lượt miễn phí (Remaining Donations 0/13) thì nút
# đổi thành nút kim cương ("448") -> bấm -> hộp "Spend N Gems on clearing the Cooldown?" ->
# "Okay" -> có lại 13 lượt. Ảnh cắt từ tests/event/kings_path/screens/donate_*.png.
# Tiêu đề "Alliance Science" (198, 23): 1,00 (0,99 khi có hộp xác nhận); màn khác <= 0,64.
SCIENCE_TITLE = f"{KP}/Donate/title.png"
# Chữ "Donate" trên nút xanh của thẻ khoa học trên cùng (317, 361): 1,00; màn khác <= 0,64.
DONATE_BUTTON = f"{KP}/Donate/donate.png"
# Mép trái nút kim cương + icon (không lấy số vì giá đổi theo lần mua) (294, 361): 1,00;
# khi hộp xác nhận che 0,72. Màn khác tới 0,91 (nút kim cương ở màn Bubble) -> chỉ xét khi
# thấy SCIENCE_TITLE.
GEMS_BUTTON = f"{KP}/Donate/gems.png"
# Chữ "Okay" trong hộp xác nhận tiêu kim cương (199, 387): 1,00; màn khác <= 0,50.
OKAY = f"{KP}/Donate/okay.png"

# Mua lại lượt tối đa 5 lần mỗi lượt chạy: lần vào đầu đã hết lượt miễn phí -> 5 x 13 = 65 >= 60
# (mốc cao nhất "Donate to the Alliance 60 time(s)"). Còn lượt miễn phí thì donate đủ (mục tiêu -
# số đã làm, OCR ở dòng Go) là dừng nên chỉ mua đúng số lần cần (VD 13 miễn phí + 4 lần mua).
MAX_GEM_BUYS = 5
SCIENCE_WAIT = 10   # sau Go: chờ màn Alliance Science (giây)
DONATE_WAIT = 1     # sau mỗi lần bấm Donate
GEMS_WAIT = 2       # sau khi bấm nút kim cương / Okay
MAX_MISSES = 5      # số lần chụp liên tiếp không nhận ra màn nào -> bỏ, lượt sau làm tiếp

# ---- Không làm Patrol: donate qua Liên minh (alliance.py) --------------------------------
# Ô Patrol ở tab Event = 0 (không tích) -> Donate không vào King's Path: màn chính -> Liên minh
# -> cuộn xuống -> Alliance Science -> donate thẻ khoa học đầu tiên (như activity Alliance
# Capacity, dùng lại ảnh của nó). Không có dòng Go để đọc tiến độ -> tự lưu số lần đã donate hôm
# nay vào daily_done `<KEY>_alliance_<n>` (n = 1, 2, ...): bị ngắt thì lượt sau donate tiếp phần
# còn thiếu.
PATROL_KEY = "kings_path_patrol"   # ô Patrol trong settings tab Event
EVENT_TAB = "Event"                # tên tab trong bot.settings
# Đo trên tests/event/kings_path/screens/alliance_*.png:
ALLIANCE_BUTTON = "JoinBoss/lienminh.png"         # nút Liên minh ở màn chính (361, 558): 0,93
ALLIANCE_SCROLL = "JoinBoss/chientranh.png"       # dòng Alliance War (42, 396): 0,97 -> cuộn xuống
ALLIANCE_SCIENCE = "Science/scienceclick.png"     # dòng Alliance Science: 0,99 sau khi cuộn (49, 498);
                                                  # bị che ở đáy trước khi cuộn: 0,86 (không bấm)
OUT_ALLIANCE = "JoinBoss/outLM.png"               # popup ngoài liên minh (bấm lệch +40, +40 rồi Back)
NAV_MAX_STEPS = 30
