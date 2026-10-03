"""
constants.py — ảnh riêng của nhiệm vụ Refine Equipment (King's Path, Day 4).
"""
from .....context.templates import TEMPLATE_DIR
from ..constants import KP

# Ô chọn ở group King's Path: {"value": mục tiêu, "day": 4}.
KEY = "kings_path_refine"
DAY = 4   # ngày mở nhiệm vụ (dùng khi settings thiếu "day")

# Tab phụ "Sharp Weapons" (thứ 3, bên phải), dòng "Refine equipment N time(s)" (10/20/50/100).
# Đang chọn 1,00 (day4_sharp_weapons.png), chưa chọn 1,00 (day4_fortune_wheel.png); khớp chéo 0,89.
TAB = f"{KP}/Tab/sharpWeapons.png"
TAB_SELECTED = f"{KP}/Tab/sharpWeaponsSelected.png"
TAB_INDEX = 2

R = f"{KP}/Refine"

# ---- Sau khi bấm Go (ảnh tests/event/kings_path/screens/refine_*.png) ---------------------
# Go -> về thành, Lò rèn (Forge) ở giữa -> bấm giữa -> menu (../building.py): icon "Craft"
# (108, 217): 1,00 (refine_menu.png); menu khác <= 0,47.
MENU_CRAFT = f"{R}/menuCraft.png"

# ---- Màn Craft ------------------------------------------------------------------------
# Tiêu đề "Craft" (198, 23): 1,00 ở cả tab Craft / Refine; màn khác <= 0,53.
CRAFT_TITLE = f"{R}/craftTitle.png"
# Tab "Refine" góc trên phải (337, 74): chưa chọn 1,00 (refine_craft.png), đang chọn 1,00
# (refine_screen.png); khớp chéo 0,90 -> ngưỡng 0,95. Màn khác <= 0,66.
TAB_REFINE = f"{R}/tabRefine.png"
TAB_REFINE_SELECTED = f"{R}/tabRefineSelected.png"
TAB_REFINE_THRESHOLD = 0.95
TAB_REFINE_REGION = (0, 7, 100, 15)   # % màn hình: hàng tab Craft / Set / Star / Refine
# Nút xanh "Refine" góc dưới trái (127, 685): 1,00; màn khác <= 0,48 ("Advanced Refine" khác nền).
REFINE_BUTTON = f"{R}/refineButton.png"
REFINE_REGION = (0, 92, 60, 100)

# ---- Hàng trang bị (y ~578) ----------------------------------------------------------------
# Chọn món XANH bên trái nhất; không có món xanh thì món TÍM bên trái nhất.
# 1) Theo ảnh mẫu, chia theo loại trang bị: Equipment/<loại>/blue*.png, purple*.png — phần trong ô
#    26x26 (bỏ viền: món đang chọn có viền vàng), cắt từ tests/event/kings_path/screens/
#    refine_<loại>.png. Đúng món 1,00; món khác màu / khác loại <= 0,56 -> ngưỡng 0,8.
EQUIPMENT = f"{R}/Equipment"
# Thứ tự loại trên vòng chọn loại ở đáy màn (trái -> phải).
EQUIPMENT_TYPES = ("helmet", "armor", "pants", "boots", "ring", "bow", "dagger", "axe", "sword", "mace")


def _equipment_images(pattern: str) -> list[str]:
    return sorted(f"{EQUIPMENT}/{p.parent.name}/{p.name}"
                  for p in (TEMPLATE_DIR / EQUIPMENT).glob(f"*/{pattern}"))


BLUE_ITEMS = _equipment_images("blue*.png")
PURPLE_ITEMS = _equipment_images("purple*.png")
ITEM_THRESHOLD = 0.8
ITEMS_REGION = (0, 78, 100, 86)   # % màn hình: thanh trang bị (y 550 .. 606)
# 2) Món xanh chưa có ảnh mẫu: nhận viền XANH theo MÀU: điểm có hue 95..125 (OpenCV), S > 100,
# V > 120 trong dải ITEMS_Y; nối liền (giãn 3x3) thành khối >= ITEM_MIN px mỗi chiều = 1 viền.
# Đo: refine_items.png viền xanh x 94 / 249, viền vàng / tím không ra khối; refine_craft.png x 42.
ITEMS_Y = (550, 606)
BLUE_HUE = (95, 125)
BLUE_MIN_S = 100
BLUE_MIN_V = 120
ITEM_MIN = 30
# Thanh trang bị cuộn ngang (màn Craft còn món khuất bên phải): chưa thấy món xanh thì vuốt thanh
# sang trái (ngón tay kéo phải -> trái), tối đa ITEMS_SWIPES lần; thanh không đổi sau khi vuốt
# (sai khác trung bình < ITEMS_SAME) = hết thanh.
ITEMS_SWIPE = (75, 82, 15, 82)   # % màn hình, y 82% ~ 578 px
ITEMS_SWIPES = 6
ITEMS_SWIPE_WAIT = 2
ITEMS_SAME = 3

# ---- Vòng chọn loại trang bị ở đáy màn (refine_<loại>.png) ----------------------------------
# Loại đang chọn ở giữa, vòng to viền cam: tâm (196, 634) -> Equipment/<loại>/active.png (30x30).
# Hai loại kề bên, vòng nhỏ xám: trái (121, 645) -> disabledLeft.png, phải (272, 644) ->
# disabledRight.png (26x26; icon xoay theo vòng cung nên trái / phải khác ảnh, khớp chéo 0,39..0,97).
# Đúng loại 1,00; loại khác <= 0,54. Hai vòng ở mép ((50, 668), (342, 672)) bị nút che: không cắt.
# Còn thiếu: mũ là loại đầu (chỉ có disabledLeft), chuỳ chưa có màn riêng (không có active /
# disabledLeft), kiếm chưa có disabledLeft (cần màn chuỳ). Chỉ lấy loại đã có file.


