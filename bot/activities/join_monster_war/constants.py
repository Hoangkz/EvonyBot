"""
constants.py — Join Monster War images, limits and action names.
"""
JB = "JoinBoss"
JOIN = f"{JB}/thamgia.png"
MARCH = f"{JB}/hanhquan.png"
TROOP_CHECK = f"{JB}/checkLocam.png"
LOCATION = f"{JB}/location.png"
# Optional general selection in the march screen (C# selectGeneral ->
# chooseDevelopment -> chooseFavorite -> Select).
SELECT_GENERAL = f"{JB}/selectGeneral.png"
CHOOSE_DEVELOPMENT = f"{JB}/chooseDevelopment.png"
CHOOSE_FAVORITE = f"{JB}/chooseFavorite.png"
SELECT = f"{JB}/Select.png"
STAMINA_ITEM = f"{JB}/theluc.png"
USE_STAMINA = f"{JB}/usetheluc.png"
PLUS = f"{JB}/plus.png"
JOINED_BUTTON = f"{JB}/Joined.png"
PVP_WAR = f"{JB}/PvPWar.png"
WAR_TAB = f"{JB}/checkChienTranh.png"
LISTBOSS = f"{JB}/listboss.png"
ALLIANCE_ICON = f"{JB}/lienminh.png"   # nút Liên minh ở màn hình chính
BOSS_MONSTER = f"{JB}/bossMonster.png"
WAR_TICKED = f"{JB}/warTicked.png"         # ô "War" đang tích (xem WAR_UNTICK_TRIES)

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
    BOSS_MONSTER: (35, 20, 65, 40),       # đo: x43-58 y24-35
    SELECT_GENERAL: (5, 45, 30, 65),      # đo: x10-24 y51-59
    CHOOSE_DEVELOPMENT: (40, 5, 80, 20),  # đo: x51-65 y9-14
    SELECT: (65, 10, 100, 100),           # đo: x71-93, mỗi tướng 1 nút
    WAR_TICKED: (44, 12, 58, 21),         # đo: ô War x48-54 y15-18 (ô Monster War ở x9-19: ngoài vùng)
}

# Ô "War" (rally đánh người chơi) ở đầu danh sách War, cạnh ô "Monster War":
# ảnh ô hình thoi CÓ dấu tích (cắt từ ảnh chụp thật). Thấy thì bấm bỏ tích để
# danh sách chỉ còn rally đánh boss. Ô "Monster War" giống hệt nên chỉ tìm trong
# REGIONS[WAR_TICKED]. Điểm khớp: đang tích 1.00, đã bỏ tích ~0.67.
WAR_UNTICK_TRIES = 3                # số lần bấm tối đa mỗi lượt chạy, tránh bấm qua bấm lại

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
