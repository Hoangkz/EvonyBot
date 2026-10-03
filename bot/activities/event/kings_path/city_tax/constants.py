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
# Hết lượt miễn phí ("Reset Countdown" thay "Free: N"): nút dòng thành "💎 2" (tax_congrats_gems.png;
# rowTax chỉ 0,53) -> không thấy đủ nút "Tax" thì tìm hình kim cương trên nút (chỉ hình, không lấy số
# giá vì giá có thể đổi): dòng không bị che 1,00, bị băng quà che một phần 0,86; màn Tax còn lượt
# miễn phí <= 0,64. Kim cương có ở nhiều màn khác (Donate 0,98...) -> chỉ tìm trong cột nút
# ROW_BUTTON_REGION (% màn hình) và chỉ khi đang ở màn Tax.
ROW_TAX_GEMS = f"{KP}/Tax/rowTaxGems.png"
ROW_TAX_GEMS_THRESHOLD = 0.85
ROW_BUTTON_REGION = (64, 30, 93, 90)
TAX_ROWS = 4
ROW_NAMES = ("Food", "Wood", "Stone", "Iron")   # tên trong log, theo dòng trên -> dưới

# ---- Popup Tax (chọn số lần) ---------------------------------------------------------
# Chữ "Cost" trong popup (192, 381): 0,99 (ảnh của Daily Activities). Ô số và nút Tax tính
# lệch từ chữ này: ô số (198, 300), nút Tax (198, 438). Số lần vượt lượt miễn phí thì tiêu
# kim cương (người chơi cho phép).
POPUP = "DailyActivites/ActivitiesTaxResource/TapTax1.png"
# Chọn số lần bằng nút "−" (71, 345) / "+" (324, 345) (lệch so với chữ "Cost"), không gõ số: ô số
# mặc định là số lượt miễn phí còn lại (tax_popup.png "Free: 11" -> 11) nên không biết trước ->
# bấm "−" tới khi ô số (198, 300; COUNT_BOX lệch so với "Cost") không đổi nữa (= nhỏ nhất, luôn là 1 — game không cho < 1;
# tối đa MINUS_MAX_TAPS lần), rồi bấm "+" (số lần - 1) lần.
MINUS_OFFSET = (-121, -36)
PLUS_OFFSET = (132, -36)
COUNT_BOX = (-49, -94, 110, 28)   # (dx, dy, w, h)
SAME_COUNT = 0.99    # ảnh ô số trước / sau khi bấm "−" khớp >= SAME_COUNT -> không đổi
# Game cập nhật ô số chậm: chụp ngay sau 1 lần bấm có khi còn số cũ (VD 8 -> dừng nhầm ở 3) -> chỉ
# coi là nhỏ nhất khi ô số đứng yên SAME_STREAK lần bấm "−" liên tiếp (bấm thừa ở 1 không sao).
SAME_STREAK = 3
MINUS_MAX_TAPS = 60
STEP_WAIT = 0.3      # sau mỗi lần bấm "−" / "+" (giữ nhanh)
TAX_STEP_WAIT = 2    # chờ thêm sau mọi bước khác trong màn Tax (bấm dòng, popup hiện, Tax, về màn Tax)
# Nút "Tax" to trong popup (198, 438): 1,00; màn khác <= 0,61.
POPUP_TAX = f"{KP}/Tax/popupTax.png"
# Nút "+" của popup (324, 345; PLUS_OFFSET so với chữ "Cost"): 1,00 khi popup mở; màn Tax đã đóng
# popup 0,58 (màn Train cũng có "+" 0,98 -> chỉ tìm trong ô PLUS_HALF quanh vị trí nút). Bấm Tax
# trong popup xong: không thấy "+" = popup đã đóng; còn thấy thì kiểm tra lại CLOSE_CHECKS lần, mỗi
# lần chờ 1 s; vẫn còn -> Back CLOSE_BACKS lần, không lưu done, đi lại từ đầu (AGAIN).
POPUP_PLUS = f"{KP}/Tax/popupPlus.png"
# Thu xong có khi hiện băng "Congratulations! Taxing Gift" che dòng 2 (tax_congrats_gems.png):
# nhận ra bằng icon hộp quà đỏ (41, 370): 1,00; màn khác <= 0,57 -> bấm CONGRATS_TAP (% màn hình).
TAXING_GIFT = f"{KP}/Tax/taxingGift.png"
CONGRATS_TAP = (50, 95)
# Thu quá lượt miễn phí: hộp "Are you sure you want to spend N Gems on taxing resources?" -> bấm
# "Okay" (197, 414; tax_confirm_gems.png): 1,00; hộp kim cương của Donate 0,88; màn khác <= 0,59.
# Hộp làm tối nút "+" của popup (0,36) -> phải xét Okay trước khi coi popup đã đóng.
OKAY = f"{KP}/Tax/okay.png"
PLUS_HALF = 25
CLOSE_CHECKS = 10
CLOSE_BACKS = 2
SCREEN_WAIT = 10    # chờ popup Tax hiện (giây)
TAX_WAIT = 3        # sau khi bấm Tax trong popup: chờ về màn Tax
