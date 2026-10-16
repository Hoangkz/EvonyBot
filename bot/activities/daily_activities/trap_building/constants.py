"""
constants.py — ảnh của nhiệm vụ Daily Activities "Trap Buiding" (thư mục ảnh ActivitiesBuildTrap/).
"""
from ..constants import ROOT

KEY = "daily_trap_buiding"   # key nhiệm vụ trong bot/worker/priority.py
LABEL = "Trap Buiding"   # ô tích ở tab Daily Activities, key daily_done
FOLDER = "ActivitiesBuildTrap"
FOLDER_PATH = f"{ROOT}/{FOLDER}"

# ---- Luồng mới sau Go (run.after_go), giống Gather Troops Trap Factory (xây bẫy) -------------------
# Go -> về thành, Trap Factory ở giữa -> bấm -> menu "Build" (đang xây thì "Speed Up" -> Finish All trước)
# -> màn Train bẫy -> KHÔNG chọn loại / cấp: bẫy đang hiện khi vào -> không nhập số (số mặc định của ô)
# -> số mẻ = ceil(TRAP_GOAL / số mỗi mẻ) (mỗi mẻ >= 150 thì 1 mẻ, lớn hơn cũng được; nhỏ hơn thì nhiều mẻ)
# -> mỗi mẻ: Build -> Trap Building Speedup -> (lần đầu Speedup Settings) Finish All -> xong hôm nay.
# Code chung: ../train.py.
TRAP_GOAL = 150         # nhiệm vụ "Build 150 traps"
