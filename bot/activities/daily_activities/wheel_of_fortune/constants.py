"""
constants.py — ảnh của nhiệm vụ Daily Activities "Wheel of Fortune" (thư mục ảnh ActivitiesWheelofFortune/).
"""
from ..constants import ROOT

KEY = "daily_wheel_of_fortune"   # key nhiệm vụ trong bot/worker/priority.py
LABEL = "Wheel of Fortune"   # ô tích ở tab Daily Activities, key daily_done
FOLDER = "ActivitiesWheelofFortune"
FOLDER_PATH = f"{ROOT}/{FOLDER}"

# ---- Luồng mới sau Go (run.after_go), như King's Path Wheel sau Go ---------------------------------
# Go -> game mở thẳng màn Wheel of Fortune -> event/kings_path/wheel spin_wheel: "100 Spins" nếu có (-> Back), không
# thì "10 Spins" SPINS_10_GOAL lần -> Back -> xong hôm nay. Nhiệm vụ Daily chỉ cần 1 lần 10 Spins: không quay tới hết
# chip như King's Path, không vào Purchase Chips (hết chip ngay lần đầu thì game vẫn mở Purchase Chips -> Back, xong).
SPINS_10_GOAL = 1
