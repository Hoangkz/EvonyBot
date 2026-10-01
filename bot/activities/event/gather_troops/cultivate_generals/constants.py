"""
constants.py — ảnh, ngưỡng và action riêng của nhiệm vụ Cultivate Generals.
"""
from .....common import images_in
from ...constants import EV, THRESHOLDS as EVENT_THRESHOLDS

KEY = "gather_troops_cultivate_generals"

# ---- Màn Gather Troops ----------------------------------------------------
# Tab "Recruit More" (Day 1). Hai ảnh chỉ khác độ sáng chữ nên khớp chéo khá cao:
#   đang chọn (RECRUIT_MORE_SELECTED): 1,00 khi chọn / 0,90 khi chưa chọn -> ngưỡng 0,95
#   chưa chọn (RECRUIT_MORE):          0,95 khi chưa chọn / 0,87 khi chọn
# -> xét ảnh "đang chọn" trước; không thấy mới xét ảnh "chưa chọn" (ngưỡng mặc định 0,9).
RECRUIT_MORE = f"{EV}/GatherTroops/CultivateGenerals/recruitMore.png"
RECRUIT_MORE_SELECTED = f"{EV}/GatherTroops/CultivateGenerals/recruitMoreSelected.png"
# Tổng số lần cultivate cần đạt cho cả nhiệm vụ: dòng Go ghi "300 / 500" -> đã làm 300,
# còn thiếu TOTAL - 300 = 700 (7 lần bấm Cultivate x100); đạt TOTAL thì xong.
TOTAL = 1000

# ---- Màn danh sách Generals (sau khi bấm Go) --------------------------------
# Trái tim lọc tướng yêu thích (dùng chung ảnh với Join Boss): đã tích = đỏ. Trên màn
# Generals khớp 0,99 tại (139, 208); tim trên từng thẻ tướng không khớp. Chỉ tìm ở hàng
# bộ lọc cho chắc.
FAVORITE_ON = "JoinBoss/favoriteOn.png"
FAVORITE_OFF = "JoinBoss/favoriteOff.png"
FAVORITE_REGION = (25, 25, 45, 35)          # % màn hình: quanh (139, 208)
# Kéo nhanh danh sách xuống cuối: 6 lần, ngón tay kéo lên thật nhanh.
LIST_FLING = (50, 85, 50, 15)               # % màn hình
LIST_FLING_TIMES = 6
LIST_FLING_DURATION = 0.1                   # giây
# Thẻ tướng cuối danh sách: bấm tại % màn hình; cắt quanh điểm này một ảnh nhỏ (giữ
# trong RAM) rồi chờ tối đa GENERAL_OPEN_WAIT giây cho tới khi ảnh đó biến mất (màn đổi).
LAST_GENERAL = (10, 90)                     # % màn hình
GENERAL_PATCH = 40                          # px, cạnh ảnh nhỏ
GENERAL_OPEN_WAIT = 15                      # giây

# ---- Màn chi tiết tướng -------------------------------------------------------
# Nút "Cultivate" ở hàng nút đáy, có 2 loại tuỳ tướng (mỗi mẫu trong thư mục, tìm cả hai):
#   1.png: hàng 3 nút (Enhance / Cultivate / Covenant), chữ lớn, tâm (200, 677)
#   2.png: hàng 4 nút (thêm Specialty), chữ nhỏ, tâm (152, 677)
# Mỗi mẫu khớp 1,00 trên loại của nó, loại kia <= 0,36. Màn Cultivate có "Cultivate Once"
# / "Quick Cultivate" (y 457) giống chữ -> chỉ tìm ở hàng nút đáy (ở đó <= 0,32).
CULTIVATE_BUTTONS = images_in(f"{EV}/GatherTroops/CultivateGenerals/CultivateButton")
CULTIVATE_REGION = (25, 92, 70, 100)        # % màn hình

# ---- Màn Cultivate ----------------------------------------------------------------
# Tab "Quick Cultivate" (màn Cultivate mở ra ở tab "Cultivate Once"). Hai ảnh chỉ khác độ
# sáng chữ nên khớp chéo 0,90 -> cả hai ngưỡng 0,95, xét "đang chọn" trước:
#   chưa chọn (QUICK_CULTIVATE):          1,00 khi chưa chọn / 0,90 khi đã chọn
#   đang chọn (QUICK_CULTIVATE_SELECTED): 1,00 khi đã chọn   / 0,90 khi chưa chọn
QUICK_CULTIVATE = f"{EV}/GatherTroops/CultivateGenerals/quickCultivate.png"
QUICK_CULTIVATE_SELECTED = f"{EV}/GatherTroops/CultivateGenerals/quickCultivateSelected.png"
# Ở tab Quick Cultivate có 1 trong 2 nút ở góc dưới trái (tìm trên cùng ảnh chụp):
#   "Cultivate x100" (2000 gems), tâm (100, 642): bấm -> +100 lần, nút đổi thành Cancel.
#   "Cancel" (kết quả vừa cultivate, cạnh Confirm), tâm (99, 648): bấm để bỏ kết quả.
# Màn khác: x100 <= 0,61 (tab Cultivate Once), Cancel <= 0,63.
CULTIVATE_X100 = f"{EV}/GatherTroops/CultivateGenerals/cultivateX100.png"
CANCEL = f"{EV}/GatherTroops/CultivateGenerals/cancel.png"
QUICK_BUTTON_REGION = (0, 85, 50, 100)      # % màn hình: góc dưới trái
CULTIVATE_X100_TIMES = 100                  # số lần cultivate của mỗi lần bấm x100
X100_WAIT = 10                              # giây chờ nút x100 đổi thành Cancel

THRESHOLDS = {
    **EVENT_THRESHOLDS,
    RECRUIT_MORE_SELECTED: 0.95,
    QUICK_CULTIVATE: 0.95,
    QUICK_CULTIVATE_SELECTED: 0.95,
}
REGIONS = {
    FAVORITE_ON: FAVORITE_REGION,
    FAVORITE_OFF: FAVORITE_REGION,
    **{path: CULTIVATE_REGION for path in CULTIVATE_BUTTONS},
    CULTIVATE_X100: QUICK_BUTTON_REGION,
    CANCEL: QUICK_BUTTON_REGION,
}

# ---- Actions --------------------------------------------------------------------
ON_RECRUIT_MORE = "on_recruit_more"         # tab Recruit More đang chọn
OPEN_RECRUIT_MORE = "open_recruit_more"     # tab Recruit More chưa chọn -> bấm
TICK_FAVORITE = "tick_favorite"             # danh sách Generals, tim lọc chưa tích
ON_GENERALS_LIST = "on_generals_list"       # danh sách Generals, tim lọc đã tích
OPEN_CULTIVATE = "open_cultivate"           # màn chi tiết tướng -> bấm Cultivate
OPEN_QUICK_CULTIVATE = "open_quick_cultivate"   # màn Cultivate, tab Quick chưa chọn
ON_QUICK_CULTIVATE = "on_quick_cultivate"       # tab Quick Cultivate đang chọn
