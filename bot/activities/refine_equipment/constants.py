"""
constants.py — "Refine Equipment" activity: tinh luyện 6 trang bị của một tướng (ảnh Images/RefineEquipment/, toạ độ, danh mục thuộc tính).
"""
KEY = "refine_equipment"          # key nhiệm vụ trong priority.py / daily_done (`refine_equipment_error` khi lỗi)
NAME = "Refine Equipment"         # tên hiện trong log, cũng là tên tab / nút Select Activity
FOLDER = "RefineEquipment"

# Hạn chế khi chưa đọc được dòng thuộc tính (xem TODO.md): False thì nhiệm vụ không vào danh sách của worker.
READY = False

# ---- Settings (cột `refine_equipment` của DB) ---------------------------------------------------------------
# {"favorite": bool, "general_type": "all", "slots": {"weapon": {"lines": [{"attribute": "Ground Troop Attack", "color": "gold", "lock": true}, {"attribute": "Ranged Troop Attack", "color": "gold", "lock": false}], "max_refines": 100}, ...}}
FAVORITE_KEY = "favorite"           # tích tim lọc tướng yêu thích trước khi chọn tướng
GENERAL_TYPE_KEY = "general_type"   # tab loại tướng ở danh sách Generals
SLOTS_KEY = "slots"                 # {id ô trang bị: {"lines": [...]}}; ô không có dòng nào = bỏ qua
LINES_KEY = "lines"                 # các dòng cần có của ô: mỗi dòng riêng thuộc tính, màu tối thiểu, khoá hay không
ATTRIBUTE_KEY = "attribute"
COLOR_KEY = "color"                 # màu tối thiểu của dòng đó: orange | gold
MAX_REFINES_KEY = "max_refines"     # số lần Refine tối đa CHO TỪNG TRANG BỊ mỗi lượt: 100 .. 1000 hoặc "ALL" (không giới hạn)
REFINES_ALL = "ALL"
MAX_REFINES_OPTIONS = (*range(100, 1001, 100), REFINES_ALL)
DEFAULT_MAX_REFINES = 100
LOCK_KEY = "lock"                   # True: dòng đã ra đúng (thuộc tính + màu) thì khoá lại (ổ khoá cạnh dòng) rồi Refine tiếp các dòng còn lại
MAX_LINES = 4                       # mỗi trang bị có đúng 4 dòng tinh luyện; người dùng thêm tối đa ngần này dòng cần có (nút +), hai dòng có thể trùng thuộc tính

COLORS = (("orange", "Orange"), ("gold", "Gold"))
DEFAULT_COLOR = "gold"

# Tab loại tướng ở hàng đầu danh sách Generals (id, nhãn, tâm x theo % màn hình): All + 4 tab biểu tượng (kiếm, búa, vương miện, tháp).
# Tab đang chọn giãn ra hiện tên (hammer = "Development") và đẩy các tab khác đi chỗ khác, nên x dưới đây chỉ đúng khi "All" đang chọn:
# bấm ALL_TAB_X trước (nằm trong tab All khi nó đang chọn, và là tab đầu khi tab khác đang chọn), rồi mới bấm tab cần.
GENERAL_TYPES = (
    ("all", "All", 18.2),
    ("military", "Military", 40.4),
    ("development", "Development", 56.3),
    ("duty", "Duty", 73.7),
    ("sub", "Subordinate City", 89.6),
)
DEFAULT_GENERAL_TYPE = "all"
ALL_TAB_X = 10.9                    # % màn hình
TYPE_TAB_Y = 23.6                   # % màn hình
FIRST_GENERAL = (22.7, 49.7)        # % màn hình: thẻ tướng đầu tiên (sau lọc)

