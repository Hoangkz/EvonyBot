"""
constants.py — ảnh, ngưỡng và action dùng chung cho các nhiệm vụ King's Path.
Ảnh riêng (tab phụ, tiêu đề dòng) nằm trong constants.py của từng nhiệm vụ.

Ảnh cắt từ tests/event/kings_path/screens/ (màn 396x704).
"""
from ..constants import EV, EVENT_TITLE_REGION, KINGS_PATH_TITLE

KP = f"{EV}/KingsPath"

# ---- Màn King's Path ---------------------------------------------------------------
# Chữ "King's Path" trên thanh tiêu đề, tâm (198, 23). Hàng tab Day giống hệt Gather Troops
# (khớp chéo 1,00) nên phải thấy tiêu đề này mới coi là đang ở màn King's Path.
TITLE = KINGS_PATH_TITLE
TITLE_REGION = EVENT_TITLE_REGION

# Chữ "Day N" trên hàng tab (y ~209; tâm x: Day 1 45, Day 2 120, Day 3 196, Day 4 271).
# Chưa chọn / đang chọn khớp chéo 0,90 -> ngưỡng 0,95. Day 5 (x 347): chưa chọn / đang chọn chéo
# 0,91; chữ "Day 5" lúc khoá giống lúc mở (0,94) — không sao: Day khoá thì dừng trước khi bấm.
DAY_TABS = {d: f"{KP}/Day/day{d}.png" for d in (1, 2, 3, 4, 5)}
DAY_TABS_SELECTED = {d: f"{KP}/Day/day{d}Selected.png" for d in (1, 2, 3, 4, 5)}
DAY_THRESHOLD = 0.95

# Tab phụ trong một Day (3 tab, y ~252; tâm x 71 / 198 / 324). Ảnh tab chưa chọn thiếu thì
# bấm theo vị trí khi Day đang chọn (VD City Tax: chưa có ảnh "City Tax" chưa chọn).
SUB_TAB_Y = 252
SUB_TAB_X = (71, 198, 324)
SUB_TABS_REGION = (0, 33, 100, 39)   # % màn hình: hàng tab phụ
# Chưa chọn / đang chọn chỉ khác độ sáng chữ: khớp chéo 0,88 .. 0,90 -> 0,95.
# Màn khác (278 ảnh tests) <= 0,67.
TAB_THRESHOLD = 0.95

# Nút "Go" (Event/goButton.png) trên dòng King's Path: 0,91 .. 1,00 (nền có vệt sáng chạy
# ngang nên thấp hơn Gather Troops); nút Claim < 0,60.
GO_THRESHOLD = 0.85

# Tiêu đề dòng nhiệm vụ (khi một tab phụ có nhiều loại nhiệm vụ, VD Teamwork: Patrol +
# Donate): nút Go của dòng nằm ngay dưới-phải tiêu đề, cùng dòng: Go.y = tiêu đề.y + 43
# (đo: Patrol 301 -> Go 344, 413 -> 455; Donate 523 -> 567). Cho lệch ROW_GO_TOLERANCE px.
ROW_GO_DY = 43
ROW_GO_TOLERANCE = 8
ROW_TITLE_THRESHOLD = 0.75   # đúng dòng 0,81 .. 1,00 (nền có vệt sáng); màn khác <= 0,67
ROWS_REGION = (0, 35, 100, 100)   # % màn hình: danh sách dòng dưới hàng tab phụ

# Bấm Go -> game chuyển màn (thành / bản đồ / màn chức năng): chờ.
GO_WAIT = 5

# ---- Sau Go: công trình trong thành (building.py) ----------------------------------
# Go -> về thành, công trình của nhiệm vụ ở giữa màn hình. Chờ thêm GO_EXTRA_WAIT giây (cùng
# GO_WAIT là 10 s) -> bấm giữa màn hình -> chờ MENU_WAIT giây -> menu công trình; không thấy
# icon thì bấm giữa thêm lần nữa (MENU_TRIES lần). Rồi chờ màn chức năng tối đa SCREEN_WAIT giây.
GO_EXTRA_WAIT = 5
BUILDING_CENTER = (50, 50)   # % màn hình
MENU_WAIT = 5
MENU_TRIES = 2
SCREEN_WAIT = 10

# ---- Actions --------------------------------------------------------------------
OPEN_DAY = "kp_open_day"   # tab Day của nhiệm vụ chưa chọn -> bấm
ON_DAY = "kp_on_day"       # Day đang chọn nhưng tab phụ khác -> bấm tab phụ theo vị trí
OPEN_TAB = "kp_open_tab"   # tab phụ của nhiệm vụ chưa chọn -> bấm
ON_TAB = "kp_on_tab"       # tab phụ đang chọn -> tìm dòng Go của nhiệm vụ
