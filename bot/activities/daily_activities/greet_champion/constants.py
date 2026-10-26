"""
constants.py — ảnh của nhiệm vụ Daily Activities "Greet Champion" (thư mục ảnh ActivitiesGreetChampion/).
"""
from ..constants import ROOT

KEY = "daily_greet_champion"   # key nhiệm vụ trong bot/worker/priority.py
LABEL = "Greet Champion"   # ô tích ở tab Daily Activities, key daily_done
FOLDER = "ActivitiesGreetChampion"
FOLDER_PATH = f"{ROOT}/{FOLDER}"

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
# Chữ vàng "10/10" cạnh "Greet" = đủ lượt. Chữ đè trong suốt lên nền mỹ nữ nên so MÀU đổi theo nền (mẫu cắt trên Esmeralda: Helen
# 10/10 chỉ 0,70 -> không nhận ra, chờ tới hết 600 s, không lưu xong). So HÌNH chữ: chỉ lấy điểm vàng (HSV GREET_FULL_HSV) của mẫu
# và của vùng GREET_FULL_REGION rồi so hai mặt nạ. Đo: Esmeralda 10/10 1,00 (có toast 0,96), Helen 10/10 0,875; Helen 2/10 0,60.
GREET_FULL = f"{FOLDER_PATH}/GreetFull.png"
GREET_FULL_REGION = (30, 500, 100, 535)   # px (x0, y0, x1, y1): dòng chữ "Greet n/10" dưới nút Greet
GREET_FULL_HSV = ((18, 120, 150), (35, 255, 255))   # khoảng HSV của chữ vàng
GREET_FULL_THRESHOLD = 0.78
# Thông báo giữa màn "You cannot Empower anymore for today!" (bấm giữa = vào mỹ nữ, hết lượt Empower hôm nay). KHÔNG có nghĩa
# Greet đã 10/10 (21913: hiện cả lúc Greet 2/10 đang chờ hồi) -> chỉ thôi bấm giữa khi Greet khoá, chờ LOCKED_WAIT rồi xét lại.
# Cắt dòng đầu "You cannot Empower anymore for"; khớp 1,00, 1012 ảnh test khác <= 0,37.
EMPOWER_LIMIT = f"{FOLDER_PATH}/EmpowerLimit.png"
LOCKED_WAIT = 1          # giây chờ giữa hai lần xét khi Greet khoá mà đã hết Empower (không bấm giữa)
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

# Nhiệm vụ Daily chỉ cần GREET_REQUIRED lần chào: đủ là lưu "xong hôm nay" (KEY) vào DB NGAY rồi chào tiếp trong cùng lần chạy tới khi
# bị ngắt. Phần còn lại (tới 10/10) do việc nối tiếp MORE_KEY làm: tìm thành -> trái tim / Keep -> Champion -> chào tiếp.
GREET_REQUIRED = 5
GREET_MAX = 10           # số lần chào tối đa mỗi ngày
MORE_KEY = "daily_greet_champion_more"   # xong (10/10 hoặc hết mỹ nữ) = có trong daily_done
MORE_LABEL = "Greet Champion (more)"


def greet_key(n: int) -> str:
    """Key daily_done: đã bấm Greet lần thứ `n` hôm nay (đếm lần chào của bot, vì màn game chỉ cho biết 10/10)."""
    return f"{KEY}_greet_{n}"
