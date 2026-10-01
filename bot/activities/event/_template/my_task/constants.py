"""
constants.py — ảnh, ngưỡng và action riêng của nhiệm vụ <tên nhiệm vụ>.
"""
from ...constants import EV, THRESHOLDS as EVENT_THRESHOLDS

KEY = "my_task"   # key trong ui/tabs/event.json / settings

# ---- Màn <...> ------------------------------------------------------------------
# Mỗi ảnh ghi kèm điểm khớp đo được (skill template-images): đúng màn / màn khác.
# Hai ảnh "đang chọn" / "chưa chọn" khớp chéo cao -> ngưỡng 0,95, xét "đang chọn" trước.
# (Mẫu dùng tạm tab "Recruit More" của Gather Troops để test mẫu chạy được — đổi khi copy.)
TAB = f"{EV}/GatherTroops/recruitMore.png"
TAB_SELECTED = f"{EV}/GatherTroops/recruitMoreSelected.png"

THRESHOLDS = {
    **EVENT_THRESHOLDS,
    TAB_SELECTED: 0.95,
}
REGIONS = {
    # ảnh: (x1, y1, x2, y2) % màn hình
}

# ---- Actions --------------------------------------------------------------------
OPEN_TAB = "open_tab"   # tab chưa chọn -> bấm
ON_TAB = "on_tab"       # tab đang chọn -> làm nhiệm vụ