# ---- Danh mục thuộc tính theo trang bị ----------------------------------------------------------------------
# Lấy từ nút Advanced Filter ("About Equipment Refining") của màn Refine Equipment, chụp trên máy 21913 (6 ô của tướng đầu tiên).
_TROOPS = ("Ground Troop", "Ranged Troop", "Mounted Troop", "Siege Machine")
_ATTACK = tuple(f"{t} Attack" for t in _TROOPS)
_DEFENSE = tuple(f"{t} Defense" for t in _TROOPS)
_HP = tuple(f"{t} HP" for t in _TROOPS)
_LOAD = tuple(f"{t} Load" for t in _TROOPS)
_GATHER = tuple(f"{r} Gathering Speed" for r in ("Food", "Lumber", "Stone", "Ore"))
_MARCH = ("March Speed", "March Speed to Monsters", "Increases Troop Capacity in Subordinate City")
_SUBORDINATE = ("Increases Gold Production Speed in Subordinate City", "Increases Construction Speed in Subordinate City",
                "Subordinate City Training Speed")

# (id, nhãn, vị trí ô trên màn tướng theo % màn hình, thuộc tính)
SLOTS = (
    ("weapon", "Weapon", (15.9, 24.1), _ATTACK + _GATHER + _MARCH),
    ("armor", "Armor", (15.9, 38.4), _DEFENSE + _LOAD + _SUBORDINATE),
    ("boots", "Boots", (15.9, 51.8), _DEFENSE + _LOAD + _MARCH),
    ("helmet", "Helmet", (83.8, 24.1), _HP + _GATHER + _SUBORDINATE),
    ("pants", "Pants", (83.8, 38.4), _HP + _GATHER + _SUBORDINATE),
    ("ring", "Ring", (83.8, 51.8), _ATTACK + _LOAD + _SUBORDINATE),
)

# ---- Ảnh -----------------------------------------------------------------------------------------------------
FEATURES_ICON = "OpenBox/Setup/chucnang.png"        # nút "•••" ở màn thành
# Menu "•••": icon + chữ Generals (240,298)-(305,356) trên màn 396x704: 1,00; màn khác <= 0,43.
MENU_GENERALS = f"{FOLDER}/menuGenerals.png"
# Danh sách Generals: tim lọc yêu thích ở (139, 208). Tim tắt 0,88 (giao diện mới; ngưỡng 0,8), màn khác thấp.
FAVORITE_ON = "JoinBoss/favoriteOn.png"
FAVORITE_OFF = "JoinBoss/favoriteOff.png"
FAVORITE_REGION = (25, 25, 45, 35)                  # % màn hình
FAVORITE_THRESHOLD = 0.8
# Màn tướng: nút Enhance đáy trái (60, 677): 1,00; vẫn thấy khi hộp thông tin trang bị phủ lên (0,99), màn khác <= 0,52.
ENHANCE = f"{FOLDER}/enhance.png"
# Hộp thông tin trang bị: nút View (vị trí lên xuống theo số dòng của hộp): 1,00; 0,92 .. 0,99 giữa 6 ô; màn khác <= 0,52.
VIEW = f"{FOLDER}/view.png"
VIEW_THRESHOLD = 0.85
# Màn General Equipment: nút Refine xanh đáy phải (320, 677): 1,00; màn khác <= 0,53.
EQUIPMENT_REFINE = f"{FOLDER}/equipmentRefine.png"
# Màn Craft (tab Refine, mở từ General Equipment): nút Refine xanh đáy trái, dùng chung ảnh với King's Path Refine.
CRAFT_REFINE = "Event/KingsPath/Refine/refineButton.png"
# Màn Refine Equipment: tiêu đề (1,00; General Equipment 0,81 -> ngưỡng 0,9), nút Cancel / Confirm sau khi Refine.
EQUIPMENT_TITLE = "Event/KingsPath/Refine/equipmentTitle.png"
EQUIPMENT_TITLE_THRESHOLD = 0.9
REFINE_BUTTON = "Event/KingsPath/Refine/equipmentRefine.png"   # nút Refine xanh giữa đáy (197, 668)
CANCEL = "Event/KingsPath/Refine/cancel.png"
CONFIRM = f"{FOLDER}/confirm.png"                   # 1,00 sau khi Refine; màn Refine Equipment chưa có kết quả 0,75 -> ngưỡng 0,9

