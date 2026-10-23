"""constants.py — nhóm trang bị, ảnh icon và key cấu hình của tab "Craft"."""
from ...context.templates import TEMPLATE_DIR

FOLDER = "Craft"                     # Images/Craft/<nhóm>/NN_<Tên_trang_bị>.png: icon trang bị vàng trở lên (NN = thứ tự trong danh sách của game);
                                     # Images/Craft/<nhóm>/name/<cùng tên file>: ảnh tên hiện ở đầu màn Craft khi chọn trang bị đó
LOCK = f"{FOLDER}/lock.png"          # ổ khoá giữa icon: trang bị chưa mở khoá, không chế tạo được (ngưỡng đo 0.65)
LOCK_THRESHOLD = 0.65

# (tên thư mục, tiêu đề group) theo thứ tự hiển thị; nhóm chưa có ảnh thì tab bỏ qua.
CATEGORIES = [
    ("ring", "Ring"), ("bow", "Bow"), ("spear", "Spear"), ("axe", "Axe"), ("sword", "Sword"), ("staff", "Staff"),
    ("helmet", "Helmet"), ("armor", "Armor"), ("legs", "Legwear"), ("boots", "Boots"),
]
KEEP_ORDER = {"staff"}               # nhóm giữ thứ tự NN tăng dần; các nhóm khác hiện ngược (phẩm cao nhất lên đầu)

ITEMS_KEY = "items"                  # {"ring/05": số lượng, ...}: chỉ các trang bị đã tích
DEFAULT_QTY = 1
MAX_QTY = 99


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
