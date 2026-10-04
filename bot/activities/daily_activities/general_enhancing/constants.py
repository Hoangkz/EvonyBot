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
