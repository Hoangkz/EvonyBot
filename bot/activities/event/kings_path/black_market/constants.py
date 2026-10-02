"""
constants.py — ảnh riêng của nhiệm vụ Black Market (King's Path, Day 5).
"""
from ..constants import KP

# Ô chọn ở group King's Path: {"value": mục tiêu, "day": 5}.
KEY = "kings_path_black_market"
DAY = 5   # ngày mở nhiệm vụ (dùng khi settings thiếu "day")

# Tab phụ "Market Trade" (thứ 1, bên trái), dòng nhiệm vụ "Buy items from the Black Market for
# N time(s)". Đang chọn (day5_market_trade.png) / chưa chọn (day5_war_horn.png): 1,00, khớp chéo
# 0,90 -> ngưỡng 0,95; màn khác <= 0,57.
TAB = f"{KP}/Tab/marketTrade.png"
TAB_SELECTED = f"{KP}/Tab/marketTradeSelected.png"
TAB_INDEX = 0

# ---- Sau khi bấm Go (ảnh tests/event/kings_path/screens/bm_*.png) -------------------------
# Go -> về thành, Chợ ở giữa -> bấm giữa -> menu Chợ (../building.py) -> icon "Black Market"
# (111, 254): 1,00 (cũng khớp menu Chợ ở tax_menu.png — cùng menu).
MENU_BLACK_MARKET = f"{KP}/BlackMarket/menuBlackMarket.png"
# Tiêu đề "Black Market" (199, 23): 1,00; màn khác <= 0,44. Các ảnh dưới chỉ xét khi thấy tiêu đề.
TITLE = f"{KP}/BlackMarket/title.png"
# 6 món: tâm nút giá (dưới mỗi món). Còn mua được = nút xanh: trung bình (G - R) trong ô 80x16
# quanh tâm 24..34; đã mua (xám, "Rebuy unlocks at VIP13") -29,8 -> ngưỡng SLOT_GREEN.
SLOTS = [(82, 368), (198, 368), (314, 368), (82, 521), (198, 521), (314, 521)]
SLOT_GREEN = 10
SLOT_HALF = (40, 8)
# Icon kim cương trên nút giá (món trả bằng kim cương; vị trí xê dịch theo độ dài số): trên 5 ảnh
# bm_*.png ô trả kim cương 0,85..1,00, ô khác <= 0,53 -> ngưỡng 0,7; bỏ qua món đó.
GEM = f"{KP}/BlackMarket/gem.png"
GEM_THRESHOLD = 0.7
# Hộp "Are you sure you want to purchase ...?" -> "Confirm" (198, 414): 1,00. Chỉ bấm khi vừa bấm
# một món (khớp cả popup khác 0,96).
CONFIRM = f"{KP}/BlackMarket/confirm.png"
# "Instant Refresh" (199, 584): mua hết các món (mỗi món 1 lần) thì bấm -> 6 món mới (xác nhận
# bằng ITEM_BOX bên dưới), mua tiếp cho tới khi đủ. Hết lượt miễn phí thì refresh bằng kim cương (nút ghi
# "Instant Refresh 50", bm_refresh_gems.png) như bình thường; hiện hộp xác nhận thì cũng Confirm.
INSTANT_REFRESH = f"{KP}/BlackMarket/instantRefresh.png"
# Xác nhận Refresh đã ra hàng mới: trước khi bấm, cắt ô vật phẩm 1 (hình món + nút giá, ITEM_BOX);
# bấm -> chờ REFRESH_FIRST_CHECK giây -> so lại: cùng món 1,00 / món khác <= 0,75 (9 mẫu bm_*.png)
# -> còn giống (>= SAME_ITEM) thì chờ thêm 1 s, tối đa REFRESH_CHECKS lần; vẫn giống thì bấm Refresh
# lại (tối đa REFRESH_TRIES lần bấm, quá thì dừng).
ITEM_BOX = (34, 250, 96, 130)   # (x, y, w, h)
SAME_ITEM = 0.95
REFRESH_FIRST_CHECK = 2
REFRESH_CHECKS = 10
REFRESH_TRIES = 3
BUY_WAIT = 2
MAX_STEPS = 300   # mục tiêu tới 100 lần mua: mỗi lần mua 2 bước + refresh
