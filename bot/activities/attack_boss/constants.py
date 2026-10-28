"""
constants.py — Attack Boss: key cấu hình của tab, tên nguồn nhận boss, thời gian chờ.
"""
TAB = "Attack Boss"   # = tên activity = tên tab = khoá settings (database.TAB_COLUMNS)

# Tab (settings["Attack Boss"]): ngoài các key giống Join Monster War (troop, use_stamina, select_general, ...,
# selected_bosses) còn có:
SOURCE_KEY = "source"            # nguồn nhận boss: một trong SOURCES
PLAYER_KEY = "player_name"       # tên người chơi gửi boss (nguồn player_chat)
EMAIL_KEY = "email"              # tài khoản đăng nhập iScout (nguồn api): bot tự đăng nhập trong trình duyệt nó mở
PASSWORD_KEY = "password"        # mật khẩu iScout (lưu nguyên văn trong DB, ô nhập hiện dấu chấm)
TYPE_KEY = "attack_type"         # cách đánh: một trong ATTACK_TYPES
VIKING = "Viking"                # boss Viking được gửi đi theo luồng chung (nguồn Alliance / Whisper); chỉ Viking tự gọi (Summon) là riêng
VIKING_SUMMON_KEY = "viking_summon"   # tích Summon: bot tự gọi Viking theo cơ chế Viking Summon (cùng key với tab Join Monster War); độ khó ở "viking_level"
MARCH_SPEED_KEY = "march_speedup"    # tăng tốc lúc hành quân tới boss: một trong SPEEDUP_CHOICES
RETURN_SPEED_KEY = "return_speedup"  # tăng tốc lúc đội quân trở về
SPEEDUP_CHOICES = ("No", "All", "5s", "10s", "15s", "20s", "30s", *(str(n) for n in range(1, 11)))     # "No" = không tăng tốc (mặc định); "1".."10" = dùng đúng chừng đó cái vật phẩm
SPEEDUP_DEFAULT = "No"
EGGS_KEY = "crazy_eggs_hours"    # Crazy Eggs: 0 (không làm) / 1..4 giờ, cùng ý nghĩa với ô ở tab Daily Activities

SOURCE_ALLIANCE = "alliance_chat"
SOURCE_PLAYER = "player_chat"
SOURCE_API = "api"
ISCOUT_DONE_MINUTES = 10          # nguồn IsCout: boss đã đánh chỉ nhớ tối đa chừng này phút (theo id và theo toạ độ), sau đó còn sống thì đánh lại được
ISCOUT_BATCH = 6                 # nguồn IsCout: mỗi lượt lấy bấy nhiêu boss gần thành nhất, đánh hết rồi mới kiểm tra trình duyệt lại
ISCOUT_CHECK_POLL = 1            # nguồn IsCout: giây giữa hai lần kiểm tra trình duyệt iScout lúc bắt đầu (chờ mở trình duyệt / đăng nhập / nhận dữ liệu)
SOURCES = (
    (SOURCE_ALLIANCE, "Alliance chat"),
    (SOURCE_PLAYER, "Whisper"),
    (SOURCE_API, "IsCout"),
)
SOURCE_DEFAULT = SOURCE_ALLIANCE

TYPE_ATTACK = "attack"           # đánh một mình
TYPE_WAR = "alliance_war"        # lập Alliance War (rally) cho liên minh vào đánh cùng
ATTACK_TYPES = (
    (TYPE_ATTACK, "Attack"),
    (TYPE_WAR, "Alliance War"),
)
TYPE_DEFAULT = TYPE_ATTACK

IDLE_WAIT = 5            # giây nghỉ khi nguồn chưa có boss mới

