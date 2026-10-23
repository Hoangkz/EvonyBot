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
# Tab "Development" (cái búa) ở hàng tab của màn chọn tướng, khi chưa chọn (khớp 0,99;
# đang chọn thì tab thành chữ "Development", khớp 0,61) -> tab tích "Development General".
CHOOSE_DEVELOPMENT = f"{JB}/chooseDevelopment.png"
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
# Chữ "Total Troops" của màn chi tiết đội (hiện khi cú vuốt cuộn bị game coi là tap vào thẻ rally):
# không khớp màn nào khác -> Back một lần về danh sách War.
TROOP_DETAIL = f"{JB}/totalTroops.png"
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
    TROOP_DETAIL: (3, 38, 45, 46),        # đo: x22-138, y288-308
    PVP_WAR: (5, 6, 45, 15),              # đo: x11-37 y9-12
    WAR_TAB: (5, 88, 50, 100),            # đo: x15-41 y94-97
    LISTBOSS: (80, 20, 100, 90),          # cột icon bên phải (đo: x86-97 y57-60, vị trí dọc có thể đổi)
    BOSS_MONSTER: (35, 20, 65, 45),       # đo: chữ x 163-234, y 262-269 (41-59%, 37-38%)
    SELECT: (65, 10, 100, 100),           # đo: nút Select (329, 373) / (329, 627), mỗi tướng 1 nút
    FAVORITE_ON: (30, 15, 40, 20),        # đo: trái tim lọc (139, 124); tim của từng tướng ở x 358: ngoài vùng
    FAVORITE_OFF: (30, 15, 40, 20),
    CHOOSE_DEVELOPMENT: (45, 5, 75, 28),  # đo: búa (219, 77) màn Select a General / (219, 161) màn Generals
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
# Ô "Monster War" (cạnh ô "War", cùng hình): phải đang tích mới thấy rally đánh boss. Không thấy dấu tích
# (không tích: khớp ~0,6; tích: 0,82-0,92) thì bấm vào tâm ô (đo trên 396x704: ô x37-61, y104-132).
MONSTER_TICKED_REGION = (0, 12, 30, 21)
MONSTER_TICKED_THRESHOLD = 0.78
MONSTER_WAR_TAP = (49, 118)
MONSTER_TICK_TRIES = 3             # số lần bấm tối đa mỗi lượt chạy

# Hàng preset trên màn March (% màn hình): ô i (1-8) có tâm x = PRESET_X0 + (i - 1) * PRESET_DX,
# y = PRESET_Y. Đo trên 396x704: tâm x 41, 86, 130, 175, 220, 265, 310, 354; y 77.
PRESET_COUNT = 8
# Ổ khoá ô preset khớp 0,877-0,98 tuỳ ô (máy 21913: ô 6 = 0,895, ô 7 = 0,877), ô mở chỉ ~0,2-0,25:
# ngưỡng mặc định 0,9 đếm thiếu khoá -> tưởng ô khoá là ô mở.
PRESET_LOCKED_THRESHOLD = 0.8
# Ô preset đang chọn có vòng sáng cam quanh biểu tượng: vành bán kính 18-22 px quanh tâm ô
# (trên chiều rộng 396 -> 4,5-5,6 %). Đo: ô đang chọn 138 điểm cam (R > 150, R - B > 90), ô khác 0.
PRESET_RING_R = (4.5, 5.6)            # % chiều rộng màn hình
PRESET_ACTIVE_MIN_PIXELS = 30
PRESET_ACTIVE_WAIT = 5                # giây tối đa chờ ô vừa bấm sáng lên (kiểm tra mỗi 1 giây)

