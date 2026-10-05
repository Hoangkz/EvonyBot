"""
constants.py — ảnh của nhiệm vụ Daily Activities "General Enhancing" (thư mục ảnh ActivitiesGeneralEnhancing/).
"""
from ..constants import ROOT, OPEN

KEY = "daily_general_enhancing"   # key nhiệm vụ trong bot/worker/priority.json
LABEL = "General Enhancing"   # ô tích ở tab Daily Activities, key daily_done
FOLDER = "ActivitiesGeneralEnhancing"
FOLDER_PATH = f"{ROOT}/{FOLDER}"
# Ảnh "đã xong" (thấy là nhiệm vụ hôm nay xong).
DONE_IMAGES = ("CultivateFinishCurrent.png", "CultivateFinish.png", )
# (ảnh, action) theo thứ tự ưu tiên. Action chung (OPEN / TAP / ...) do common.run_task xử lý,
# action riêng (chuỗi) chuyển cho run.handle.
ACTIONS = (
    ("Cultivate1.png", "cultivate_loop"),
    ("Cultivate.png", "cultivate"),
    ("ActivitiesGeneralEnhancing.png", OPEN),
)
AFTER_OPEN_TAP = (30, 50)   # sau Go: bấm chỗ này (% màn hình)

# ---- Luồng mới sau Go (run.after_go), như Gather Troops Cultivate Generals nhưng Gold Cultivate -----------
# Nhiệm vụ "Cultivate Generals for 5 time(s)". Go -> danh sách Generals -> tim lọc yêu thích (ảnh / bước của
# event/gather_troops/cultivate_generals) -> kéo xuống cuối -> tướng cuối -> "Cultivate" -> màn Cultivate (giao diện
# cũ, máy 21943: Gems Cultivate / Gold Cultivate + thanh Quick Cultivate) -> "Gold Cultivate" (6000 vàng, không tốn
# kim cương) -> kết quả Cancel / Confirm -> Cancel (bỏ kết quả như Event) -> lặp CULTIVATE_GOAL lần.
# Ảnh đo trên tests/daily_activities/general_enhancing/screens/ (396x704):
# - chữ "Gold Cultivate" (287, 660): 1,00 trên màn Cultivate; màn khác <= 0,63 (Quick Cultivate 0,63).
# - nút "Cancel" (108, 669) sau khi cultivate: 1,00; Cancel của popup khác cũng 0,96 .. 1,00 -> chỉ tìm ở góc dưới
#   trái (CANCEL_REGION) và chỉ sau khi vừa bấm Gold Cultivate.
# - tim lọc chưa tích của giao diện cũ chỉ khớp ảnh Event 0,86 -> ngưỡng FAVORITE_OFF_THRESHOLD.
GOLD_CULTIVATE = f"{FOLDER_PATH}/GoldCultivate.png"
CULTIVATE_CANCEL = f"{FOLDER_PATH}/CultivateCancel.png"
CANCEL_REGION = (0, 88, 50, 100)        # % màn hình
FAVORITE_OFF_THRESHOLD = 0.8
CULTIVATE_GOAL = 5
RESULT_WAIT = 5         # giây chờ kết quả (nút Cancel) sau khi bấm Gold Cultivate
MAX_STEPS = 40
BACKS_AFTER = 3         # xong: Back (màn Cultivate -> màn tướng -> danh sách -> thành)
