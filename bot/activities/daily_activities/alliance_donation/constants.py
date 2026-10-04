"""
constants.py — ảnh của nhiệm vụ Daily Activities "Alliance Donation" (thư mục ảnh ActivitiesDonateAlliance/).
"""
from ..constants import ROOT, OPEN

KEY = "daily_alliance_donation"   # key nhiệm vụ trong bot/worker/priority.json
LABEL = "Alliance Donation"   # ô tích ở tab Daily Activities, key daily_done
FOLDER = "ActivitiesDonateAlliance"
FOLDER_PATH = f"{ROOT}/{FOLDER}"
# Ảnh "đã xong" (thấy là nhiệm vụ hôm nay xong).
DONE_IMAGES = ("AllianceDonateFinish1.png", "AllianceDonateFinish.png", )
# (ảnh, action) theo thứ tự ưu tiên. Action chung (OPEN / TAP / ...) do common.run_task xử lý,
# action riêng (chuỗi) chuyển cho run.handle.
ACTIONS = (
    ("AllianceCapacity.png", "donate"),
    ("ActivitiesDonateAlliance1.png", OPEN),
)