# Bước đánh (đo trên giả lập 396 x 704)
RING_MAX_DIST = 100            # px: IsCout chỉ nhận vòng màu cách tâm màn hình không quá chừng này; xa hơn là boss khác (đo trên 21913: boss đích lệch < 50 px, boss khác 160-190 px)
NAME_GAP = 15                  # px: IsCout tìm dòng tên boss trong vùng cam: chữ cách nhau dưới chừng này cột gộp thành một dòng (huy hiệu cấp + từng từ của tên)
NAME_MIN_W = 40                # px: dòng tên rộng ít nhất chừng này (tia lửa và mảnh viền vòng sáng hẹp hơn hoặc thấp hơn)
NAME_MIN_H, NAME_MAX_H = 7, 12   # px: dòng tên cao trong khoảng này
NAME_TAP_ABOVE = 4             # px: bấm cao hơn mép trên của dòng tên chừng này (y nhỏ hơn y của tên một chút) = vào chân / thân boss
RETAP_AFTER = 2              # IsCout: bấm vào boss mà sau chừng này lần tìm nút Attack (mỗi ATTACK_MENU_POLL giây) vẫn chưa thấy thì tìm lại vòng màu (boss có thể đang di chuyển)
RETAP_MOVE = 20               # px: vòng màu tìm lại cách chỗ đã bấm hơn chừng này thì bấm lại (đáy vòng nhấp nháy ~10 px theo hoạt ảnh lửa); không thì chỉ chờ tiếp (menu hiện chậm do lag)
ATTACK_MENU_POLL = 1          # IsCout: giây giữa hai lần tìm nút Attack của menu nhanh sau khi bấm vào boss
ATTACK_MENU_WAIT = 8          # IsCout: chờ tối đa chừng này giây; không thấy nút Attack thì tính boss là đã đánh ngay
BOSS_POLL = 1                # giây giữa hai lần tìm vòng màu boss trong BOSS_WAIT
BOSS_WAIT = 8                # giây chờ boss hiện ra giữa màn hình sau khi nhảy tới toạ độ
BOSS_NEAR = 90               # px: boss nằm trong khoảng này quanh giữa màn hình (boss_scan.CAMERA_PX) mới là boss cần đánh
POPUP_WAIT = 5               # giây chờ cửa sổ thông tin boss sau khi bấm Attack ở menu nhanh
MARCH_OPEN_WAIT = 6          # giây chờ màn March mở sau khi bấm Attack ở cửa sổ boss
MARCH_WAIT = 6               # giây chờ về bản đồ sau khi bấm March
POLL = 0.5                   # giây giữa hai lần kiểm tra
ATTACK_FROM_WAR = (-166, 0)  # px: nút Attack so với nút Alliance War (bossPopup.png) trong cửa sổ thông tin boss (283,531) -> (117,531)
MARCH_BUTTON = "AttackBoss/march.png"   # chữ "March" của nút March ở màn đánh boss (bên dưới có đồng hồ nên ảnh hanhquan.png của Join Boss chỉ khớp ~0,69)
MARCH_THRESHOLD = 0.8
LOW_ODDS = "AttackBoss/lowOdds.png"   # hai dòng chữ đầu của hộp "winning odds are extremely low. Are you sure you still want to send the troops?" (Cancel / Confirm) hiện sau khi bấm March
LOW_ODDS_THRESHOLD = 0.7              # đo trên 24 ảnh thật: có hộp 1,0; không có hộp tối đa 0,23
LOW_ODDS_CANCEL = (-65, 77)           # nút Cancel so với tâm ảnh mẫu (hộp nằm cố định giữa màn hình)
# Alliance War (rally): bấm nút Alliance War ở cửa sổ boss -> hộp "Alliance War Rally!" chọn thời gian chờ -> màn March (bố cục như màn March của Join Monster War)
RALLY_TITLE = "AttackBoss/rallyTitle.png"
RALLY_MINUTES = 5                                   # thời gian chờ rally chọn mặc định
RALLY_BUTTONS = {5: (110, 365), 10: (283, 365), 30: (110, 420), 60: (283, 420)}     # nút từng thời gian trong hộp (396 x 704)
RALLY_WAIT = 4                                      # giây chờ hộp chọn thời gian rally
DEFEATED_ATTR = "attack_viking_defeated"           # trên bot: đã thấy popup "boss Viking đã bị hạ" (có chữ Summon) mà chưa gọi boss mới
VIKING_LABEL = (197, 332)                           # nhãn "Viking(Asking for help)" của boss Viking tự gọi (boss vừa gọi nằm giữa màn hình, nhãn cao hơn giữa ~20 px)
MAIN_GENERAL_REGION = (80, 25, 97, 35)   # % màn hình: kính lúp ở ô Main General của màn March khi Attack (tâm 349, 204)

# Kết quả của attack(): đã hành quân / bỏ hẳn (boss chết hoặc không được tích) / chưa đánh được, giữ lại thử sau
MARCHED, DROP, RETRY = "marched", "drop", "retry"
ON_SPOT_KM = 3               # camera lệch toạ độ boss không quá chừng này mỗi trục thì coi là đang đứng trên boss
BACK_ARROW = "AttackBoss/backArrow.png"   # mũi tên quay lại vàng ở góc trên trái của màn toàn màn hình (chat, cuộc trò chuyện); màn March khớp 0,72
BACK_ARROW_THRESHOLD = 0.9
WORLD_TRIES = 6
TO_CITY = "CityMap/toCity.png"   # nút góc dưới phải khi ở bản đồ thế giới (= common/go_home.TO_CITY)

