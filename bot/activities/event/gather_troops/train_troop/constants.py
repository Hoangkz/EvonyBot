"""
constants.py — ảnh, ngưỡng và action dùng chung cho các nhiệm vụ train lính của Gather
Troops (Ground Troop, Mounted Troop, ...). Ảnh riêng của từng nhiệm vụ (tab Day, tab phụ,
ảnh cấp lính) nằm trong constants.py của nhiệm vụ đó (xem TroopTask trong run.py).
"""
import json

from .....context import TEMPLATE_DIR
from ...constants import EV

# ---- Thành chính sau khi bấm Go -----------------------------------------------------
# Bấm Go -> game đưa về thành, kéo doanh trại (Barracks / Stables ...) vào giữa màn hình.
# Chờ GO_WAIT giây rồi bấm giữa màn hình để mở menu công trình; menu hiện icon "Train" (hai
# thanh kiếm). Barracks (110, 234): khớp 1,00; Stables (115, 233): 0,91; trước khi bấm
# <= 0,58; 136 màn khác <= 0,68 -> ngưỡng TRAIN_THRESHOLD.
TRAIN = f"{EV}/GatherTroops/Train/train.png"
TRAIN_THRESHOLD = 0.8
GO_WAIT = 10              # giây chờ sau khi bấm Go
CENTER = (50, 50)         # % màn hình: công trình sau khi bấm Go
MENU_CHECK_DELAY = 1      # giây chờ menu hiện trước khi tìm icon Train
MENU_WAIT = 3             # giây chờ sau mỗi bước của menu

# ---- Màn Train (bấm icon Train trong menu công trình) --------------------------------
LOWEST_TIER = 7           # nhiệm vụ chỉ tính "tier 7 and above"
TRAIN_WAIT = 3            # giây chờ màn Train mở sau khi bấm icon Train
# Số lính tối đa một lần train: ô bên phải nút "+" (đọc bằng bot.ocr.read_train_count).
TRAIN_COUNT_BOX = (282, 570, 104, 24)       # (x, y, w, h) px trên màn 396x704
# Nút "Train" xanh (chữ "Train", tâm (295, 663)): khớp 1,00; nút xám khi cấp khoá 0,77.
# Bấm Train -> nút đổi thành "Training Speedup" ở cùng chỗ -> bấm tiếp mở màn speedup.
TRAIN_BUTTON = f"{EV}/GatherTroops/Train/trainButton.png"
TRAIN_BUTTON_POS = (295, 668)               # px: nút Train / Training Speedup
# Ngưỡng nhận nút "Train" cả xanh lẫn xám (cấp khoá 0,77): không thấy cả hai = nút đã là
# "Training Speedup" (có mẻ đang train). TODO: đo lại khi có ảnh nút Training Speedup thật.
TRAIN_BUTTON_ANY = 0.7
# Chữ "Train" của nút "Instant Train" (tốn gems, nửa trái, tâm (128, 664)) cũng khớp
# 0,71-0,74 -> CHỈ tìm nút Train ở nửa phải đáy màn hình (% màn hình).
TRAIN_BUTTON_REGION = (52, 90, 100, 100)
BUTTON_WAIT = 2                             # giây chờ sau mỗi lần bấm nút

# ---- Màn Training Speedup ----------------------------------------------------------------
# Tiêu đề "Training Speedup" và nút "Finish All" (tâm (100, 674)) vẫn khớp 0,99 khi hộp
# "Finish All" mở đè lên -> xét hộp trước. Màn khác <= 0,51.
SPEEDUP_TITLE = f"{EV}/GatherTroops/Train/speedupTitle.png"
SPEEDUP_SETTINGS = f"{EV}/GatherTroops/Train/speedupSettings.png"   # "Speedup Settings >>" (115, 630)
FINISH_ALL = f"{EV}/GatherTroops/Train/finishAll.png"
# Hộp "Finish All" (bấm Speedup Settings): ô tích góc dưới trái (41, 536) "dùng speedup
# thường khi speedup riêng không đủ" và nút Confirm (197, 590). Ô tích / bỏ tích khớp chéo
# 0,73 -> ngưỡng 0,9; màn khác <= 0,67.
FINISH_ALL_TITLE = f"{EV}/GatherTroops/Train/finishAllTitle.png"
CHECKBOX_OFF = f"{EV}/GatherTroops/Train/checkboxOff.png"
CHECKBOX_ON = f"{EV}/GatherTroops/Train/checkboxOn.png"
CONFIRM = f"{EV}/GatherTroops/Train/confirm.png"
FINISH_WAIT = 3                             # giây chờ sau khi bấm Finish All
# Toạ độ đo sẵn (dùng khi không tìm thấy ảnh nút trên ảnh chụp).
SPEEDUP_SETTINGS_POS = (115, 630)
FINISH_ALL_POS = (100, 674)
CONFIRM_POS = (197, 590)


def tier_targets(key: str) -> dict[int, int]:
    """{cấp: số lính} của ô chọn `key` trong ui/tabs/event.json (VD 10 -> 5000): mục tiêu
    khi cấp người dùng chọn bị khoá và phải train cấp thấp hơn."""
    data = json.loads((TEMPLATE_DIR.parent / "ui/tabs/event.json").read_text(encoding="utf-8"))
    for group in data["groups"]:
        for combo in group.get("combos", []):
            if combo["key"] == key:
                return {v["level"]: v["value"] for v in combo["values"] if v.get("level")}
    return {}


# ---- Actions --------------------------------------------------------------------
OPEN_DAY = "open_day"                       # tab Day của nhiệm vụ chưa chọn -> bấm
OPEN_TAB = "open_tab"                       # tab phụ của nhiệm vụ chưa chọn -> bấm
ON_TAB = "on_tab"                           # tab phụ đang chọn -> bấm Go đầu tiên
ON_TRAIN_MENU = "on_train_menu"             # menu công trình đã mở (có icon Train) -> bấm
ON_TRAIN_SCREEN = "on_train_screen"         # màn Train (hàng cấp lính) -> chọn cấp, train
ON_FINISH_ALL_DIALOG = "on_finish_all_dialog"   # hộp Finish All -> tích ô, Confirm
ON_SPEEDUP = "on_speedup"                   # màn Training Speedup -> (settings) Finish All