# ---- Dòng có sẵn (khung Original) và ô Gold / Orange Attribute -------------------------------------------------
# Mỗi dòng Original có ổ khoá bên trái: đã khoá = vàng (lockOn), chưa khoá = xám (lockOff). Đo trên 21913 (nhẫn có 4 dòng, khoá 0 / 1 / 2 dòng): đúng trạng thái
# 1,00, trạng thái kia 0,61 .. 0,63 -> ngưỡng 0,9. Trang bị chưa tinh luyện không có khung Original, không thấy ổ khoá nào (0 dòng). Khoá + chưa khoá <= MAX_LINES.
# Khoá dòng làm nút Refine tính thêm kim cương (hiện "1.5K -> 0" trên nút).
LOCK_ON = f"{FOLDER}/lockOn.png"
LOCK_OFF = f"{FOLDER}/lockOff.png"
LOCK_THRESHOLD = 0.9
LOCK_REGION = (3, 54, 14, 78)       # % màn hình: cột ổ khoá của 4 dòng Original (y 405 .. 522)
# Hai ô "Gold Attribute" / "Orange Attribute" (báo khi ra thuộc tính vàng / cam), dùng chung ảnh với King's Path Refine: chữ khớp 1,00; ô đang tích 0,91 (boxOn) /
# trống 0,46; ô trống 1,00 (boxOff) / tích 0,46 (đo 21913). Ô lệch BOX_FROM_LABEL so với tâm chữ.
LABEL_GOLD = "Event/KingsPath/Refine/labelGold.png"
LABEL_ORANGE = "Event/KingsPath/Refine/labelOrange.png"
LABEL_THRESHOLD = 0.8
BOX_FROM_LABEL = {LABEL_GOLD: (-33, 8), LABEL_ORANGE: (-42, 8)}
BOX_ON = "Event/KingsPath/Refine/boxOn.png"
BOX_OFF = "Event/KingsPath/Refine/boxOff.png"
BOX_HALF = 18

# ---- Ô trang bị trống ----------------------------------------------------------------------------------------
# Ô chưa mặc đồ là biểu tượng xám tối; ô đã mặc đồ có khung màu và hình đồ. Đo độ bão hòa (S trong HSV) trung bình của ô SLOT_HALF px quanh tâm
# (ảnh tướng chưa có đồ nào, 396x704): ô trống 56 .. 65; ô đã mặc đủ 6 món 153 .. 214 -> dưới EMPTY_SATURATION là ô trống, bỏ qua không bấm.
SLOT_HALF = 35
EMPTY_SATURATION = 100

# ---- Giới hạn / chờ ------------------------------------------------------------------------------------------
GENERAL_WAIT_TRIES = 8   # sau khi bấm tướng đầu tiên: chờ 1 s rồi kiểm tra đã sang màn tướng (Enhance) chưa, tối đa ngần này lần
SLOT_TAP_TRIES = 2       # số lần bấm ô trang bị tối đa: không thấy View sau VIEW_WAIT_TRIES lần chờ thì bấm lại (vẫn ở màn tướng)
SCREEN_WAIT_TRIES = 8     # sau khi bấm View / Refine / Refine (Craft): chờ 1 s rồi tìm dấu hiệu của màn kế, tối đa ngần này lần
BUTTON_TAP_TRIES = 2       # số lần bấm mỗi nút tối đa: không thấy màn kế thì bấm lại nút (nếu còn hiện)
VIEW_WAIT_TRIES = 8      # sau khi bấm ô trang bị: chờ 1 s rồi tìm chữ View, tối đa ngần này lần
MENU_WAIT_TRIES = 5    # sau khi bấm icon Generals: chờ 1 s rồi kiểm tra đã vào danh sách chưa, tối đa ngần này lần
MAX_STEPS = 15         # số bước tối đa tới màn tướng
SCREEN_WAIT = 8        # giây tối đa chờ một màn / nút hiện sau khi bấm
STEP_WAIT = 2          # sau mỗi lần bấm
REFINE_WAIT = 4        # chờ kết quả sau khi bấm Refine
BACKS_TO_GENERAL = 3   # Refine Equipment -> Craft -> General Equipment -> màn tướng
BACKS_TO_CITY = 4      # màn tướng -> danh sách -> thành (dư 1 lần cho chắc)
