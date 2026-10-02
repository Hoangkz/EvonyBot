"""
constants.py — ảnh riêng của nhiệm vụ Train Troop (King's Path, Day 3). Màn Train /
Training Speedup dùng chung với Gather Troops: xem gather_troops/train_troop/constants.py.
"""
from ...gather_troops.troop_tier import tier_images
from ..constants import DAY_TABS, DAY_THRESHOLD, KP, TAB_THRESHOLD

# Ô chọn ở group King's Path: {"value": số lính, "day": 3}.
KEY = "kings_path_train_troop"
DAY = 3   # ngày mở nhiệm vụ (dùng khi settings thiếu "day")

# Tab "Day 3" chưa chọn (KP/Day/day3.png, ngưỡng 0,95).
DAY_3 = DAY_TABS[DAY]
# Tab phụ "Strong Troops" (thứ 1, bên trái), dòng nhiệm vụ "Train N Troop(s)".
TAB = f"{KP}/Tab/strongTroops.png"
TAB_SELECTED = f"{KP}/Tab/strongTroopsSelected.png"

# Go -> doanh trại (Barracks) như Ground Troop. Nhiệm vụ tính mọi cấp lính -> luôn train
# cấp I (rẻ, nhanh nhất). Ảnh cấp I, II cắt từ tests/event/kings_path/screens/train_t01.png.
TIERS = tier_images("Event/GatherTroops/GroundTroop/Tier")
LOWEST = 1

THRESHOLDS = {
    DAY_3: DAY_THRESHOLD,
    TAB: TAB_THRESHOLD,
    TAB_SELECTED: TAB_THRESHOLD,
}
