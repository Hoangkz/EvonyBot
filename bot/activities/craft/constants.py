"""constants.py — nhóm trang bị, ảnh icon và key cấu hình của tab "Craft"."""
from ...context.templates import TEMPLATE_DIR

KEY = "craft"                        # key nhiệm vụ trong priority.py / daily_done (`craft_error` khi lỗi)
NAME = "Craft"                       # tên hiện trong log
STEP_WAIT = 2                        # giây chờ sau mỗi bước bấm
FOLDER = "Craft"                     # Images/Craft/<nhóm>/NN_<Tên_trang_bị>.png: icon trang bị vàng trở lên (NN = thứ tự trong danh sách của game);
                                     # Images/Craft/<nhóm>/name/<cùng tên file>: ảnh tên hiện ở đầu màn Craft khi chọn trang bị đó
LOCK = f"{FOLDER}/lock.png"          # ổ khoá giữa icon (10x10): trang bị chưa mở khoá. Từ ô khoá đầu tiên tới hết danh sách đều chưa mở -> không chế tạo được
LOCK_THRESHOLD = 0.7                 # đo: ô khoá 0,72 .. 1,00; ô đã mở <= 0,46 (một chỗ nền khác 0,65)
LOCK_MARGIN = 20                     # trang bị có tâm x >= x ổ khoá đầu tiên - ngần này px là ô khoá đó hoặc nằm bên phải nó

# (tên thư mục, tiêu đề group) theo thứ tự hiển thị; nhóm chưa có ảnh thì tab bỏ qua.
CATEGORIES = [
    ("ring", "Ring"), ("bow", "Bow"), ("spear", "Spear"), ("axe", "Axe"), ("sword", "Sword"), ("staff", "Staff"),
    ("helmet", "Helmet"), ("armor", "Armor"), ("legs", "Legwear"), ("boots", "Boots"),
]
KEEP_ORDER = {"staff"}               # nhóm giữ thứ tự NN tăng dần; các nhóm khác hiện ngược (phẩm cao nhất lên đầu)

# Quà đổi (Redeem) của event, xếp theo độ ưu tiên từ trên xuống (id, tên hiện trên tab); thêm quà mới = thêm một dòng.
GIFTS = [("resource", "Resource"), ("stamina", "Stamina")]
CLAIM_KEY = "claim_event_gifts"      # bool: có nhận / đổi quà event không
GIFT_ORDER_KEY = "gift_order"        # [id quà, ...] theo thứ tự ưu tiên

ITEMS_KEY = "items"                  # {"ring/05": số lượng, ...}: chỉ các trang bị đã tích
DEFAULT_QTY = 1
MAX_QTY = 99

# ---- Màn Craft (vào màn là loại Nhẫn, tab Craft) -------------------------------------------------------------------------------------
# Vòng chọn loại ở đáy màn, trái -> phải (mũ là loại đầu bên trái, chuỳ là loại cuối bên phải). Loại đang mở ở giữa (tâm ACTIVE_POS):
# ảnh Images/Craft/Category/<loại>.png (60x60) khớp 1,00 đúng loại; loại khác <= 0,83 -> ngưỡng 0,9. Bấm vòng nhỏ bên trái / phải sang loại kề.
CAROUSEL = ("helmet", "armor", "legs", "boots", "ring", "bow", "spear", "axe", "sword", "staff")
START_TYPE = "ring"
CATEGORY_DIR = f"{FOLDER}/Category"
ACTIVE_POS = (196, 634)
ACTIVE_HALF = 40
CATEGORY_THRESHOLD = 0.9
LEFT_TYPE_POS = (121, 645)
RIGHT_TYPE_POS = (272, 644)
TYPE_WAIT = 2                        # giây chờ sau khi bấm sang loại khác
TYPE_CHECKS = 6                      # số lần kiểm tra (mỗi lần 1 giây) vòng giữa đã đổi loại chưa

# Hàng trang bị ở đáy (y ~578): vuốt sang trái (ngón kéo phải -> trái) xem tiếp, sang phải về đầu danh sách. Vuốt CHẬM (ITEMS_SWIPE_TIME) để gần
# như hết quán tính. Hết danh sách khi vuốt mà một trang bị (ô giữa hàng) không đổi (sai khác trung bình < ITEMS_SAME): không vuốt tiếp.
ITEMS_REGION = (0, 78, 100, 86)      # % màn hình: hàng trang bị (y 550 .. 606)
ITEMS_Y = (550, 606)
ITEMS_SWIPE_LEFT = (85, 82, 20, 82)
ITEMS_SWIPE_RIGHT = (20, 82, 85, 82)
ITEMS_SWIPE_TIME = 2.5
ITEMS_SWIPE_WAIT = 1.5
ITEMS_SWIPES = 20                    # số cú vuốt tối đa mỗi chiều
ITEMS_SAME = 20                      # một trang bị (ô giữa hàng) trước / sau cú vuốt sai khác trung bình < ngưỡng này = không cuộn nữa = đã tới đầu / cuối danh sách.
                                     # Đo: đang cuộn 50 .. 70; ở cuối bên phải 0,0 .. 0,1; ở đầu bên trái danh sách còn nảy lại (overscroll) nên vẫn 7 .. 14 -> ngưỡng 20
ITEM_PATCH = (176, 557, 220, 600)    # ô icon giữa hàng (x0, y0, x1, y1): so trước / sau khi vuốt
ICON_THRESHOLD = 0.65                # phần giữa icon (28x28, bỏ viền: món đang chọn có viền khác) khớp trên hàng trang bị. Đo trên màn thật: đúng trang bị
                                     # 0,68 .. 1,00 (icon cắt lệch vài px thì thấp hơn), trang bị khác <= 0,58; khớp nhầm đã có bước so ảnh tên chặn
