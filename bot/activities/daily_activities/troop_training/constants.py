"""
constants.py — ảnh của nhiệm vụ Daily Activities "Troop Training" (thư mục ảnh ActivitiesTroopTrain/).
"""
from ..constants import ROOT, OPEN, TAP

KEY = "daily_troop_training"   # key nhiệm vụ trong bot/worker/priority.py
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

# ---- Luồng mới sau Go (run.after_go), giống King's Path Train Troop -------------------------------
# Go -> về thành, game kéo tới công trình train ngẫu nhiên 1 trong 4 loại lính (bộ / kỵ / cung / xe) ->
# bấm công trình -> menu (Train; đang train thì Speed Up -> Finish All trước, không tính) -> màn Train ->
# chọn cấp I -> KHÔNG nhập số: giữ số mặc định của ô (tối đa một lần train), số mẻ = ceil(TRAIN_GOAL /
# số mỗi mẻ) (lớn hơn TRAIN_GOAL cũng được) -> mỗi mẻ: Train -> Training Speedup -> (lần đầu Speedup
# Settings) Finish All. Code chung: ../train.py; ảnh / toạ độ màn Train: event/gather_troops/train_troop.
TRAIN_GOAL = 300        # số lính tối thiểu cần train (nhiệm vụ "Train 300 troops in the Main City")
