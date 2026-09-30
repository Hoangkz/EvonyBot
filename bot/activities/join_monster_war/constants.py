"""
constants.py — Join Monster War images, limits and action names.
"""
JB = "JoinBoss"
JOIN = f"{JB}/thamgia.png"
MARCH = f"{JB}/hanhquan.png"
LOCATION = f"{JB}/location.png"
# Chọn tướng trên màn March (xem _choose_general): dấu "+" ở ô tướng còn trống ->
# màn "Select a General": trái tim lọc tướng yêu thích (đã tích = đỏ) -> nút "Select".
SELECT_GENERAL = f"{JB}/selectGeneral.png"
SELECT = f"{JB}/Select.png"
FAVORITE_ON = f"{JB}/favoriteOn.png"      # trái tim lọc đã tích (khớp 1,00; chưa tích 0,19)
FAVORITE_OFF = f"{JB}/favoriteOff.png"    # trái tim lọc chưa tích (khớp 1,00; đã tích 0,07)
# Ô tướng trên màn March (% màn hình), dùng làm vùng tìm "+" / kính lúp của ô đó.
MAIN_GENERAL = (3, 47, 97, 63)            # đo: y 330-443, kính lúp (348, 388)
ASSISTANT_GENERAL = (3, 64, 97, 79)       # đo: y 452-555, "+" (65, 502), kính lúp (348, 502)
# Nút "Confirm" của popup "You do not have enough Stamina. Get more now?" (hiện sau khi bấm
# March). Cắt từ ảnh chụp thật; không khớp màn nào khác (cao nhất 0,46).
NOT_ENOUGH_STAMINA = f"{JB}/hettheluc.png"
# Màn "Use Item" sau khi bấm Confirm: chữ "Use (" của nút "Use ( N )" ở mỗi vật phẩm thể lực
# (chỉ tìm ở cột nút bên phải: chữ "Use it to gain..." ở cột mô tả cũng khớp).
STAMINA_ITEM_USE = f"{JB}/staminaItemUse.png"
# Nút "Use" lớn của popup chọn số lượng.
STAMINA_USE = f"{JB}/staminaUse.png"
JOINED_BUTTON = f"{JB}/Joined.png"
PVP_WAR = f"{JB}/PvPWar.png"
WAR_TAB = f"{JB}/checkChienTranh.png"
LISTBOSS = f"{JB}/listboss.png"
ALLIANCE_ICON = f"{JB}/lienminh.png"   # nút Liên minh ở màn hình chính
# Chữ "Boss Monster" trên màn March (rally đánh boss). Không dùng lá cờ xanh (bossMonster.png):
# rally đang "Attacking" thì chỗ đó là hai thanh kiếm.
BOSS_MONSTER = f"{JB}/bossMonsterText.png"
WAR_TICKED = f"{JB}/warTicked.png"         # ô "War" đang tích (xem WAR_UNTICK_TRIES)
# Màn March: hàng 8 ô preset đội quân ở trên cùng; ô chưa mở có ổ khoá.
PRESET_LOCKED = f"{JB}/presetLocked.png"
# Kính lúp ở ô "Main General": preset đang chọn có tướng chính -> dùng được.
GENERAL_SEARCH = f"{JB}/generalSearch.png"

