"""
constants.py — ảnh của nhiệm vụ Daily Activities "Material Composing" (thư mục ảnh ActivitiesComposeMaterials/).
"""
from ..constants import ROOT

KEY = "daily_material_composing"   # key nhiệm vụ trong bot/worker/priority.py
LABEL = "Material Composing"   # ô tích ở tab Daily Activities, key daily_done
FOLDER = "ActivitiesComposeMaterials"
FOLDER_PATH = f"{ROOT}/{FOLDER}"

# ---- Luồng mới sau Go (run.after_go) ------------------------------------------------------------------
# Ảnh đo trên máy 21913 (396x704), ảnh chụp 1.png .. 3.1.png do người dùng gửi:
# 1. Go -> màn Items (tab Equipment). Vật phẩm có mũi tên xanh hướng lên ở góc dưới trái ô = ghép được. Nhận bằng MÀU (nền ô
#    đổi theo phẩm chất nên ảnh mẫu không đáng tin): điểm ảnh xanh lá (H 30..50, S > 150, V > 130), khối ~14x14 (diện tích
#    100..150). Chọn mũi tên có y nhỏ nhất (cùng hàng thì x nhỏ nhất), bấm ô = mũi tên + ITEM_TAP_OFFSET.
# 2. Chọn ô -> panel mô tả hiện nút "Compose" nhỏ (ComposeSmall, tâm (315, 443)) -> bấm.
# 3. Màn Compose (tiêu đề ComposeTitle): nút Compose lớn dưới trái (tâm (100, 676)) xanh = bấm được, xám = hết nguyên liệu
#    (độ bão hoà màu 204 so với 9). Bấm đủ COMPOSE_GOAL lần thì xong; xám -> Back 2 lần, chọn vật phẩm khác, bấm nốt phần còn thiếu.
ITEMS_TITLE = f"{FOLDER_PATH}/ItemsTitle.png"
COMPOSE_TITLE = f"{FOLDER_PATH}/ComposeTitle.png"
COMPOSE_SMALL = f"{FOLDER_PATH}/ComposeSmall.png"
COMPOSE_BIG = f"{FOLDER_PATH}/ComposeBig.png"
COMPOSE_SMALL_REGION = (55, 56, 100, 70)   # % màn hình: nút Compose nhỏ của panel mô tả
COMPOSE_BIG_REGION = (0, 90, 50, 100)      # % màn hình: nút Compose lớn dưới trái màn Compose
LIST_REGION_Y = (215, 690)                 # px: vùng lưới vật phẩm (bỏ banner + thanh tab, đáy)
ARROW_HSV = ((30, 50), 150, 130)           # (khoảng H, S tối thiểu, V tối thiểu) của mũi tên xanh
ARROW_SIZE = (12, 17, 12, 16)              # (rộng min, rộng max, cao min, cao max)
ARROW_AREA = (90, 160)                     # diện tích khối màu
ROW_HEIGHT = 20                            # px: các mũi tên cách nhau < chừng này theo y coi là cùng hàng
ITEM_TAP_OFFSET = (21, -30)                # từ mũi tên tới tâm ô vật phẩm
SELECT_WAITS = 3                           # sau khi bấm ô: chờ 1 giây, chưa thấy Compose nhỏ thì chờ thêm tối đa chừng này lần
SELECT_TRIES = 3                           # số vật phẩm khác nhau thử chọn tối đa
SCROLLS = 3                                # số lần cuộn tối đa khi không có mũi tên xanh (thường không cần cuộn)
LIST_SWIPE = (50, 85, 50, 45)              # % màn hình: cuộn lưới vật phẩm xuống
COMPOSE_GOAL = 3                           # số lần bấm Compose để xong nhiệm vụ
COMPOSE_BOX = (30, 655, 158, 42)           # px (x, y, rộng, cao): khung nút Compose lớn để xét xanh / xám
COMPOSE_MIN_SATURATION = 100               # độ bão hoà HSV trung bình dưới mức này = nút xám
COMPOSE_WAIT = 2                           # giây chờ sau mỗi lần bấm Compose
MAX_ROUNDS = 6                             # số lần chọn lại vật phẩm tối đa (mỗi lần xám -> Back 2 lần -> chọn lại)
SCREEN_WAIT = 8                            # giây chờ màn Items sau Go
BACKS_AFTER = 4                            # xong: Back tối đa chừng này lần tới khi rời màn Items / Compose
