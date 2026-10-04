"""
constants.py — ảnh của nhiệm vụ Daily Activities "Patrol" (thư mục ảnh ActivitiesPatrol/).
"""
from ..constants import ROOT, OPEN

KEY = "daily_patrol"   # key nhiệm vụ trong bot/worker/priority.json
LABEL = "Patrol"   # ô tích ở tab Daily Activities, key daily_done
FOLDER = "ActivitiesPatrol"
FOLDER_PATH = f"{ROOT}/{FOLDER}"
# Ảnh "đã xong" (thấy là nhiệm vụ hôm nay xong).
DONE_IMAGES = ("PatrolFinishCurrent.png", "PatrolFinish.png", )
# (ảnh, action) theo thứ tự ưu tiên. Action chung (OPEN / TAP / ...) do common.run_task xử lý,
# action riêng (chuỗi) chuyển cho run.handle.
ACTIONS = (
    ("Patrol1.png", "patrol"),
    ("Patrol.png", "patrol_button"),
    ("ActivitiesPatrol.png", OPEN),
)