# Vùng có thể xuất hiện của từng ảnh (% màn hình: x0, y0, x1, y1) — chỉ tìm
# trong vùng đó cho nhanh và không khớp nhầm. Đo trên ảnh chụp 396x704 rồi
# nới rộng thêm một ít. Ảnh không có trong bảng (thể lực, hết thể lực, popup
# chung...) -> tìm cả màn hình.
REGIONS = {
    JOIN: (70, 35, 100, 90),              # đo: x80-88, y47-49 (thẻ trên) / y80-82 (thẻ dưới)
    JOINED_BUTTON: (70, 35, 100, 90),     # đo: x77-91, y47-50 / y80-83
    MARCH: (60, 90, 100, 100),            # đo: x68-83 y94-97
    PVP_WAR: (5, 6, 45, 15),              # đo: x11-37 y9-12
    WAR_TAB: (5, 88, 50, 100),            # đo: x15-41 y94-97
    LISTBOSS: (80, 20, 100, 90),          # cột icon bên phải (đo: x86-97 y57-60, vị trí dọc có thể đổi)
    BOSS_MONSTER: (35, 20, 65, 45),       # đo: chữ x 163-234, y 262-269 (41-59%, 37-38%)
    SELECT: (65, 10, 100, 100),           # đo: nút Select (329, 373) / (329, 627), mỗi tướng 1 nút
    FAVORITE_ON: (30, 15, 40, 20),        # đo: trái tim lọc (139, 124); tim của từng tướng ở x 358: ngoài vùng
    FAVORITE_OFF: (30, 15, 40, 20),
    WAR_TICKED: (44, 12, 58, 21),         # đo: ô War x48-54 y15-18 (ô Monster War ở x9-19: ngoài vùng)
    PRESET_LOCKED: (0, 7, 100, 16),       # hàng preset, đo: y 9-13
    STAMINA_ITEM_USE: (65, 40, 95, 100),  # cột nút Use, đo: (292, 360), (296, 479), (288, 598)
    STAMINA_USE: (45, 65, 95, 78),        # đo: (281, 502)
    GENERAL_SEARCH: (80, 50, 97, 60),     # ô Main General, đo: (348, 388); kính lúp tướng phụ ở y 502: ngoài vùng
}

# Ô "War" (rally đánh người chơi) ở đầu danh sách War, cạnh ô "Monster War":
# ảnh ô hình thoi CÓ dấu tích (cắt từ ảnh chụp thật). Thấy thì bấm bỏ tích để
# danh sách chỉ còn rally đánh boss. Ô "Monster War" giống hệt nên chỉ tìm trong
# REGIONS[WAR_TICKED]. Điểm khớp: đang tích 1.00, đã bỏ tích ~0.67.
WAR_UNTICK_TRIES = 3                # số lần bấm tối đa mỗi lượt chạy, tránh bấm qua bấm lại

# Hàng preset trên màn March (% màn hình): ô i (1-8) có tâm x = PRESET_X0 + (i - 1) * PRESET_DX,
# y = PRESET_Y. Đo trên 396x704: tâm x 41, 86, 130, 175, 220, 265, 310, 354; y 77.
PRESET_COUNT = 8

# Popup dùng vật phẩm thể lực: điểm gần cuối thanh trượt số lượng (% màn hình; đo thanh
# x 90-300, y 370 trên 396x704) -> dùng hết (use_stamina = ALL).
STAMINA_SLIDER_END = (74.7, 52.6)
STAMINA_REFILL_WAIT = 5             # giây chờ sau khi bấm Use, trước khi Back về màn March
PRESET_X0, PRESET_DX, PRESET_Y = 10.4, 11.3, 11

# Dải ngay trên nút Battle Logs / Auto-Join (% màn hình). Trống (chỉ nền tối,
# sáng nhất ~43) = danh sách War đã hiện hết; còn thẻ bị che thì có chữ/viền
# sáng tới ~250. Đo trên 6 ảnh 396x704 (y 605-640).
LIST_END_REGION = (5, 86, 95, 91)
LIST_END_MAX_LIGHT = 80
JOIN_MIN_Y, JOIN_MAX_Y = 262, 615   # "Join" buttons outside this band are ignored
# Nút "Join" thật khớp 0,96-1,00; nút "Joined" (chữ chứa "Join") khớp tới 0,80 -> ngưỡng
# 0,9, và bỏ luôn điểm Join nằm đè lên một nút Joined (JOINED_OVERLAP px).
JOIN_THRESHOLD = 0.9
JOINED_OVERLAP = 20
SAME_SPOT = 10                      # px: two positions closer than this are the same rally

# What to do when each image is seen.
OUT_OF_STAMINA = "out_of_stamina"
MARCH_SCREEN = "march_screen"
JOIN_LIST = "join_list"
SCROLL = "scroll"
JOINED = "joined"
TAP = "tap"
BACK = "back"
NO_BOSS = "no_boss"   # màn hình chính không có listboss / PvPWar không có boss nào
LEAVE_ALLIANCE_POPUP = "leave_alliance_popup"

# run() trả về IDLE khi thoát vì đang rảnh (chỉ khi bật exit_when_idle) —
# worker sẽ quay lại kiểm tra boss sau. Mọi lần return khác (vd hết thể lực
# mà use_stamina = No) = Join Boss dừng hẳn.
IDLE = "idle"