ITEM_WAIT = 2                        # giây chờ sau khi chọn một trang bị

# Tên trang bị đang chọn (đầu màn, chữ giữa): ảnh Images/Craft/<loại>/name/<cùng tên file icon> khớp 1,00 khi đúng trang bị.
TITLE_REGION = (0, 15, 100, 22)      # % màn hình: y 105 .. 155
TITLE_THRESHOLD = 0.9

# Nút bên phải đáy màn (x 205 .. 333, y 668 .. 704) có 3 trạng thái, phân biệt theo màu (HSV trung bình của BUTTON_BOX; đo: Quick Compose
# H 53 S 200, Begin vàng H 17 S 233, Begin xám S 12):
#   xanh lá  = "Quick Compose" (thiếu nguyên liệu, ghép được): bấm -> nút đổi thành Begin;
#   vàng     = "Begin" chế tạo được: bấm -> game về thành (Lò rèn đang chế tạo, chỉ chế tạo được MỘT trang bị một lúc);
#   xám/đen  = "Begin" chưa chế tạo được: bỏ qua trang bị này.
BUTTON_BOX = (212, 676, 328, 700)
BUTTON_POS = (269, 686)
QUICK_COMPOSE = "quick_compose"
BEGIN = "begin"
DISABLED = "disabled"
COLOR_MIN_SATURATION = 120           # dưới mức này (xám, S ~ 12) = Begin chưa chế tạo được
GREEN_HUE = (40, 70)
GOLD_HUE = (8, 30)
ACTION_WAIT = 3                      # giây chờ sau khi bấm Begin
# Sau Quick Compose: bot.wait_for chờ nút đổi thành Begin vàng, kiểm tra mỗi BEGIN_INTERVAL giây, tối đa BEGIN_TIMEOUT giây (8 lần). Ảnh mẫu chỉ có chữ
# "Begin" + nền nút (216..324 x 677..688), KHÔNG lấy dòng thời gian bên dưới (mỗi trang bị một số khác): Begin vàng 1,00; Begin xám 0,89; Quick Compose <= 0,49
# -> ngưỡng 0,95.
BEGIN_BUTTON = f"{FOLDER}/beginButton.png"
BEGIN_THRESHOLD = 0.95
BEGIN_TIMEOUT = 8
BEGIN_INTERVAL = 1

# ---- Sau Begin: Lò rèn đang chế tạo (ảnh chụp trên 21943 với Iron Ring) ------------------------------------------------------------------
# Bấm Lò rèn (giữa màn) -> menu tròn có thêm "Speed Up" (tia chớp, (90, 272)) / Instant Finish (kim cương) / Cancel Crafting (KHÔNG bấm) ->
# màn "Crafting Speedup" (giống Healing / Training Speedup): lần đầu Speedup Settings -> hộp Finish All (tích ô, Confirm); nút vàng "Finish All"
# (100, 674) dùng vật phẩm tăng tốc cho tới khi xong -> về thành, hiện "Finished All Successfully!" -> vài giây sau bóng trang bị vừa làm xong nổi trên
# Lò rèn ((198, 222), viền màu theo phẩm) -> bấm -> hộp "Congratulations on getting" -> Confirm (197, 566) -> về thành.
MENU_SPEED_UP = f"{FOLDER}/Menu/speedUp.png"          # icon + chữ "Speed Up" ở menu Lò rèn đang chế tạo: 1,00; menu rảnh / màn khác <= 0,38
SPEEDUP_TITLE = f"{FOLDER}/speedupTitle.png"          # "Crafting Speedup" (198, 24): 1,00; màn khác <= 0,41
CONGRATS = f"{FOLDER}/congrats.png"                   # ruy băng "Congratulations on getting": 1,00; màn khác <= 0,37
CONFIRM = f"{FOLDER}/confirm.png"                     # nút Confirm xanh của hộp đó: 1,00; màn khác <= 0,39
CONFIRM_POS = (197, 566)
COLLECT_POS = (198, 222)                              # bóng trang bị trên Lò rèn (Lò rèn ở giữa màn)
COLLECT_WAIT = 4                                      # giây chờ bóng hiện sau Finish All
COLLECT_TRIES = 4
SPEEDUP_STEPS = 8
SPEEDUP_WAIT = 3


# Bộ trang bị (lọc ở tab): nhãn và từ khoá trong tên, xét theo thứ tự; tên không khớp từ khoá nào là "Basic" (Fighter's, General's, Champion's...).
SETS = [("King", "King's"), ("Dragon", "Dragon"), ("Achaemenidae", "Achaemenidae"), ("Officer", "Officer's"), ("Consul", "Consul's")]
SET_BASIC = "Basic"


def item_set(name: str) -> str:
    """"Fearless Dragon Helmet" -> "Dragon"; "Consul's Ring" -> "Consul"; "Fighter's Bow" -> "Basic"."""
    return next((label for label, word in SETS if word in name), SET_BASIC)


def item_name(stem: str) -> str:
    """"05_Fighter's_Bow" -> "Fighter's Bow"."""
    return stem.split("_", 1)[-1].replace("_", " ")


def catalog() -> list[tuple[str, str, list[tuple[str, str, str]]]]:
    """[(nhóm, tiêu đề, [(id "nhóm/NN_Tên", đường dẫn ảnh tương đối Images/, tên trang bị)])] cho các nhóm đã có ảnh."""
    result = []
    for key, title in CATEGORIES:
        files = sorted((TEMPLATE_DIR / FOLDER / key).glob("*.png"), reverse=key not in KEEP_ORDER)
        if files:
            result.append((key, title, [(f"{key}/{p.stem}", f"{FOLDER}/{key}/{p.name}", item_name(p.stem)) for p in files]))
    return result
