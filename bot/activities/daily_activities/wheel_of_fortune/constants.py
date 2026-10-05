"""
constants.py — ảnh của nhiệm vụ Daily Activities "Wheel of Fortune" (thư mục ảnh ActivitiesWheelofFortune/).
"""
from ..constants import ROOT, OPEN

KEY = "daily_wheel_of_fortune"   # key nhiệm vụ trong bot/worker/priority.json
LABEL = "Wheel of Fortune"   # ô tích ở tab Daily Activities, key daily_done
FOLDER = "ActivitiesWheelofFortune"
FOLDER_PATH = f"{ROOT}/{FOLDER}"
# Ảnh "đã xong" (thấy là nhiệm vụ hôm nay xong).
DONE_IMAGES = ("SpinFinishCurrent.png", "SpinFinish.png", )
# (ảnh, action) theo thứ tự ưu tiên. Action chung (OPEN / TAP / ...) do common.run_task xử lý,
# action riêng (chuỗi) chuyển cho run.handle.
ACTIONS = (
    ("WheelofFortune.png", "spin"),
    ("ActivitiesWheelofFortune.png", OPEN),
)
AFTER_OPEN_TAP = None   # sau Go: không bấm thêm

# ---- Luồng mới sau Go (run.after_go), giống hệt King's Path Wheel sau Go ---------------------------
# Go -> game mở thẳng màn Wheel of Fortune -> event/kings_path/wheel spin_wheel: "100 Spins" nếu có (-> Back), không
# thì "10 Spins" liên tục tới khi hết chip (game mở Purchase Chips -> Back) -> xong hôm nay.
