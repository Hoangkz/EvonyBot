"""
constants.py — ảnh và ngưỡng riêng của nhiệm vụ Defense Force (xây bẫy). Màn Train /
Training Speedup dùng chung: xem ../train_troop/constants.py.
"""
from ...constants import EV
from ..siege_machine.constants import DAY_4, THRESHOLDS as SIEGE_THRESHOLDS
from ..troop_tier import kind_images

# Ô chọn ở group Gather Troops (Day 4): {"value": số bẫy, "level": cấp bẫy, "day": 4}.
KEY = "defense_force"
DAY = 4   # ngày mở nhiệm vụ (dùng khi settings thiếu "day")
LOCKED_KEY = f"{KEY}_locked"   # giống TroopTask.locked_key
LOWEST_LEVEL = 3   # nhiệm vụ chỉ tính "level 3 and above Trap(s)"

# ---- Màn Gather Troops ----------------------------------------------------
# Tab "Day 4": dùng chung ảnh với Siege Machine (DAY_4, ngưỡng 0,95).
# Tab phụ "Defense Force" (Day 4, bên phải; bên trái là "Siege Machine"), tâm (293, 252):
#   chưa chọn (DEFENSE_FORCE):          1,00 khi chưa chọn / 0,90 khi đã chọn
#   đang chọn (DEFENSE_FORCE_SELECTED): 1,00 khi đã chọn   / 0,91 khi chưa chọn
# -> cả hai ngưỡng 0,95, xét "đang chọn" trước. (Tab phụ bên phải của Day 3 cũng giống hệt
# vị trí nhưng khác chữ.)
DEFENSE_FORCE = f"{EV}/GatherTroops/DefenseForce/defenseForce.png"
DEFENSE_FORCE_SELECTED = f"{EV}/GatherTroops/DefenseForce/defenseForceSelected.png"

# ---- Thành: xưởng bẫy (Trap Factory) -------------------------------------------------
# Menu Trap Factory không có "Train" mà có "Build" (búa + chữ, (100, 233)): khớp 1,00; màn
# khác <= 0,32. Đang xây bẫy thì menu có "Speed Up" như các công trình khác (0,89).
BUILD = f"{EV}/GatherTroops/DefenseForce/build.png"
# Tiêu đề "Trap Building Speedup" (ảnh "Training Speedup" chỉ khớp 0,85): 1,00; màn speedup
# của lính 0,73; màn khác thấp hơn. Màn này giống hệt màn Training Speedup (Speedup
# Settings, Finish All).
SPEEDUP_TITLE = f"{EV}/GatherTroops/DefenseForce/speedupTitle.png"

# ---- Màn Train bẫy -------------------------------------------------------------------
# Mỗi cấp 4 loại bẫy liền nhau trên hàng: Trap, Rock, Abatis, Fire Arrow (loại nào cũng
# được). Ảnh Event/GatherTroops/DefenseForce/Tier/<cấp>_<loại>.png (I..VII), cắt như ảnh
# lính (36x26). Các loại cùng cấp khớp chéo tới 0,83 (troop_tier lấy ảnh khớp cao nhất,
# luôn đúng loại); cấp khác <= 0,65.
KINDS = ["trap", "rock", "abatis", "fireArrow"]
TIERS = kind_images(f"{EV}/GatherTroops/DefenseForce/Tier", KINDS)

THRESHOLDS = {
    DAY_4: SIEGE_THRESHOLDS[DAY_4],
    DEFENSE_FORCE: 0.95,
    DEFENSE_FORCE_SELECTED: 0.95,
}
