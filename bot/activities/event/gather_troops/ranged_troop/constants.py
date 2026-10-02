"""
constants.py — ảnh và ngưỡng riêng của nhiệm vụ Ranged Troop. Màn Train / Training
Speedup dùng chung: xem ../train_troop/constants.py.
"""
from ...constants import EV
from ..mounted_troop.constants import DAY_3, THRESHOLDS as MOUNTED_THRESHOLDS
from ..troop_tier import tier_images

# Ô chọn ở group Gather Troops (Day 3): {"value": số lính, "level": cấp lính, "day": 3}.
KEY = "ranged_troop"
DAY = 3   # ngày mở nhiệm vụ (dùng khi settings thiếu "day")
LOCKED_KEY = f"{KEY}_locked"   # giống TroopTask.locked_key

# ---- Màn Gather Troops ----------------------------------------------------
# Tab "Day 3": dùng chung ảnh với Mounted Troop (DAY_3, ngưỡng 0,97).
# Tab phụ "Ranged Troop" (Day 3, bên phải; bên trái là "Mounted Troop"), tâm (293, 252):
#   chưa chọn (RANGED_TROOP):          1,00 khi chưa chọn / 0,90 khi đã chọn
#   đang chọn (RANGED_TROOP_SELECTED): 1,00 khi đã chọn   / 0,91 khi chưa chọn
# -> cả hai ngưỡng 0,95, xét "đang chọn" trước. Màn khác <= 0,80 (tab Ground Troop của Day 2).
RANGED_TROOP = f"{EV}/GatherTroops/RangedTroop/rangedTroop.png"
RANGED_TROOP_SELECTED = f"{EV}/GatherTroops/RangedTroop/rangedTroopSelected.png"

# ---- Màn Train (trại cung - Archer Camp) -------------------------------------------
# Ảnh từng cấp lính cung (Event/GatherTroops/RangedTroop/Tier/<cấp>.png, I..XVI), cắt như ảnh
# lính bộ (36x26, phần dưới vòng tròn). Đo trên 18 ảnh: cùng cấp >= 0,76, cấp khác <= 0,58
# -> ngưỡng chung troop_tier.TIER_THRESHOLD (0,65).
TIERS = tier_images(f"{EV}/GatherTroops/RangedTroop/Tier")

THRESHOLDS = {
    DAY_3: MOUNTED_THRESHOLDS[DAY_3],
    RANGED_TROOP: 0.95,
    RANGED_TROOP_SELECTED: 0.95,
}