# Popup dùng vật phẩm thể lực: điểm gần cuối thanh trượt số lượng (% màn hình; đo thanh
# x 90-300, y 370 trên 396x704) -> dùng hết (use_stamina = ALL).
STAMINA_SLIDER_END = (74.7, 52.6)
# Dùng vật phẩm thể lực mốc 200 / 300 / 400 / 500: popup số lượng mở sẵn ở mốc 100 thể lực nên bấm
# nút + thêm (mốc - 100) / thể lực mỗi vật phẩm lần (VD vật phẩm 10, mốc 200: 10 lần; vật phẩm
# 50, mốc 500: 8 lần). Loại vật phẩm nhận theo cả biểu tượng (khung + thịt + số, 72x72, cắt ở
# popup x 50-122, y 225-297): chọn mẫu khớp cao nhất. Khớp chéo đo trên 21913: 10 <-> 25 = 0,951
# (cùng khung xanh lá), các cặp khác <= 0,87, đúng loại = 1,00 -> không lấy mẫu đầu tiên vượt ngưỡng.
STAMINA_ITEMS = {100: f"{JB}/staminaItem100.png", 50: f"{JB}/staminaItem50.png",
                 25: f"{JB}/staminaItem25.png", 10: f"{JB}/staminaItem10.png"}
STAMINA_ITEM_MIN_SCORE = 0.9
STAMINA_ITEM_REGION = (8, 30, 34, 44)    # % màn hình: biểu tượng vật phẩm ở góc trái popup (x 40-130, y 220-300)
STAMINA_PLUS = f"{JB}/staminaPlus.png"
STAMINA_BAR_REGION = (0, 48, 100, 58)    # % màn hình: dải chứa nút − và nút + (y 370 / 704 = 52,6)
STAMINA_BASE = 100                       # thể lực popup mở sẵn
STAMINA_PLUS_DELAY = 0                       # giây sau mỗi lần bấm +: mỗi tap ADB đã mất ~0,5 giây
STAMINA_ADDED_WAIT = 1                   # giây chờ sau khi bấm + xong, trước khi bấm Use
TROOP_BACK_WAIT = 1   # giây chờ sau khi Back khỏi màn chi tiết đội
STAMINA_REFILL_WAIT = 2             # giây chờ sau khi bấm Use (game tự đóng popup) rồi mới Back
PRESET_X0, PRESET_DX, PRESET_Y = 10.4, 11.3, 11

# Dải ngay trên nút Battle Logs / Auto-Join (% màn hình). Trống (chỉ nền tối,
# sáng nhất ~43) = danh sách War đã hiện hết; còn thẻ bị che thì có chữ/viền
# sáng tới ~250. Đo trên 6 ảnh 396x704 (y 605-640).
LIST_END_REGION = (5, 86, 95, 91)
LIST_END_MAX_LIGHT = 80
JOIN_MIN_Y, JOIN_MAX_Y = 37.25, 87.35   # % chiều cao màn hình (y 262-615 / 704): nút Join ngoài dải này bị bỏ qua
# Nút "Join" thật khớp 0,96-1,00; nút "Joined" (chữ chứa "Join") khớp tới 0,80 -> ngưỡng
# 0,9, và bỏ luôn điểm Join nằm đè lên một nút Joined (JOINED_OVERLAP px).
JOIN_THRESHOLD = 0.9
JOINED_OVERLAP = 20
SAME_SPOT = 10                      # px: two positions closer than this are the same rally

# What to do when each image is seen.
OUT_OF_STAMINA = "out_of_stamina"
TROOP_DETAIL_SEEN = "troop_detail_seen"   # thấy màn chi tiết đội -> Back rồi chờ TROOP_BACK_WAIT
MARCH_SCREEN = "march_screen"
JOIN_LIST = "join_list"
SCROLL = "scroll"
JOINED = "joined"
TAP = "tap"
BACK = "back"
NO_BOSS = "no_boss"   # màn hình chính không có listboss / PvPWar không có boss nào
LEAVE_ALLIANCE_POPUP = "leave_alliance_popup"

# run() trả về IDLE khi thoát vì đang rảnh (chỉ khi bật exit_when_idle) —
# worker sẽ quay lại kiểm tra boss sau. Hết thể lực cũng là rảnh (không phải
# dừng hẳn): worker chuyển sang làm nhiệm vụ rồi quay lại sau.
IDLE = "idle"
