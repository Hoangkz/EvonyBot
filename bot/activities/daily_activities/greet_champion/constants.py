"""
constants.py — ảnh của nhiệm vụ Daily Activities "Greet Champion" (thư mục ảnh ActivitiesGreetChampion/).
"""
from ..constants import ROOT, OPEN

KEY = "daily_greet_champion"   # key nhiệm vụ trong bot/worker/priority.py
LABEL = "Greet Champion"   # ô tích ở tab Daily Activities, key daily_done
FOLDER = "ActivitiesGreetChampion"
FOLDER_PATH = f"{ROOT}/{FOLDER}"
# Ảnh "đã xong": không có, xong khi đã chào tới 10/10 (hay dòng nhiệm vụ hết Go).
DONE_IMAGES = ()
# Tiêu đề dòng "Greet the Champion 2 time(s)." lấy từ Title.png (chỉ chữ "Greet the Champion", bỏ số lần);
# ACTIONS chỉ để đủ Task.
ACTIONS = (("Title.png", OPEN),)

# ---- Sau Go (run.after_go) --------------------------------------------------------------------
# Go -> về thành chính. Thành chính (Keep) ở giữa:
#   - có trái tim đỏ nổi trên đầu Keep (Heart.png, Champion đang chờ) -> bấm thẳng vào trái tim;
#   - không có -> như Gold Levy: bấm giữa Keep (open_menu nhận ra / tự học ảnh công trình) -> menu tròn,
#     icon "Champion" (Champion.png) -> bấm.
# Cả hai ra màn Champion (ChampionTitle.png): một mỹ nữ (VD Helen), nút "Greet n/10" góc dưới trái (Greet.png, chỉ
# phần icon). Vòng lặp liên tục, mỗi vòng xét màn hiện tại:
#   - thấy Greet 10/10 (GreetFull.png) -> xong hôm nay (đánh dấu);
#   - thấy nút "Unlock" (mỹ nữ chưa mở khoá, không có Greet) -> CHỈ lúc này mới đổi mỹ nữ: mũi tên PHẢI (ưu tiên), xám
#     (hết danh sách) thì TRÁI; cả hai xám -> hết mỹ nữ chào được, xong hôm nay;
#   - không thấy Unlock (đã mở khoá): Greet sáng (GREET_BUTTON) -> bấm Greet rồi bấm giữa màn MIDDLE_TAPS lần; Greet
#     khoá (không khớp ảnh) -> chỉ bấm giữa màn 1 lần. Popup xác nhận (Confirm) thì tích "Don't show again" rồi Confirm.
#     Không chờ gì.
# Dừng khi quá TASK_MAX_SECONDS.
# Mũi tên còn bấm được màu vàng (độ bão hoà HSV trung bình của điểm sáng 130..160), hết đường thì xám (~3).
HEART = f"{FOLDER_PATH}/Heart.png"
MENU_CHAMPION = f"{FOLDER_PATH}/Champion.png"
CHAMPION_TITLE = f"{FOLDER_PATH}/ChampionTitle.png"
GREET_BUTTON = f"{FOLDER_PATH}/Greet.png"   # icon nút Greet sáng (chưa khoá); khoá (ổ khoá + đếm ngược) thì không khớp
GREET_THRESHOLD = 0.8
# Bấm Greet -> popup "Are you sure you want to interact with <tên>?": ô "Don't show this again for today" (chưa tích
# khớp 1,00, màn thường 0,4) -> tích -> Confirm (xanh). Đã tích hôm nay thì popup không hiện nữa.
DONT_SHOW = f"{FOLDER_PATH}/DontShow.png"
CONFIRM = f"{FOLDER_PATH}/Confirm.png"
UNLOCK_BUTTON = f"{FOLDER_PATH}/Unlock.png"   # nút "Unlock" dưới cùng màn: mỹ nữ này chưa mở khoá
UNLOCK_THRESHOLD = 0.85
GREET_FULL = f"{FOLDER_PATH}/GreetFull.png"   # chữ "10/10" của nút Greet: đủ lượt thì nút đen, bấm chỉ hiện "Purchase the Champion Monthly Card
#                                             to unlock the privilege of Greet x10!". Khớp 1,00; "0/10" 0,68, "2/10" <= 0,63 -> ngưỡng riêng
GREET_FULL_THRESHOLD = 0.9
MIDDLE_TAPS = 10         # sau mỗi lần Greet: bấm giữa chừng này lần liên tiếp, không delay
ARROW_RIGHT = (94, 50)   # % màn hình: tâm mũi tên phải / trái đổi mỹ nữ
ARROW_LEFT = (5, 50)
ARROW_BOX_RIGHT = (358, 332, 388, 382)   # px (x0, y0, x1, y1) của hình thoi mũi tên, để xét còn vàng hay đã xám
ARROW_BOX_LEFT = (8, 332, 38, 382)
ARROW_BRIGHT = 180       # điểm sáng (V) của hình thoi
ARROW_MIN_SATURATION = 60
NEXT_WAIT = 3            # giây chờ sau khi bấm mũi tên đổi mỹ nữ (chỗ DUY NHẤT nhiệm vụ này phải chờ; mọi bước khác không chờ)
SCREEN_WAIT = 8          # giây tối đa đợi màn Champion hiện / màn đổi khi Back (xét ảnh liên tục, không ngủ)
TASK_MAX_SECONDS = 600   # tổng thời gian tối đa của nhiệm vụ sau Go (10 lần Greet ~ 10 phút)
GREET_MIDDLE = (50, 50)  # % màn hình: bấm giữa sau mỗi lần Greet (đóng hoạt ảnh / thưởng chào)
BACKS_AFTER = 4          # xong: Back (tối đa chừng này lần) tới khi về màn thành sạch
