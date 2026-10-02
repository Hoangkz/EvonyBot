"""
constants.py — ảnh riêng của nhiệm vụ Wheel (King's Path, Day 4).
"""
from ..constants import KP

# Ô chọn ở group King's Path: {"value": mục tiêu, "day": 4}.
KEY = "kings_path_wheel"
DAY = 4   # ngày mở nhiệm vụ (dùng khi settings thiếu "day")

# Tab phụ "Fortune Wheel" (thứ 2, bên giữa), dòng nhiệm vụ "Spin the Wheel of Fortune N time(s)".
TAB = f"{KP}/Tab/fortuneWheel.png"
TAB_SELECTED = f"{KP}/Tab/fortuneWheelSelected.png"
TAB_INDEX = 1

# ---- Màn Wheel of Fortune (mở ra sau khi bấm Go) ----------------------------------------
# Ảnh cắt từ tests/event/kings_path/screens/wheel_*.png.
# Nút "100 Spins" (74, 666): 1,00; chữ "10 Spins" 0,77..0,78; màn khác <= 0,46. Chỉ có khi đủ
# chip (>= 9000). Bấm 1 lần = 100 lượt -> đủ mọi mốc (5 .. 100) -> Back là xong.
SPINS_100 = f"{KP}/Wheel/spins100.png"
# Chữ "10 Spins": (197, 666) khi có 100 Spins, (101, 666) khi không đủ chip cho 100: 0,98..1,00
# (cả khi bảng kết quả "Congratulations" đang hiện — bảng không che hàng nút).
SPINS_10 = f"{KP}/Wheel/spins10.png"
SPINS_REGION = (0, 90, 100, 100)   # % màn hình: hàng nút quay

# ---- Màn Purchase Chips -----------------------------------------------------------------
# Bấm 10 Spins khi không đủ chip -> game tự mở màn này -> Back, xong hôm nay.
# Tiêu đề "Purchase Chips" (199, 23): 1,00 (0,99 khi popup che); màn khác <= 0,49.
CHIPS_TITLE = f"{KP}/Wheel/chipsTitle.png"

WHEEL_WAIT = 10    # sau Go: chờ màn Wheel of Fortune (giây, mỗi giây chụp 1 lần)
SPIN_100_WAIT = 3  # sau khi bấm 100 Spins, trước khi Back
SPIN_10_WAIT = 1   # giữa các lần bấm 10 Spins liên tục
BUTTON_WAIT = 2    # sau các nút khác
MAX_STEPS = 300    # số bước tối đa (mỗi lần bấm 10 Spins là 1 bước)
