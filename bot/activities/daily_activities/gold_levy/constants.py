"""
constants.py — ảnh của nhiệm vụ Daily Activities "Gold Levy" (thư mục ảnh ActivitiesLevyGold/).
"""
from ..constants import ROOT, OPEN

KEY = "daily_gold_levy"   # key nhiệm vụ trong bot/worker/priority.json
LABEL = "Gold Levy"   # ô tích ở tab Daily Activities, key daily_done
FOLDER = "ActivitiesLevyGold"
FOLDER_PATH = f"{ROOT}/{FOLDER}"
# Ảnh "đã xong" (thấy là nhiệm vụ hôm nay xong).
DONE_IMAGES = ("LevyGoldFinish.png", "LevyGoldFinish1.png", )
# (ảnh, action) theo thứ tự ưu tiên. Action chung (OPEN / TAP / ...) do common.run_task xử lý,
# action riêng (chuỗi) chuyển cho run.handle.
# Sau Go: về thành, Thành chính (Keep) ở giữa -> common bấm giữa -> menu tròn, icon "Levy" (Levy.png 0,94)
# -> popup Levy -> "Free Levy All" (vàng, FreeLevyAll.png) -> bấm -> xong. Hết lượt free thì nút xám
# (FreeLevyAllDone.png) -> cũng xong. Hai ảnh khớp chéo 0,88 (< ngưỡng 0,9), ảnh đúng 1,00; màn khác
# <= 0,44 (đo trên tests/daily_activities/gold_levy/screens/07, 08). Không dùng Gems Levy (tốn kim cương).
ACTIONS = (
    ("FreeLevyAll.png", "levy_all"),
    ("FreeLevyAllDone.png", "levy_done"),
    ("Levy.png", "levy"),
    ("LevyGoldActivityCurrent.png", OPEN),
    ("LevyGoldActivity1.png", OPEN),
)
LEVY_ALL_WAIT = 3       # giây chờ sau khi bấm Free Levy All
POPUP_WAIT = 10         # luồng mới (run.after_go): giây chờ tối đa popup Levy sau khi bấm icon "Levy"
BACKS_AFTER_LEVY = 3    # xong: Back (tối đa chừng này lần) tới khi popup Levy đóng
