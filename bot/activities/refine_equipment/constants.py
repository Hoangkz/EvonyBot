"""
constants.py — "Refine Equipment" activity: tinh luyện 6 trang bị của một tướng (ảnh Images/RefineEquipment/, toạ độ, danh mục thuộc tính).
"""
KEY = "refine_equipment"          # key nhiệm vụ trong priority.py / daily_done (`refine_equipment_error` khi lỗi)
NAME = "Refine Equipment"         # tên hiện trong log, cũng là tên tab / nút Select Activity
FOLDER = "RefineEquipment"

# True: nhiệm vụ vào danh sách của worker khi có ít nhất một trang bị đã tích thuộc tính. Vòng Refine / Confirm / Cancel + Lock đã chạy trọn trên 21913 (nhẫn, 3 Gold).
READY = True

# ---- Settings (cột `refine_equipment` của DB) ---------------------------------------------------------------
# {"favorite": bool, "general_type": "all", "slots": {"weapon": {"lines": [{"attribute": "Ground Troop Attack", "color": "gold", "lock": true}, {"attribute": "Ranged Troop Attack", "color": "gold", "lock": false}], "max_refines": 100, "stop": {"gold": 1, "orange": 0}}, ...}}
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
MAX_LINES = 4                       # mỗi trang bị có đúng 4 dòng tinh luyện, mỗi dòng ra ngẫu nhiên một trong nhiều thuộc tính (tổng số vàng + cam của một mức dừng <= 4)
STOP_KEY = "stop"                   # khi nào dừng (Confirm): {"gold": số dòng vàng, "orange": số dòng cam} trong 4 dòng New, CHO TỪNG TRANG BỊ
DEFAULT_STOP = (1, 0)               # 1 vàng


def _stop_options() -> tuple:
    """(vàng, cam) các mức dừng, tổng 1 .. MAX_LINES dòng. Mức có vàng xếp trước, từ nhiều xuống ít (4 Gold, 3 Gold + 1 Orange, 3 Gold, ... 1 Gold),
    rồi các mức chỉ có cam (4 Orange ... 1 Orange)."""
    options = [(g, o) for g in range(0, MAX_LINES + 1) for o in range(0, MAX_LINES + 1) if 1 <= g + o <= MAX_LINES]
    return tuple(sorted(options, key=lambda go: (go[0] == 0, -go[0], -go[1])))


STOP_OPTIONS = _stop_options()


def stop_label(gold: int, orange: int) -> str:
    """"2 Gold", "1 Orange", "1 Gold + 1 Orange"."""
    return " + ".join(f"{n} {name}" for n, name in ((gold, "Gold"), (orange, "Orange")) if n)


KIND_KEY = "kind"                   # loại tăng của dòng: tăng % ("+3.9%", "1%~10%") hay tăng chỉ số ("+128", "1~333") hay cả hai
KINDS = (("all", "All"), ("percent", "%"), ("flat", "Flat"))
DEFAULT_KIND = "all"
LOCK_KEY = "lock"                   # True: dòng đã ra đúng (thuộc tính + màu) thì khoá lại (ổ khoá cạnh dòng) rồi Refine tiếp các dòng còn lại

COLORS = (("orange", "Orange"), ("gold", "Gold"))
DEFAULT_COLOR = "gold"