# Nhảy tới toạ độ (goto.py): hộp "Search" mở bằng cách bấm dòng toạ độ X:… Y:… ở đáy bản đồ (đo trên 396 x 704)
COORD_BAR = (205, 622)
SEARCH_X, SEARCH_Y = (135, 382), (270, 382)      # ô X và ô Y của hộp Search
SEARCH_TITLE = "AttackBoss/searchTitle.png"
GO_BUTTON = "AttackBoss/searchGo.png"
GO_THRESHOLD = 0.8
SEARCH_OPEN_WAIT = 4         # giây chờ hộp Search / thanh nhập mở
INPUT_DELETES = 12           # xoá lùi thừa trước khi gõ (xoá khi ô đã trống không sao)
INPUT_SETTLE = 0.5           # giây chờ sau khi gõ
GOTO_WAIT = 3                # giây chờ camera chạy tới toạ độ sau khi bấm Go
GOTO_TRIES = 3

# Đọc chat (sources.py), đo trên 396 x 704
CHAT_BAR = (150, 650)            # dòng chat ở đáy bản đồ: bấm để mở màn chat
CHAT_TITLE = "Chat/title.png"    # chữ "Chat" ở đầu màn chat
CHAT_THRESHOLD = 0.8
CHAT_OPEN_WAIT = 4               # giây chờ màn chat mở
TAB_ALLIANCE = (200, 52)         # tab Alliance của màn chat (World ở 55, Whisper ở 335)
TAB_WAIT = 1.5
SCROLL = (200, 150, 200, 520)    # vuốt xuống = cuộn lên xem tin cũ hơn (danh sách tin cao ~590 px, mỗi lần cuộn ~370 px nên các trang chồng lên nhau)
SCROLL_TIME = 0.6
SCROLL_WAIT = 1.0
TAB_WHISPER = (335, 52)
CONVERSATION_WAIT = 2.5          # giây chờ cuộc trò chuyện Whisper mở sau khi bấm dòng của người chơi
WHISPER_KEEP = 10                # số ảnh tin nhắn boss được giữ (đánh xong vẫn giữ để loại tin trùng); quá thì bỏ ảnh cũ nhất
WHISPER_BATCH = 6                # số tin boss mới nhất đọc mỗi lần vào Whisper (mỗi ~5 phút có boss mới, đánh hết 6 con mất > 10 phút)
AGE_LIMIT_MIN = 30               # phút: chỉ nhận tin gửi trong khoảng này; gặp tin cũ hơn thì thôi cuộn lên
MAX_PAGES = 10                   # số trang chụp tối đa mỗi lần (tin không đọc được giờ thì chặn ở đây)
SAME_PAGE_DIFF = 1.0             # độ lệch điểm ảnh trung bình giữa hai trang liên tiếp dưới mức này = không cuộn được nữa (hết tin)

# Tăng tốc (speedup.py), đo trên 396 x 704
SPEED_ROW = {"Marching": "AttackBoss/rowMarching.png", "Returning": "AttackBoss/rowReturning.png"}   # nhãn dòng trong bảng hành quân
SPEED_ROW_THRESHOLD = 0.85
SPEED_ICON = "AttackBoss/speedIcon.png"            # icon mũi tên sang (⏩) ở cuối mỗi dòng của bảng hành quân
SPEED_ICON_THRESHOLD = 0.8
SPEED_ICON_SAME_ROW = 12             # px: icon nằm cùng dòng với nhãn khi lệch dọc không quá chừng này
SPEED_ICON_OFFSET = (115, 7)         # icon tăng tốc so với tâm nhãn dòng (tâm nhãn x ~83, icon x ~198)
SPEED_TITLE = "AttackBoss/speedTitle.png"          # tên vật phẩm đầu tiên "Adv Troop March Speedup": thấy là popup tăng tốc đang mở
SPEED_USE_X_PERCENT = 84.6           # tâm nút Use luôn ở x cố định này (% chiều rộng màn hình; 335 / 396 px)
SPEED_USE_DY = 17                    # tâm nút Use thấp hơn tâm tên vật phẩm "Adv Troop March Speedup" chừng này px (tên ở y 556-576, nút ở y ~583): y tính từ tên, KHÔNG tìm
                                     # chữ Use / số lượng vì số lượng dài (VD "Use (2,390)") có thể tràn ra ngoài viền nút
