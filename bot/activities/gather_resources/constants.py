"""
constants.py — hằng số của activity "Gather Resources" (cũng dùng cho tab UI). Toạ độ % theo màn 396x704 của giả lập.
"""
# (id, nhãn hiện ở ô chọn) — id là giá trị lưu DB, cũng là tên ảnh chữ của loại ở bảng Search (Gather/type_<id>.png)
RESOURCES = [
    ("food", "Food"),
    ("wood", "Wood"),
    ("stone", "Stone"),
    ("iron", "Iron"),
    ("gems", "Gems"),
]
DEFAULT_RESOURCE = "food"
MAX_LEVEL = 15       # cấp cao nhất ở ô chọn của tab (liệt kê từ MAX_LEVEL về 1); thanh cấp trong game còn lên quá 15
DEFAULT_LEVEL = 10
MAX_TROOP = 6        # số dòng (đội) tối đa ở tab; đội n = dòng thứ n, ở màn March bấm March luôn (không chọn preset)
SQUADS_KEY = "squads"   # settings: {"squads": [{"resource": "food", "level": 10}, ...]}

# DB (daily_done): "gather_resources_troop<n>_<epoch>" = đội ở dòng n rảnh lúc <epoch> (giây); mỗi đội giữ một key.
KEY = "gather_resources"
FREE_PREFIX = "gather_resources_troop{troop}_"

# ---- ảnh (Images/Gather/) ----
FOLDER = "Gather"
SEARCH_ICON = f"{FOLDER}/search.png"            # kính lúp ở bản đồ thế giới (thấy = đang ở thế giới, không popup)
CITY_MENU = "OpenBox/Setup/chucnang.png"         # nút "•••" ở màn thành (đo 0.98; vẫn khớp khi hộp "thoát game" phủ mờ lên)
TYPE_LABEL = FOLDER + "/type_{resource}.png"     # chữ loại mỏ ở hàng chọn của bảng Search
PLUS = f"{FOLDER}/plus.png"
MINUS = f"{FOLDER}/minus.png"
UNCHECKED = f"{FOLDER}/unchecked.png"            # ô "Only search Resource Spots with full resources" chưa tích
SEARCH_BUTTON = f"{FOLDER}/searchButton.png"
OCCUPY = f"{FOLDER}/occupy.png"                  # nút Occupy (thu thập) ở menu tròn của mỏ
MARCH_TITLE = f"{FOLDER}/marchTitle.png"
MARCH_BUTTON = f"{FOLDER}/marchButton.png"       # nút March vàng (có lính)
NO_TROOPS = f"{FOLDER}/noTroops.png"             # nút March xám: hết lính trong thành
NO_TARGET = f"{FOLDER}/noTarget.png"             # thông báo "No matching targets found near your Main City"
MARCH_FULL = f"{FOLDER}/marchFull.png"           # bấm Occupy khi đã dùng hết đường march: "You cannot send more troops."
TARGET_TAKEN = f"{FOLDER}/targetTaken.png"       # Search ra mỏ đội mình đang đi tới: "You can only send one army to the target at a time."

# ---- vùng tìm (% màn hình) và ngưỡng ----
TYPE_ROW = (0, 70, 100, 78)
PANEL = (0, 78, 100, 100)
MENU = (0, 25, 70, 70)
MARCH_BAR = (55, 90, 100, 98)
THRESHOLD = 0.85
TYPE_THRESHOLD = 0.8      # hàng loại có thể bị cuộn lệch nửa chữ (đo: 0.87 khi lệch, 1.0 khi thẳng)
BUTTON_THRESHOLD = 0.95   # nút March vàng / xám chỉ khác màu: khớp chéo 0.85
AFTER_OCCUPY_WAIT = 0.8   # sau khi bấm Occupy: chờ 0.8 giây rồi chụp, xem màn March / hết đường march / mỏ trùng
AFTER_OCCUPY_TRIES = 10   # ... tối đa 10 lần; không thấy gì thì bấm Search lại
OCCUPY_TRIES = 5         # sau khi bấm Search: chụp tìm Occupy mỗi 1 giây, tối đa 5 lần; không ra thì Search lại
MENU_SETTLE = 1          # giây chờ menu tròn trượt ra xong rồi mới bấm Occupy (bấm lúc đang trượt thì trượt)
NO_TARGET_THRESHOLD = 0.8   # chữ thông báo trên nền trong suốt (đo noTarget 1.0 / 0.44, marchFull 1.0 / 0.55, targetTaken 0.99 / 0.50)