# Tab loại tướng ở hàng đầu danh sách Generals (id, nhãn, tâm x theo % màn hình). Đã đối chiếu với game trên 21913: biểu tượng mũ = All, kiếm = Military, búa = Development, vương miện = Duty, tháp =
# Subordinate City (tab đang chọn giãn ra hiện tên đó).
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
# Danh sách Generals sau lọc không có tướng nào (VD tim yêu thích mà chưa có tướng yêu thích): giữa màn hiện chữ "No favorite General", 1,00 (màn khác <= 0,48)
# -> dừng activity, không bấm tướng.
NO_GENERAL = f"{FOLDER}/noGeneral.png"
# Chưa tích tim mà loại tướng không có ai: giữa màn hiện "No General!" (1,00; màn "No favorite General" 0,83 vì chung chữ; màn khác <= 0,47).
NO_GENERAL_ANY = f"{FOLDER}/noGeneralAny.png"
NO_GENERAL_THRESHOLD = 0.9
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
# Nút Refine xanh giữa đáy màn Refine Equipment. Khi có dòng bị khoá nút hiện thêm dòng giá kim cương ("1.5K -> 0") nên cả nút không còn khớp một ảnh: chỉ lấy chữ "Refine"
# (chữ nằm ở y 668 khi không có giá, ~657 khi có giá), tìm trong vùng đáy màn: không giá 1,00; có giá 0,76; màn khác trong vùng <= 0,49 -> ngưỡng 0,7.
REFINE_BUTTON = f"{FOLDER}/refineWord.png"
REFINE_BUTTON_REGION = (25, 90, 75, 100)    # % màn hình
REFINE_BUTTON_THRESHOLD = 0.7
STABLE_TRIES = 5           # đọc 4 dòng New: lặp (cách 1 s) tới khi hai lần đọc liên tiếp giống nhau, tối đa ngần này lần chờ thêm; không ổn định thì coi như chưa đọc được
LOCK_VERIFY_TRIES = 5      # sau khi bấm khoá: chờ 1 s rồi đọc lại ổ khoá, tối đa ngần này lần cho tới khi các dòng vừa bấm đã khoá
CANCEL = "Event/KingsPath/Refine/cancel.png"
CONFIRM = f"{FOLDER}/confirm.png"                   # 1,00 sau khi Refine; màn Refine Equipment chưa có kết quả 0,75 -> ngưỡng 0,9

# ---- Dòng có sẵn (khung Original) -------------------------------------------------------------------------------
# Mỗi dòng Original có ổ khoá bên trái: đã khoá = vàng (lockOn), chưa khoá = xám (lockOff). Đo trên 21913 (nhẫn có 4 dòng, khoá 0 / 1 / 2 dòng): đúng trạng thái
# 1,00, trạng thái kia 0,61 .. 0,63 -> ngưỡng 0,9. Trang bị chưa tinh luyện không có khung Original, không thấy ổ khoá nào (0 dòng). Khoá + chưa khoá <= MAX_LINES.
# Khoá dòng làm nút Refine tính thêm kim cương (hiện "1.5K -> 0" trên nút).
LOCK_ON = f"{FOLDER}/lockOn.png"
LOCK_OFF = f"{FOLDER}/lockOff.png"
LOCK_THRESHOLD = 0.8                # ổ khoá mở 0,85 .. 1,00, đóng 0,92 .. 1,00; trạng thái kia <= 0,63
LOCK_REGION = (3, 54, 14, 78)       # % màn hình: cột ổ khoá của 4 dòng Original (y 405 .. 522)

# Hộp cảnh báo khi Refine mà đang có dòng cao cấp CHƯA khoá ("You have unlocked high quality attribute(s)... Are you sure you want to refine now?"): tích ô
# "Don't show this again for today" rồi Confirm để Refine tiếp. Dùng chung ảnh với King's Path Refine (ô tích lệch WARN_BOX_FROM_LABEL so với tâm chữ).
WARN_LABEL = "Event/KingsPath/Refine/warnLabel.png"
WARN_CONFIRM = "Event/KingsPath/Refine/warnConfirm.png"
WARN_BOX_FROM_LABEL = (-106, -1)
UNKNOWN_POPUP_CHECKS = 2   # màn đứng yên (hai lần chụp liên tiếp giống nhau) mà không thấy nút Refine: nghi hộp thoại lạ chặn màn, kiểm tra tối đa ngần này lần rồi bấm Back một lần
STATIC_DIFF = 1.5          # độ lệch điểm ảnh trung bình (0 .. 255) giữa hai lần chụp nhỏ hơn mức này = màn đứng yên
RESULT_WAIT_TRIES = 10     # sau khi bấm Refine: chờ 1 s rồi tìm nút Confirm (kết quả New), tối đa ngần này lần; hết mà chưa thấy thì bấm Refine lại
REFINE_BUTTON_TRIES = 10   # sau khi bấm Cancel / Confirm: chờ 1 s rồi tìm nút Refine, tối đa ngần này lần

