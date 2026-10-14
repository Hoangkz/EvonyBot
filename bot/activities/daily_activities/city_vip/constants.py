"""
constants.py — nhiệm vụ Daily "City VIP" (nhận VIP ở thành, chỉ được làm trong một khung giờ).
"""
LABEL = "City VIP"                  # tên trong log (không có ô tích ở UI)
KEY = "daily_city_vip"              # key nhiệm vụ trong bot/worker/priority.py
DONE_KEY = "City VIP: claimed"      # dấu "đã nhận hôm nay" trong daily_done (hết hạn ở lần reset server)
# Chỉ làm khi giờ máy tính nằm trong [WINDOW_START, WINDOW_END) giờ (0h đến 1h): ngoài khung giờ nhiệm vụ coi như không cần làm.
WINDOW_START = 0
WINDOW_END = 1

# ---- Nhận VIP: Tường thành -> hộp quà trên đầu tường -> màn "Server Gift" -> Claim All ------------------------------------
# Ảnh trong Images/DailyActivites/ActivitiesCityVip/, đo trên máy 21913 (396x704), tường ở giữa màn (goto walls: ảnh mẫu tại (246, 345)):
# - hộp quà nằm trên đầu tường (21913 civ1: tâm (226, 229); 21933 civ3: tâm (160, 317)), có hiệu ứng nên hình đổi theo thời gian, và NỀN
#   phía sau khác nhau theo civ. Nên ảnh mẫu chỉ cắt phần BÊN TRONG vòng tròn icon (22x22, không lấy nền) và cắt NHIỀU ảnh từ 60 khung
#   hình khác nhau (thư mục GiftBox/, chọn sao cho mỗi khung hình đều khớp một ảnh); trên 21933 khớp 0,89..0,99 (trung bình 0,95),
#   ngưỡng GIFT_THRESHOLD 0,8.
# - bấm tường 1 cái hiện menu (có Patrol, MENU_PATROL của King's Path), bấm lại cùng chỗ thì menu đóng. Chỉ làm khi chưa thấy hộp quà.
# - màn hộp quà: tiêu đề "Server Gift" (200, 23) 1,00 (màn khác 0,31), nút "Claim All" (198, 676) 1,00 (màn khác 0,37).
from ....common import images_in
from ..constants import ROOT

FOLDER_PATH = f"{ROOT}/ActivitiesCityVip"
GIFT_BOXES = images_in(f"{FOLDER_PATH}/GiftBox")   # mọi ảnh trong thư mục GiftBox/
GIFT_THRESHOLD = 0.8
# Chỉ tìm hộp quà trong vùng phía trên Tường thành: (dx, dy) góc trên trái và góc dưới phải so với vị trí tường trên màn (civ1: hộp quà cách
# tường (-20, -116); các màn tường civ khác còn có icon giống hộp quà ở chỗ khác, khớp tới 0,95).
GIFT_AREA = ((-140, -190), (70, -50))
SERVER_GIFT_TITLE = f"{FOLDER_PATH}/ServerGiftTitle.png"
CLAIM_ALL = f"{FOLDER_PATH}/ClaimAll.png"
CLAIM_ALL_FALLBACK = (198, 676)       # toạ độ nút Claim All khi không nhận ra ảnh
MENU_WAIT = 3                         # giây chờ menu tường (Patrol) hiện sau khi bấm tường
GIFT_FIND_CHECKS = 3                  # sau khi đóng menu tường: chụp tìm hộp quà tối đa chừng này lần (1 giây / lần)
GIFT_OPEN_CHECKS = 5                  # bấm hộp quà xong chờ 1 giây, chưa ra màn Server Gift thì chờ thêm tối đa chừng này lần (1 giây / lần)
GIFT_TRIES = 3                        # số lần bấm hộp quà tối đa
CLAIM_WAIT = 2                        # giây chờ sau khi bấm Claim All
CLAIM_ALL_WAIT = 3                    # giây chờ nút Claim All hiện trên màn Server Gift
