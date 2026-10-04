"""
constants.py — ảnh riêng của nhiệm vụ Heal (King's Path, Day 3).
"""
from ..constants import KP

# Ô chọn ở group King's Path: {"value": mục tiêu, "day": 3}.
KEY = "kings_path_heal"
DAY = 3   # ngày mở nhiệm vụ (dùng khi settings thiếu "day")
# Đạt mục tiêu -> lưu "kings_path_heal_complete", bỏ qua luôn tới khi hàm dọn dẹp event xoá.
# Không đủ lính bị thương -> chỉ lưu "kings_path_heal" (xong hôm nay, mai kiểm tra tiếp).

# Tab phụ "Healing Heart" (thứ 3, bên phải), dòng nhiệm vụ "Heal N troops".
TAB = f"{KP}/Tab/healingHeart.png"
TAB_SELECTED = f"{KP}/Tab/healingHeartSelected.png"
TAB_INDEX = 2

# ---- Sau khi bấm Go (ảnh tests/event/kings_path/screens/heal_*.png) -----------------------
# Go -> về thành, Bệnh viện (Hospital) ở giữa -> bấm giữa -> menu Bệnh viện (../building.py):
# - rảnh: có icon "Heal" (103, 231): 1,00 (heal_menu.png); màn khác <= 0,58;
# - đang chữa dở (đếm ngược): có "Speed Up" (89, 288): 1,00 (heal_menu_healing.png); cùng icon
#   Speed Up của menu doanh trại (0,92) — không sao, lúc này đang ở Bệnh viện.
# Speed Up xét trước: ưu tiên tăng tốc lượt đang chữa.
MENU_HEAL = f"{KP}/Heal/menuHeal.png"
MENU_SPEED_UP = f"{KP}/Heal/menuSpeedUp.png"
# Icon "Upgrade" (104, 355): menu chỉ có Citizen / Detail / Upgrade (heal_menu_empty.png: không
# có lính bị thương) 1,00; menu rảnh cũng có (1,00) nhưng Heal xét trước; menu đang chữa 0,39;
# menu doanh trại 0,89. Không có Speed Up, không có Heal mà có Upgrade -> xong hôm nay.
MENU_UPGRADE = f"{KP}/Heal/menuUpgrade.png"

# ---- Màn Hospital (bấm Heal trong menu) ---------------------------------------------------
# Tiêu đề "Hospital" (199, 23): 1,00; màn khác <= 0,53. Mặc định chọn hết lính bị thương.
HOSPITAL_TITLE = f"{KP}/Heal/hospitalTitle.png"
# Nút "Reset" góc dưới trái (69, 674): bấm để bỏ chọn hết, nút đổi thành "Select All".
# Reset 1,00 trên heal_screen.png / 0,60 sau khi reset; Select All 0,56 / 1,00. Reset khớp
# 0,90 ở màn khác (march_after_refill.png) -> chỉ xét khi thấy HOSPITAL_TITLE.
RESET = f"{KP}/Heal/reset.png"
SELECT_ALL = f"{KP}/Heal/selectAll.png"
# Sau Reset: cuộn danh sách lính xuống cuối (lính cấp thấp nhất ở dòng dưới cùng). Vuốt ở mép trái (x 5%,
# cột hình lính): vuốt giữa màn có thể trúng thanh kéo số lượng của một dòng -> kéo thanh, không cuộn.
LIST_SWIPE = (5, 70, 5, 30)     # % màn hình, ngón tay kéo lên = cuộn xuống
LIST_SCROLLS = 5
# Cuối danh sách: dưới dòng lính cuối có một khoảng trống nhỏ rồi tới khung tài nguyên (dải ngang (14, 512)
# rộng 368 cao 50): ở cuối 0,99 .. 1,00 (heal_list_end.png, heal_screen_reset.png); chưa tới cuối / màn khác
# <= 0,73. Thấy thì thôi cuộn (kể cả trước lần cuộn đầu: danh sách ngắn, không cần cuộn).
LIST_END = f"{KP}/Heal/listEnd.png"
LIST_SWIPE_WAIT = 3   # chờ sau mỗi lần cuộn
# Mọi thao tác (bấm / Back / gõ số) trong nhiệm vụ Heal chờ thêm EXTRA_WAIT giây (máy chậm).
EXTRA_WAIT = 2
# Dòng lính cấp thấp nhất = dòng có nút "Dismiss" thấp nhất (Dismiss (323, 221 / 312 / 403 / 495)):
# ô số "0 / 204,582" của dòng đó lệch DISMISS_TO_AMOUNT so với tâm nút (ô (285, 465)).
DISMISS = f"{KP}/Heal/dismiss.png"
DISMISS_TO_AMOUNT = (-38, -31)
# Dòng có Dismiss cao hơn MIN_DISMISS_Y: ô số của nó bị thanh "Wounded Troops" che (danh sách cuộn
# dở) -> bỏ qua. Dòng trên cùng khi chưa cuộn: Dismiss y = 221.
MIN_DISMISS_Y = 200
INPUT_DELETES = 7   # xoá số cũ trong ô (tối đa 7 chữ số) trước khi gõ số mới
# Nút "Heal" góc dưới phải (319, 666): 1,00 khi chưa chọn lính (xám) / 0,86 khi đã chọn.
HEAL_BUTTON = f"{KP}/Heal/healButton.png"
HEAL_BUTTON_THRESHOLD = 0.8
HEAL_WAIT = 3   # sau khi bấm Heal

# ---- Nhập số lượng (bấm ô số -> thanh nhập ở đáy màn, heal_input.png) ----------------------
# Nút "OK" của thanh nhập (344, 668): 1,00; màn khác <= 0,60. Gõ số tối đa cần heal, nhỏ hơn
# lính có thì game tự hạ về số lính có.
INPUT_OK = f"{KP}/Heal/inputOk.png"
INPUT_WAIT = 10
INPUT_TRIES = 2   # không thấy thanh nhập thì bấm lại ô số (lần bấm đầu có thể bị nuốt)

# ---- Sau khi bấm Heal: màn Hospital đang chữa (heal_healing.png) -------------------------
# Nút "Speed Up" góc dưới phải (319, 674): 1,00; màn khác <= 0,71.
SPEED_UP = f"{KP}/Heal/speedUp.png"

# ---- Màn Healing Speedup (heal_speedup*.png, heal_finish_all*.png) -----------------------
# Giống màn Training Speedup của train lính: lần đầu Speedup Settings -> hộp Finish All: tích ô
# "dùng speedup thường khi speedup riêng không đủ" nếu chưa tích -> Confirm; rồi Finish All.
# Dùng lại ảnh của train lính (Speedup Settings 0,96, Finish All 0,99, hộp Finish All / ô chưa
# tích / Confirm 1,00 trên màn này); riêng tiêu đề khác chữ: "Healing Speedup" (199, 23) 1,00
# (0,99 khi hộp Finish All che), Training Speedup 0,82, màn khác 0,39.
SPEEDUP_TITLE = f"{KP}/Heal/speedupTitle.png"
SPEEDUP_STEPS = 8
SPEEDUP_WAIT = 3