# ---- toạ độ cố định (%) ----
TYPE_ICON_UP = 5          # bấm icon phía trên chữ loại (% chiều cao)
# Hàng loại: Summon, Monster, Terminator, Farm, Sawmill, Quarry, Iron Mine, Gems Mine, Cerberus, Ymir, ... (quái).
# Không thấy loại mỏ nào: ngón tay kéo DÀI sang phải 10 % -> 200 % (ra ngoài màn, game vẫn nhận) trong 1 giây, 1 lần -> hàng về
# đầu (đo: từ cuối hàng về đúng Summon..Farm); rồi ngón tay kéo CHẬM sang trái từng nấc -> hàng trượt dần về phía Gems Mine
# (đo: mỗi nấc dịch ~3 ô, không bỏ sót loại nào).
TYPE_FLING_TO_START = (10, 73, 200, 73)
TYPE_FLING_TIME, TYPE_FLINGS = 1.0, 1
# Thấy loại mỏ khác: so thứ tự trên hàng (RESOURCES: lúa, gỗ, đá, sắt, gem). Loại cần tìm nằm trước -> kéo chậm hàng về đầu
# (ngón tay sang phải); nằm sau -> kéo chậm hàng về cuối (ngón tay sang trái).
TYPE_SWIPE_TO_START = (20, 73, 70, 73)
TYPE_SWIPE_TO_END = (70, 73, 20, 73)
TYPE_SWIPE_TIME = 1.0
TYPE_MAX_STEPS = 6         # số lần kéo tối đa khi dò loại mỏ (Farm -> Gems Mine chỉ cần 2 nấc)
TO_WORLD_TAP = (92, 93)   # nút quả địa cầu góc dưới phải ở màn thành
GATHER_TIME = (100, 608, 190, 630)                   # px: giờ thu thập cạnh đồng hồ cát (x0, y0, x1, y1)
MARCH_TIME = (280, 676, 340, 694)                    # px: giờ đi dưới nút March
LEVEL_BOX = (305, 568, 375, 592)                     # px: ô số cấp bên phải nút "+" (read_number)

# ---- giới hạn / thời gian ----
LEVEL_TAP_WAIT = 0.3       # giây chờ sau mỗi lần bấm +/− rồi mới chụp đọc lại ô số
LEVEL_MAX_TAPS = 40        # tổng số lần bấm +/− tối đa khi chỉnh cấp
LEVEL_READ_TRIES = 3       # đọc ô số không ra: chụp lại tối đa chừng này lần (mỗi lần cách WAIT_INTERVAL) rồi bỏ
LEVEL_STUCK = 3            # bấm mà số không đổi chừng này lần liền (chạm cấp thấp / cao nhất của game): bỏ
SEARCH_TRIES = 3
TO_WORLD_TRIES = 8        # số bước (Back popup / bấm ra thế giới) tối đa để tới bản đồ thế giới
SEND_TRIES = 2            # Occupy không sang màn March: làm lại cả lượt (mở Search ... Occupy) một lần nữa
WAIT_TRIES, WAIT_INTERVAL = 8, 1   # chờ màn hình đổi: xem lại mỗi 1 giây, tối đa 8 lần
FREE_MARGIN = 30          # giây cộng thêm vào giờ đội về
NO_TROOP_WAIT = 30 * 60   # hết lính: mọi đội chờ 30 phút rồi thử lại
MARCH_FULL_WAIT = 10 * 60  # hết đường march: mọi đội chờ 10 phút (đường trống lại khi một đội bất kỳ về)
FAIL_WAIT = 10 * 60       # không gửi được đội (không tìm thấy mỏ, mỏ trùng...): đội đó chờ 10 phút
