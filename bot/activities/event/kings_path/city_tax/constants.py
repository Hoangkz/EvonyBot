"""
constants.py — ảnh riêng của nhiệm vụ City Tax (King's Path, Day 1).
"""
from ..constants import KP

# Ô chọn ở group King's Path: {"value": mục tiêu, "day": 1}.
KEY = "kings_path_city_tax"
DAY = 1   # ngày mở nhiệm vụ (dùng khi settings thiếu "day")

# Tab phụ "City Tax" (thứ 1, bên trái), dòng nhiệm vụ "Tax on resources for N time(s)".
# Chưa chọn (day1_hoarding.png) / đang chọn khớp chéo 0,90 -> ngưỡng 0,95.
TAB = f"{KP}/Tab/cityTax.png"
TAB_SELECTED = f"{KP}/Tab/cityTaxSelected.png"
TAB_INDEX = 0

# ---- Sau khi bấm Go -----------------------------------------------------------------
# Go -> về thành, Chợ (Market) ở giữa màn hình -> bấm giữa -> menu Chợ (../building.py).
# Icon "Tax" trong menu Chợ (221, 193): 0,97 (ảnh của Daily Activities / Resource Tax).
TAX_MENU = "DailyActivites/ActivitiesTaxResource/Tax.png"

# ---- Màn Tax ------------------------------------------------------------------------
# Dòng chữ "Please select a type of resources to tax on..." (181, 211): 1,00; khi popup che
# 0,68 -> dấu hiệu đang ở màn Tax (ảnh của Daily Activities).
TAX_SCREEN = "DailyActivites/ActivitiesTaxResource/TaxRevenue.png"
# Nút "Tax" xanh của 4 dòng tài nguyên (Food / Wood / Stone / Iron), x 308, y 284 / 383 / 482
# / 581: 1,00; màn khác <= 0,64. Cũng khớp 0,99 nút Tax to trong popup -> xét popup trước.
ROW_TAX = f"{KP}/Tax/rowTax.png"
TAX_ROWS = 4

# ---- Popup Tax (chọn số lần) ---------------------------------------------------------
# Chữ "Cost" trong popup (192, 381): 0,99 (ảnh của Daily Activities). Ô số và nút Tax tính
# lệch từ chữ này: ô số (198, 300), nút Tax (198, 438). Số lần vượt lượt miễn phí thì tiêu
# kim cương (người chơi cho phép).
POPUP = "DailyActivites/ActivitiesTaxResource/TapTax1.png"
POPUP_INPUT_OFFSET = (6, -81)
# Bấm ô số -> thanh nhập ở đáy màn (đang chứa số cũ, tax_input.png): xoá hết, gõ số mới, rồi bấm
# vào màn hình (không bấm OK) cho thanh nhập mất: chỗ trống trong popup bên trái ô số (62, 300),
# lệch POPUP_BLANK_OFFSET so với chữ "Cost" — nền trơn, không trúng nút.
POPUP_BLANK_OFFSET = (-130, -81)
# Nút "Tax" to trong popup (198, 438): 1,00; màn khác <= 0,61.
POPUP_TAX = f"{KP}/Tax/popupTax.png"
INPUT_DELETES = 5   # xoá số cũ trong ô (VD "8"; tối đa 5 chữ số) trước khi gõ số mới
SCREEN_WAIT = 10    # chờ popup Tax hiện (giây)
TAX_WAIT = 3        # sau khi bấm Tax trong popup: chờ về màn Tax
