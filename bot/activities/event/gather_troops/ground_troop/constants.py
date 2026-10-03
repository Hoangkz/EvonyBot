"""
constants.py — ảnh và ngưỡng riêng của nhiệm vụ Ground Troop. Màn Train / Training
Speedup dùng chung: xem ../train_troop/constants.py.
"""
from ...constants import EV
from ..troop_tier import tier_images

# Ô chọn ở group Gather Troops (Day 2): {"value": số lính, "level": cấp lính, "day": 2}.
KEY = "gather_troops_ground_troop"
DAY = 2   # ngày mở nhiệm vụ (dùng khi settings thiếu "day")
# Lưu trong daily_done khi tab Day của nhiệm vụ còn khoá: bỏ qua nhiệm vụ tới lần reset
# server kế tiếp (ngày mới mở theo reset). Giống TroopTask.locked_key.
LOCKED_KEY = f"{KEY}_locked"

# ---- Màn Gather Troops ----------------------------------------------------
# Tab "Day 2" chưa chọn, tâm (121, 209): khớp 0,98; khi Day 2 đang chọn 0,87 -> ngưỡng 0,93.
# (Màn Gather Troops Day 1 khác cũng khớp 0,98 — đúng, đó là tab cần bấm.)
DAY_2 = f"{EV}/GatherTroops/GroundTroop/day2.png"
# Tab phụ "Ground Troop" (Day 2), tâm (292, 253). Hai ảnh chỉ khác độ sáng chữ:
#   chưa chọn (GROUND_TROOP):          1,00 khi chưa chọn / 0,90 khi đã chọn
#   đang chọn (GROUND_TROOP_SELECTED): 1,00 khi đã chọn   / 0,91 khi chưa chọn
# -> cả hai ngưỡng 0,95, xét "đang chọn" trước. Màn khác <= 0,80.
GROUND_TROOP = f"{EV}/GatherTroops/GroundTroop/groundTroop.png"
GROUND_TROOP_SELECTED = f"{EV}/GatherTroops/GroundTroop/groundTroopSelected.png"

# ---- Màn Train (doanh trại) ------------------------------------------------------
# Ảnh từng cấp lính bộ (Event/GatherTroops/GroundTroop/Tier/<cấp>.png, hiện có III..XV), xem
# gather_troops/troop_tier.py. Thấy bất kỳ cấp nào trên hàng cấp lính = đang ở màn Train.
TIERS = tier_images(f"{EV}/GatherTroops/GroundTroop/Tier")

THRESHOLDS = {
    DAY_2: 0.93,
    GROUND_TROOP: 0.95,
    GROUND_TROOP_SELECTED: 0.95,
}
