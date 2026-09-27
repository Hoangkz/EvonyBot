"""
constants.py — Join Monster War: ảnh template, vùng tìm kiếm, giới hạn và tên màn hình.
"""
JB = "JoinBoss"

# ---- ảnh ---------------------------------------------------------------
LISTBOSS = f"{JB}/listboss.png"            # (1) icon danh sách War ở cột phải màn hình chính
ALLIANCE_HOME = f"{JB}/lienminh.png"       # (1) chữ "Alliance" -> đang ở màn hình chính
PVP_WAR = f"{JB}/PvPWar.png"               # (2) tab PvP War -> đang ở danh sách War
JOIN = f"{JB}/thamgia.png"                 # (2.2) nút Join
JOINED = f"{JB}/Joined.png"                # (2.3) nút Joined
LOCATION = f"{JB}/location.png"            # icon ghim trước toạ độ boss
BOSS_MONSTER = f"{JB}/bossMonster.png"     # (3) nhãn "Boss Monster" trên màn hình March
MARCH = f"{JB}/hanhquan.png"               # (3, 4) nút March
SELECT_GENERAL = f"{JB}/selectGeneral.png" # (4) ô "+" chọn Main General
SELECT = f"{JB}/Select.png"                # (4.1) nút Select trong danh sách tướng
OUT_OF_STAMINA = f"{JB}/hettheluc.png"     # (5) nút Confirm của popup hết thể lực
STAMINA_ITEM = f"{JB}/theluc.png"          # (5.1) item thể lực trong Use Item
USE_STAMINA = f"{JB}/usetheluc.png"        # nút Use trong hộp chọn số lượng
PLUS = f"{JB}/plus.png"                    # nút "+" trong hộp chọn số lượng
LEAVE_ALLIANCE = "Items/outLM.png"         # popup rời liên minh
SKIP_DIR = f"{JB}/JoinBossNotParticipat"   # ảnh boss không join (mọi .png trong thư mục)

# ---- vùng tìm kiếm của từng ảnh (% màn hình: x0, y0, x1, y1) ---------------
# Mỗi ảnh chỉ dò trong vùng nó xuất hiện (đo trên ảnh chụp 396x704, nới rộng
# thêm một ít) -> nhẹ CPU và không khớp nhầm chỗ khác.
FULL = (0, 0, 100, 100)
REGIONS = {
    LISTBOSS: (80, 20, 100, 90),        # cột icon bên phải (đo: x86-97 y57-60, vị trí dọc có thể đổi)
    ALLIANCE_HOME: (80, 70, 100, 90),   # đo: x85-97 y78-80
    PVP_WAR: (5, 6, 45, 15),            # đo: x11-37 y9-12
    JOIN: (70, 35, 100, 90),            # đo: x80-88, y47-49 (thẻ trên) / y80-82 (thẻ dưới)
    JOINED: (70, 35, 100, 90),          # đo: x77-91, y47-50 / y80-83
    MARCH: (60, 90, 100, 100),          # đo: x68-83 y94-97
    BOSS_MONSTER: (35, 20, 65, 40),     # đo: x43-58 y24-35
    SELECT_GENERAL: (5, 45, 30, 65),    # đo: x10-24 y51-59
    SELECT: (65, 10, 100, 100),         # đo: x71-93, mỗi tướng 1 nút (y51-55, y87-90...)
    LEAVE_ALLIANCE: FULL,               # chưa biết vị trí
    # Ảnh không có trong bảng (thể lực, hết thể lực...) -> tìm cả màn hình.
}

# Vùng so sánh ảnh (không phải để tìm ảnh).
ROI_LIST = (0, 20, 100, 90)             # danh sách War: so trước / sau khi cuộn
ROI_TROOPS = (0, 45, 100, 82)           # khung tướng / quân trên màn hình March: đổi sau khi chọn preset

BOTTOM_CARD_Y = 70        # % : có nút Join/Joined thấp hơn mức này -> thẻ thứ 2 có mặt, có thể còn thẻ bên dưới
NOT_JOIN_LIMIT = 30       # số rally nhớ là đã xử lý
SAME_SPOT = 10            # px: hai vị trí gần hơn mức này là cùng một rally
IDLE_WAIT = 10            # giây chờ khi không có gì để làm
MAX_SCROLL = 10           # số lần cuộn xuống tối đa trước khi quay về đầu danh sách

# ---- tên màn hình -----------------------------------------------------------
S_STAMINA_POPUP = "stamina_popup"
S_STAMINA_LIST = "stamina_list"
S_MARCH = "march"
S_GENERALS = "generals"
S_LIST = "list"
S_HOME = "home"
S_LEAVE_ALLIANCE = "leave_alliance"
S_TAP = "tap"
S_BACK = "back"
