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

# ---- Luồng mới sau Go (run.after_go), giống Gather Troops Defense Force (xây bẫy) -------------------
# Go -> về thành, Trap Factory ở giữa -> bấm -> menu "Build" (đang xây thì "Speed Up" -> Finish All trước)
# -> màn Train bẫy -> KHÔNG chọn loại / cấp: bẫy đang hiện khi vào -> không nhập số (số mặc định của ô)
# -> số mẻ = ceil(TRAP_GOAL / số mỗi mẻ) (mỗi mẻ >= 150 thì 1 mẻ, lớn hơn cũng được; nhỏ hơn thì nhiều mẻ)
# -> mỗi mẻ: Build -> Trap Building Speedup -> (lần đầu Speedup Settings) Finish All -> xong hôm nay.
# Code chung: ../train.py.
TRAP_GOAL = 150         # nhiệm vụ "Build 150 traps"
