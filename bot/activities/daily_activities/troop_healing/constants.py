"""
constants.py — ảnh của nhiệm vụ Daily Activities "Troop Heading" (thư mục ảnh ActivitiesTroopHeal/).
"""
from ..constants import ROOT, OPEN, TAP

KEY = "daily_troop_heading"   # key nhiệm vụ trong bot/worker/priority.json
LABEL = "Troop Heading"   # ô tích ở tab Daily Activities, key daily_done
FOLDER = "ActivitiesTroopHeal"
FOLDER_PATH = f"{ROOT}/{FOLDER}"
# Ảnh "đã xong" (thấy là nhiệm vụ hôm nay xong).
DONE_IMAGES = ("HealFinish1.png", "HealFinish.png", )
# (ảnh, action) theo thứ tự ưu tiên. Action chung (OPEN / TAP / ...) do common.run_task xử lý,
# action riêng (chuỗi) chuyển cho run.handle.
ACTIONS = (
    ("HealFinishAll.png", "heal_all"),
    ("HealSelect.png", "select"),
    ("Heal-i.png", "heal_info"),
    ("Heal.png", TAP),
    ("HealActivity.png", OPEN),
)