def _equipment_icons(name: str) -> dict[str, str]:
    return {t: f"{EQUIPMENT}/{t}/{name}" for t in EQUIPMENT_TYPES
            if (TEMPLATE_DIR / EQUIPMENT / t / name).exists()}


EQUIPMENT_ACTIVE = _equipment_icons("active.png")
EQUIPMENT_DISABLED_LEFT = _equipment_icons("disabledLeft.png")
EQUIPMENT_DISABLED_RIGHT = _equipment_icons("disabledRight.png")
ACTIVE_POS = (196, 634)
DISABLED_LEFT_POS = (121, 645)
DISABLED_RIGHT_POS = (272, 644)
# Loại đang mở (vào màn là Nhẫn) không có món xanh / tím -> bấm vòng bên trái (DISABLED_LEFT_POS)
# sang loại kế: nhẫn -> giày -> quần -> giáp -> mũ (refine_<loại>.png). Ô quanh vòng giữa
# (ACTIVE_HALF quanh ACTIVE_POS) trước / sau khi bấm khớp >= TYPE_SAME = không đổi loại (mũ là
# loại đầu, bên trái hết) -> thôi. Tối đa TYPE_SWITCHES lần bấm.
ACTIVE_HALF = 20
TYPE_SAME = 0.95
TYPE_SWITCHES = 9
# Bấm sang loại khác -> chờ TYPE_WAIT giây -> vòng giữa đã đổi chưa; chưa thì chờ thêm 1 s, kiểm
# tra lại, tối đa TYPE_CHECKS lần; vẫn chưa đổi -> Back, dừng (không lưu done).
TYPE_WAIT = 1
TYPE_CHECKS = 10
# Loại đang mở = ảnh Equipment/<loại>/active.png khớp cao nhất quanh ACTIVE_POS (đúng loại 1,00;
# mũ so với loại khác <= 0,29). Tới LAST_TYPE (mũ, loại cuối bên trái) mà vẫn không có món xanh /
# tím -> lỗi "không tìm thấy", xong hôm nay (mai làm tiếp).
ACTIVE_THRESHOLD = 0.8
LAST_TYPE = "helmet"

# ---- Màn "Refine Equipment" (bấm nút Refine ở màn Craft; refine_equipment.png / _new.png) -------
# Tiêu đề (199, 23): 1,00; màn khác <= 0,53.
EQUIPMENT_TITLE = f"{R}/equipmentTitle.png"
# Hai ô "Gold Attribute" / "Orange Attribute" (báo khi ra thuộc tính vàng / cam): đang tích thì bỏ
# tích rồi mới Refine. Màn tự cuộn sau mỗi lần Refine (ô dời từ y 330 lên 208) -> tìm theo chữ
# "Gold" (68, 322) / "Orange" (194, 322) (1,00 cả khi đã cuộn), ô lệch BOX_FROM_LABEL so với chữ.
# Chữ khớp 1,00 / 0,998 (refine_equipment*.png) nhưng chỉ 0,90 khi màn cuộn kiểu khác
# (refine_equipment_gold_on.png) -> LABEL_THRESHOLD 0,8.
# Ô đang tích hay trống: so với cả boxOn.png (đang tích, cắt từ refine_equipment_gold_on.png) và
# boxOff.png (trống): giống ảnh nào hơn thì theo ảnh đó. Đo: tích -> on 0,87 / 1,00, off 0,51 / 0,46;
# trống -> off 0,93 .. 1,00, on <= 0,50.
LABELS = {f"{R}/labelGold.png": (-33, 8), f"{R}/labelOrange.png": (-42, 8)}   # {chữ: lệch tới ô}
LABEL_THRESHOLD = 0.8
BOX_OFF = f"{R}/boxOff.png"
BOX_ON = f"{R}/boxOn.png"
BOX_HALF = 18
# Nút xanh "Refine" giữa đáy (197, 668): 1,00; nút Refine của màn Craft ở đây chỉ 0,46 -> ảnh riêng.
EQUIPMENT_REFINE = f"{R}/equipmentRefine.png"
# Refine xong hiện thuộc tính "New" + Cancel / Confirm: bấm Cancel (108, 669) giữ thuộc tính cũ.
# 1,00; các màn khác có nút Cancel giống (0,96) -> chỉ bấm khi thấy EQUIPMENT_TITLE.
CANCEL = f"{R}/cancel.png"
EQUIPMENT_STEPS = 10   # chờ màn Refine Equipment (mỗi bước 1 giây)

SCREEN_STEPS = 10     # chờ màn Craft / tab Refine (mỗi bước 1 giây)
TAB_WAIT = 2          # sau khi bấm tab Refine
ITEM_WAIT = 2         # sau khi chọn món
REFINE_WAIT = 2       # sau mỗi lần bấm Refine / Cancel
STEP_WAIT = 2         # mọi bước khác của Refine (bấm Craft, bỏ tích ô, Back): chờ 2 s
BUTTON_MISSES = 5     # không thấy nút Refine liên tiếp N lần (mỗi lần 1 giây) -> dừng
