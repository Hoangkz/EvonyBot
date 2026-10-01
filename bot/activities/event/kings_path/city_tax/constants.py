"""
constants.py — ảnh riêng của nhiệm vụ City Tax (King's Path, Day 1).
"""
from ..constants import KP

# Ô chọn ở group King's Path: {"value": mục tiêu, "day": 1}.
KEY = "kings_path_city_tax"
DAY = 1   # ngày mở nhiệm vụ (dùng khi settings thiếu "day")

# Tab phụ "City Tax" (thứ 1, bên trái), dòng nhiệm vụ "Tax on resources for N time(s)".
# Chưa có ảnh tab chưa chọn: bấm theo vị trí (TAB_INDEX) khi Day 1 đang chọn.
TAB = None
TAB_SELECTED = f"{KP}/Tab/cityTaxSelected.png"
TAB_INDEX = 0
