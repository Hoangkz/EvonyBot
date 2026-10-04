"""
constants.py — ảnh của nhiệm vụ Daily Activities "Trap Buiding" (thư mục ảnh ActivitiesBuildTrap/).
"""
from ..constants import ROOT, OPEN, TAP

KEY = "daily_trap_buiding"   # key nhiệm vụ trong bot/worker/priority.json
LABEL = "Trap Buiding"   # ô tích ở tab Daily Activities, key daily_done
FOLDER = "ActivitiesBuildTrap"
FOLDER_PATH = f"{ROOT}/{FOLDER}"
# Ảnh "đã xong" (thấy là nhiệm vụ hôm nay xong).
DONE_IMAGES = ("TrapFinish1.png", "TrapFinish.png", )
# (ảnh, action) theo thứ tự ưu tiên. Action chung (OPEN / TAP / ...) do common.run_task xử lý,
# action riêng (chuỗi) chuyển cho run.handle.
ACTIONS = (
    ("TrapSpeed.png", "speed"),
    ("Trap-i.png", "build"),
    ("BuildInterface.png", "interface"),
    ("Build.png", TAP),
    ("ActivitiesBuildTrap1.png", OPEN),
)
