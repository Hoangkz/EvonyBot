"""
constants.py — activity "Black Market": danh mục vật phẩm (items.json), vùng / ngưỡng nhận diện, điều kiện dừng.
Màn Black Market (tiêu đề, 6 ô, Confirm, Instant Refresh, icon kim cương) dùng chung ảnh / toạ độ với King's Path
Black Market: event/kings_path/black_market/constants.py.
"""
import json
from pathlib import Path

NAME = "Black Market"
ITEMS_JSON = Path(__file__).with_name("items.json")
CATALOG = json.loads(ITEMS_JSON.read_text(encoding="utf-8"))

# ---- Nhận diện món trong một ô (quanh tâm nút giá (x, y), xem SLOTS) ---------------------------------------
# Icon trong items.json: phần hình phía trên ô vật phẩm (bỏ chữ số lượng gói / mệnh giá và số lượng góc dưới phải),
# tìm trong ICON_AREA (dx, dy, w, h) quanh tâm nút giá. Đo trên 366 ô (máy 21913): món đúng >= 0,85, món khác
# <= 0,72 -> ITEM_THRESHOLD.
ICON_AREA = (-35, -112, 70, 78)
ITEM_THRESHOLD = 0.8
# Gói tài nguyên (ô "Resource"): 4 loại lương thực / gỗ / đá / quặng. Icon gói 5M nhận ra cùng loại ở mọi gói 5M
# (>= 0,87); gói khác mức (chưa có icon) -> chữ số lượng (Items/Resource/*.png, `resource_packs`) trong LABEL_AREA,
# ngưỡng LABEL_THRESHOLD. Gói vàng (gold_50k / gold_100k) tạm không mua: icon vàng khớp hơn -> bỏ ô đó.
RESOURCE_IDS = ("food_5m", "lumber_5m", "stone_5m", "ore_5m")
GOLD_PACK_IDS = ("gold_50k", "gold_100k")
LABEL_AREA = (-38, -92, 76, 42)
LABEL_THRESHOLD = 0.85
CHIPS_ID = "chips_100"

# ---- Điều kiện dừng ----------------------------------------------------------------------------------------
GEMS_MIN = 50             # kim cương < 50 (giá một lần Instant Refresh trả phí): luôn dừng
GOLD_MIN = 2_000_000      # vàng < 2.000.000: dừng khi tích CheckGold
MAX_IDLE_STEPS = 30       # số bước liên tiếp không mua / refresh được gì -> dừng (kẹt)
NO_LIMIT = -1             # ô Refresh / Quantity Buy = "ALL"
