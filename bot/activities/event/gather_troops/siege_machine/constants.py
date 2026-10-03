"""
constants.py — ảnh và ngưỡng riêng của nhiệm vụ Siege Machine. Màn Train / Training
Speedup dùng chung: xem ../train_troop/constants.py.
"""
from ...constants import EV
from ..troop_tier import tier_images

# Ô chọn ở group Gather Troops (Day 4): {"value": số lính, "level": cấp lính, "day": 4}.
KEY = "gather_troops_siege_machine"
DAY = 4   # ngày mở nhiệm vụ (dùng khi settings thiếu "day")
LOCKED_KEY = f"{KEY}_locked"   # giống TroopTask.locked_key

# ---- Màn Gather Troops ----------------------------------------------------
# Tab "Day 4" chưa chọn, tâm (273, 209): khớp 1,00; khi Day 4 đang chọn 0,89 -> ngưỡng 0,95.
# (Màn Day 1..3 cũng khớp 1,00 — đúng, đó là tab cần bấm.)
DAY_4 = f"{EV}/GatherTroops/SiegeMachine/day4.png"
# Tab phụ "Siege Machine" (Day 4, bên trái; bên phải là "Defense Force"), tâm (102, 252):
#   chưa chọn (SIEGE_MACHINE):          1,00 khi chưa chọn / 0,89 khi đã chọn
#   đang chọn (SIEGE_MACHINE_SELECTED): 1,00 khi đã chọn   / 0,90 khi chưa chọn
# -> cả hai ngưỡng 0,95, xét "đang chọn" trước. Màn khác <= 0,50.
SIEGE_MACHINE = f"{EV}/GatherTroops/SiegeMachine/siegeMachine.png"
SIEGE_MACHINE_SELECTED = f"{EV}/GatherTroops/SiegeMachine/siegeMachineSelected.png"

# ---- Màn Train (xưởng - Workshop) ---------------------------------------------------
# Ảnh từng cấp xe công thành (Event/GatherTroops/SiegeMachine/Tier/<cấp>.png, I..XVI), cắt
# như ảnh lính bộ (36x26, phần dưới vòng tròn). Đo trên 16 ảnh: cùng cấp >= 0,78, cấp khác
# <= 0,60 -> ngưỡng chung troop_tier.TIER_THRESHOLD (0,65).
TIERS = tier_images(f"{EV}/GatherTroops/SiegeMachine/Tier")

THRESHOLDS = {
    DAY_4: 0.95,
    SIEGE_MACHINE: 0.95,
    SIEGE_MACHINE_SELECTED: 0.95,
}
