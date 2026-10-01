"""
constants.py — ảnh và ngưỡng riêng của nhiệm vụ Mounted Troop. Màn Train / Training
Speedup dùng chung: xem ../train_troop/constants.py.
"""
from ...constants import EV
from ..troop_tier import tier_images

# Ô chọn ở group Gather Troops (Day 3): {"value": số lính, "level": cấp lính, "day": 3}.
KEY = "mounted_troop"
DAY = 3   # ngày mở nhiệm vụ (dùng khi settings thiếu "day")
LOCKED_KEY = f"{KEY}_locked"   # giống TroopTask.locked_key

# ---- Màn Gather Troops ----------------------------------------------------
# Tab "Day 3" chưa chọn, tâm (197, 209): khớp 1,00; khi Day 3 đang chọn 0,94 -> ngưỡng 0,97.
# (Màn Day 1 / Day 2 cũng khớp 1,00 — đúng, đó là tab cần bấm.)
DAY_3 = f"{EV}/GatherTroops/MountedTroop/day3.png"
# Tab phụ "Mounted Troop" (Day 3, bên trái; bên phải là "Ranged Troop"), tâm (102, 252):
#   chưa chọn (MOUNTED_TROOP):          1,00 khi chưa chọn / 0,89 khi đã chọn
#   đang chọn (MOUNTED_TROOP_SELECTED): 1,00 khi đã chọn   / 0,90 khi chưa chọn
# -> cả hai ngưỡng 0,95, xét "đang chọn" trước. Màn khác <= 0,67.
MOUNTED_TROOP = f"{EV}/GatherTroops/MountedTroop/mountedTroop.png"
MOUNTED_TROOP_SELECTED = f"{EV}/GatherTroops/MountedTroop/mountedTroopSelected.png"

# ---- Màn Train (chuồng ngựa - Stables) ----------------------------------------------
# Ảnh từng cấp lính kỵ (Event/GatherTroops/MountedTroop/Tier/<cấp>.png, I..XV), cắt như ảnh
# lính bộ (36x26, phần dưới vòng tròn). Đo trên 17 ảnh: cùng cấp >= 0,73 (vòng sát mép),
# cấp khác <= 0,60 -> ngưỡng chung troop_tier.TIER_THRESHOLD (0,65).
TIERS = tier_images(f"{EV}/GatherTroops/MountedTroop/Tier")

THRESHOLDS = {
    DAY_3: 0.97,
    MOUNTED_TROOP: 0.95,
    MOUNTED_TROOP_SELECTED: 0.95,
}