# Nhận trạng thái màn Refine Equipment theo ổ khoá (cột trái x 12 .. 55, mọi y có thể của khung Original vì khung dịch lên xuống tuỳ màn): có ổ khoá MỞ = trang bị đã tinh
# luyện, làm bình thường; không có khoá mở mà có khoá ĐÓNG = cả 4 dòng đã khoá thì không Refine được nữa, bỏ qua sang trang bị khác; không thấy ổ khoá nào = chưa tinh luyện
# (những khoảng đen lớn, chưa có khung Original): chỉ việc bấm Refine rồi chờ bước kế tiếp.
LOCK_SEARCH_REGION = (3, 30, 14, 90)      # % màn hình

# ---- Ô trang bị trống ----------------------------------------------------------------------------------------
# Ô chưa mặc đồ là biểu tượng xám tối; ô đã mặc đồ có khung màu và hình đồ. Đo độ bão hòa (S trong HSV) trung bình của ô SLOT_HALF px quanh tâm
# (ảnh tướng chưa có đồ nào, 396x704): ô trống 56 .. 65; ô đã mặc đủ 6 món 153 .. 214 -> dưới EMPTY_SATURATION là ô trống, bỏ qua không bấm. Người dùng chỉ làm đồ khung đỏ / vàng trở lên (màu đậm) nên đồ phẩm chất thấp (khung trắng / xám, có thể dưới ngưỡng) không cần lo.
SLOT_HALF = 35
EMPTY_SATURATION = 100

# ---- Giới hạn / chờ ------------------------------------------------------------------------------------------
GENERAL_WAIT_TRIES = 8   # sau khi bấm tướng đầu tiên: chờ 1 s rồi kiểm tra đã sang màn tướng (Enhance) chưa, tối đa ngần này lần
SLOT_TAP_TRIES = 2       # số lần bấm ô trang bị tối đa: không thấy View sau VIEW_WAIT_TRIES lần chờ thì bấm lại (vẫn ở màn tướng)
SCREEN_WAIT_TRIES = 8     # sau khi bấm View / Refine / Refine (Craft): chờ 1 s rồi tìm dấu hiệu của màn kế, tối đa ngần này lần
BUTTON_TAP_TRIES = 2       # số lần bấm mỗi nút tối đa: không thấy màn kế thì bấm lại nút (nếu còn hiện)
VIEW_WAIT_TRIES = 8      # sau khi bấm ô trang bị: chờ 1 s rồi tìm chữ View, tối đa ngần này lần
MENU_WAIT_TRIES = 5    # sau khi bấm icon Generals: chờ 1 s rồi kiểm tra đã vào danh sách chưa, tối đa ngần này lần
CITY_RETURN_BACKS = 6     # về thành trước khi làm: Back tối đa ngần này lần (từ màn Refine Equipment tới thành cần 5: Craft, General Equipment, màn tướng, danh sách, thành)
MAX_STEPS = 15         # số bước tối đa tới màn tướng
SCREEN_WAIT = 8        # giây tối đa chờ một màn / nút hiện sau khi bấm
STEP_WAIT = 2          # sau mỗi lần bấm
REFINE_WAIT = 4        # chờ kết quả sau khi bấm Refine
BACKS_TO_GENERAL = 3   # Refine Equipment -> Craft -> General Equipment -> màn tướng
BACKS_TO_CITY = 4      # màn tướng -> danh sách -> thành (dư 1 lần cho chắc)