SPEED_TIME_BOX = (120, 533, 280, 546)    # thanh thời gian còn lại trong popup (x1, y1, x2, y2), chỉ phần trong của thanh (không dính viền sáng)
SPEED_TIME_MIN = 105                 # chữ thời gian: mọi kênh màu lớn hơn mức này (xám trắng; thanh xanh có kênh đỏ / xanh dương thấp)
SPEED_CELL_OFFSETS = (0, 7, 18, 25, 37, 44)   # ô của sáu chữ số "hh:mm:ss" so với mép trái của dãy số (mỗi chữ số rộng ~7 px, dấu hai chấm ~4 px)
SPEED_CELL_W = 7
SPEED_DIGIT_DIST = 0.25              # khác biệt trung bình tối đa với mẫu Images/OCR/SpeedTime để nhận ra chữ số
SPEED_PANEL = "AttackBoss/panelCollapsed.png"      # bảng hành quân đang thu gọn ("▶ March"): bấm để mở ra
SPEED_FACTOR = 0.5                   # mỗi cái vật phẩm đầu tiên (Adv Troop March Speedup) giảm 50% thời gian còn lại
SPEED_MAX_COUNT = 12                 # số cái tối đa tính ra cho một lần tăng tốc (chặn khi đọc sai thời gian quá lớn)
SPEED_OPEN_WAIT = 3
SPEED_USE_WAIT = 1.5
SPEED_MAX_USES = 6                   # số lần dùng vật phẩm tối đa mỗi lần tăng tốc (mỗi lần giảm một nửa thời gian)

# Số đường hành quân (lanes.py), đo trên 396 x 704
LANES_BOX = (186, 100, 214, 116)     # (x1, y1, x2, y2) bộ đếm "2/5" ở đầu bảng hành quân
MAX_LANES = 6                        # tối đa 6 đường cho tài khoản mạnh nhất; tài khoản yếu hơn ít hơn (bộ đếm cho biết), và còn bị chặn bởi số đội quân đã chọn
LANES_WAIT = 5                       # giây chờ giữa hai lần kiểm tra khi hết đường (chờ có đường trống mới đánh tiếp)
LANE_ADD_SLOT = "AttackBoss/addMarchSlot.png"    # dòng "+ Add March Slot" ngay dưới dòng cuối của bảng hành quân
LANE_ADD_Y0 = 135                    # y tâm dòng đó khi bảng chưa có dòng nào (1 dòng: 168, 2 dòng: 201)
LANE_ROW_PITCH = 33                  # chiều cao một dòng của bảng
LANE_DIGIT_DIST = 0.2                # khác biệt tối đa với mẫu Images/OCR/Lanes để nhận ra chữ số số đường tối đa
LANE_ROWS = {"Rallying": "AttackBoss/rowRallying.png", "Marching": "AttackBoss/rowMarching.png", "Returning": "AttackBoss/rowReturning.png"}   # ba loại dòng của bảng hành quân
LANE_PANEL_REGION = (0, 16, 56, 40)    # % màn hình: vùng nhãn các dòng của bảng hành quân (x 0-222, y 112-282)
NO_LANES = "AttackBoss/noMoreTroops.png"          # thông báo "You cannot send more troops." khi đã hết đường hành quân (hiện sau khi chọn thời gian rally / bấm March)
NO_LANES_THRESHOLD = 0.8
NO_LANES_WAIT = 3                    # giây chờ thông báo hết đường sau khi chọn thời gian rally
STAMINA = "stamina"                  # kết quả của attack(): hết thể lực mà không dùng được (ô Use Stamina là No, hết vật phẩm, hoặc dùng rồi vẫn thiếu): run bỏ các boss còn lại, tăng tốc, nghỉ STAMINA_WAIT_MINUTES
STAMINA_WAIT_MINUTES = 20            # phút nghỉ sau khi hết thể lực (như Join Monster War)
FULL = "full"                        # kết quả của attack(): game báo hết đường hành quân (giữ boss lại, chuyển sang tăng tốc / chờ)
FULL_TRIES = 150                     # hết đường mà không dùng tăng tốc: số lần bấm lại 5 phút / March tối đa (mỗi lần cách FULL_RETRY_WAIT giây, ~5 phút)
FULL_RETRY_WAIT = 2                  # giây chờ giữa hai lần bấm lại khi game báo hết đường
