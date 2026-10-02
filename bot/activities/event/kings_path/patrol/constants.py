"""
constants.py — ảnh riêng của nhiệm vụ Patrol (King's Path, Day 2).
"""
from ..constants import KP

# Ô chọn ở group King's Path: {"value": mục tiêu, "day": 2}.
KEY = "kings_path_patrol"
DAY = 2   # ngày mở nhiệm vụ (dùng khi settings thiếu "day")

# Tab phụ "Teamwork" (thứ 3, bên phải), dòng nhiệm vụ "Patrol for N time(s)".
TAB = f"{KP}/Tab/teamwork.png"
TAB_SELECTED = f"{KP}/Tab/teamworkSelected.png"
TAB_INDEX = 2

# Tab phụ có cả Patrol và Donate: tìm dòng theo chữ "Patrol for" đầu tiêu đề.
ROW_TITLE = f"{KP}/Title/patrol.png"

# ---- Sau khi bấm Go (ảnh tests/event/kings_path/screens/patrol_*.png) -------------------
# Go -> về thành, Tường thành (Walls) ở giữa -> bấm giữa -> menu (../building.py).
# Icon "Patrol" trong menu Tường thành (249, 241): 1,00; màn khác <= 0,51.
MENU_PATROL = f"{KP}/Patrol/menuPatrol.png"
# Tiêu đề "Patrol" màn Patrol (198, 23): 1,00; màn khác <= 0,74.
PATROL_TITLE = f"{KP}/Patrol/title.png"
# Ô "Select All" (200, 606): chưa tích / đã tích khớp chéo 0,87 -> ngưỡng 0,95.
SELECT_ALL_OFF = f"{KP}/Patrol/selectAllOff.png"
SELECT_ALL_ON = f"{KP}/Patrol/selectAllOn.png"
SELECT_ALL_THRESHOLD = 0.95
# Chỉ ô tích (bên trái ảnh, tâm cách góc trên-trái ảnh ~ (12, 12)) bấm được; bấm vào chữ
# "Select All" (tâm ảnh) không có tác dụng. Bấm SELECT_ALL_TRIES lần vẫn chưa tích -> dừng.
SELECT_ALL_BOX = (12, 12)
SELECT_ALL_TRIES = 3
# Nút "Patrol" (287, 660; tích hết thì tốn kim cương, VD 300) và "Refresh" (107, 660; 1000 vàng,
# ra bộ phần thưởng mới để patrol lượt tiếp): 1,00; màn khác <= 0,52.
PATROL_BUTTON = f"{KP}/Patrol/patrolButton.png"
REFRESH_BUTTON = f"{KP}/Patrol/refresh.png"
# Hết lượt Refresh (Refreshes Today 10/10, patrol_no_refresh.png): nút Refresh chuyển xám. Ảnh
# xám / xanh khớp chéo 0,90 nên phân biệt bằng màu: trung bình (G - R) trong REFRESH_BOX = 43,8
# khi bấm được / -0,1 khi xám -> ngưỡng REFRESH_GREEN.
REFRESH_BOX = (30, 648, 156, 42)   # (x, y, w, h)
REFRESH_GREEN = 20
# Đã patrol = mỗi phần thưởng có dấu tích lớn. Đếm KHỐI xanh lá (G > 150, R < 150, B < 90) trong
# khung phần thưởng ITEMS_BOX (không đếm tổng điểm ảnh: hình phần thưởng xanh lá dễ làm lệch):
# sau patrol 10 khối 26..35 px (patrol_done / patrol_no_refresh); chỉ tích ô nhỏ ở góc: khối lớn
# nhất 10 px (patrol_selected); chưa tích: 0 -> đã patrol khi có >= BIG_TICKS khối >= BIG_TICK_AREA px.
ITEMS_BOX = (36, 445, 334, 140)   # (x, y, w, h)
BIG_TICK_AREA = 20
BIG_TICKS = 6
# Bấm Patrol -> chỉ tính lượt khi màn chuyển sang "đã patrol" trong PATROL_CONFIRM_WAIT giây (chụp
# mỗi 1 s). Không chuyển (game chậm, popup thiếu kim cương...) -> không tính, dừng.
PATROL_CONFIRM_WAIT = 8

# Mỗi lượt patrol tích hết 10 phần thưởng = +10 tiến độ nhiệm vụ. Một ngày patrol tối đa 10 lượt
# (= 100 tiến độ; nhiệm vụ cần 200 -> 2 ngày). Số lượt trong ngày lưu daily_done
# `<KEY>_round_<n>` (mất khi reset server) -> bị ngắt giữa chừng vẫn đếm đúng.
PER_ROUND = 10
ROUNDS_PER_DAY = 10
BUTTON_WAIT = 3
MAX_STEPS = 60
