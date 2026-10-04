"""
constants.py — ảnh của nhiệm vụ Daily Activities "Troop Training" (thư mục ảnh ActivitiesTroopTrain/).
"""
from ..constants import ROOT, OPEN, TAP

KEY = "daily_troop_training"   # key nhiệm vụ trong bot/worker/priority.json
LABEL = "Troop Training"   # ô tích ở tab Daily Activities, key daily_done
FOLDER = "ActivitiesTroopTrain"
FOLDER_PATH = f"{ROOT}/{FOLDER}"
# Ảnh "đã xong" (thấy là nhiệm vụ hôm nay xong).
DONE_IMAGES = ("TroopFinish.png", "TroopFinish1.png", )
# (ảnh, action) theo thứ tự ưu tiên. Action chung (OPEN / TAP / ...) do common.run_task xử lý,
# action riêng (chuỗi) chuyển cho run.handle.
ACTIONS = (
    ("TroopSpeed.png", "speed"),
    ("TrainSoldierSelectedCurrent.png", "soldier"),
    ("TrainSoldierCurrent.png", "soldier"),
    ("TrainSoldier1.png", "soldier"),
    ("TrainInterface.png", "interface"),
    ("Train.png", TAP),
    ("TrainTroop.png", OPEN),
)
