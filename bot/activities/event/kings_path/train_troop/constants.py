"""
constants.py — ảnh riêng của nhiệm vụ Train Troop (King's Path, Day 3). Màn Train /
Training Speedup dùng chung với Gather Troops: xem gather_troops/train_troop/constants.py.
"""
from ..constants import DAY_TABS, DAY_THRESHOLD, KP, TAB_THRESHOLD

# Ô chọn ở group King's Path: {"value": số lính, "day": 3}.
KEY = "kings_path_train_troop"
DAY = 3   # ngày mở nhiệm vụ (dùng khi settings thiếu "day")

# Tab "Day 3" chưa chọn (KP/Day/day3.png, ngưỡng 0,95).
DAY_3 = DAY_TABS[DAY]
# Tab phụ "Strong Troops" (thứ 1, bên trái), dòng nhiệm vụ "Train N Troop(s)".
TAB = f"{KP}/Tab/strongTroops.png"
TAB_SELECTED = f"{KP}/Tab/strongTroopsSelected.png"

# Go -> game mở ngẫu nhiên công trình train của 1 trong 4 loại lính (bộ / kỵ / cung / xe).
# Nhiệm vụ tính mọi cấp lính -> luôn train cấp I (rẻ, nhanh nhất): ảnh cấp I của cả 4 loại, loại
# nào thấy trước cũng được (troop_tier.choose_first_tier vuốt hàng cấp sang trái tới khi thấy).
KINDS = ("GroundTroop", "MountedTroop", "RangedTroop", "SiegeMachine")
TIERS = {1: [f"Event/GatherTroops/{kind}/Tier/1.png" for kind in KINDS]}
# Nhận ra màn Train (mở ở loại / cấp bất kỳ, VD trường bắn cấp IV — train_ranged_t04.png): nút "i"
# tròn góc trên (320, 45), giống nhau ở mọi màn Train: 50 màn Train (cả bẫy) 1,00; màn khác <= 0,36.
# Chỉ tìm trong vùng góc trên phải (% màn hình).
TRAIN_INFO = "Event/GatherTroops/Train/info.png"
TRAIN_INFO_REGION = (70, 2, 91, 12)
# Chọn cấp I (tier.py): vuốt hàng cấp sang trái (ngón tay kéo trái -> phải, % màn hình; hàng ở
# y ~452 = 64%) về phía cấp I, sau mỗi lần vuốt chờ rồi kiểm tra; tối đa FIRST_TIER_SWIPES lần.
# Cấp I hiện trên hàng: ảnh cấp I khớp 0,98 .. 1,00; chỉ có cấp cao hơn: <= 0,46.
FIRST_TIER_SWIPE = (15, 64, 90, 64)
FIRST_TIER_SWIPES = 6
FIRST_TIER_SWIPE_WAIT = 2
LOWEST = 1

THRESHOLDS = {
    DAY_3: DAY_THRESHOLD,
    TAB: TAB_THRESHOLD,
    TAB_SELECTED: TAB_THRESHOLD,
}
