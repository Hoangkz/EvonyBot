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
ACTIONS = (
    ("GemsLevyTimes.png", "levy_times"),
    ("Levy1.png", "levy_one"),
    ("Levy.png", "levy"),
    ("LevyGoldActivityCurrent.png", OPEN),
    ("LevyGoldActivity1.png", OPEN),
)
