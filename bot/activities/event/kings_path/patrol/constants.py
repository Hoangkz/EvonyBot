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
