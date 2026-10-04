"""
constants.py — ảnh của nhiệm vụ Daily Activities "Resource Tax" (thư mục ảnh ActivitiesTaxResource/).
"""
from ...event.kings_path.city_tax.constants import POPUP, TAX_MENU, TAX_SCREEN
from ..constants import ROOT, OPEN

KEY = "daily_resource_tax"   # key nhiệm vụ trong bot/worker/priority.json
LABEL = "Resource Tax"   # ô tích ở tab Daily Activities, key daily_done
FOLDER = "ActivitiesTaxResource"
FOLDER_PATH = f"{ROOT}/{FOLDER}"
# Ảnh "đã xong" (thấy là nhiệm vụ hôm nay xong).
DONE_IMAGES = ("TaxFinish2.png", "TaxFinish.png", "TaxFinish1.png", )
# (ảnh, action) theo thứ tự ưu tiên. Action chung (OPEN / TAP / ...) do common.run_task xử lý,
# action riêng (chuỗi) chuyển cho run.handle.
# Ảnh màn Tax dùng chung với King's Path City Tax (Images/CityTax/, xem event/kings_path/city_tax).
ACTIONS = (
    (POPUP, "popup"),          # popup Tax còn mở (bị ngắt giữa chừng) -> đóng
    (TAX_SCREEN, "tax"),       # màn Tax -> run.tax_all
    (TAX_MENU, "tax_menu"),    # menu Chợ, icon "Tax"
    ("ActivitiesTaxResource.png", OPEN),
)

# ---- Group "City Tax" (tab Daily Activities, trong "Selection Daily"; key cấu hình TAX_KEY) -------
# settings["Tax on resource"] = {"Food": n, "Wood": n, "Stone": n, "Iron": n, "free": "Food" | None}:
# n = số lần thu loại đó (0 = không thu); "free" = loại duy nhất được tích ô Free (None = không loại nào).
# Flow (run.tax_all): loại Free thu trước, hết lượt free rồi cộng thêm n lần (tốn kim cương); rồi các loại
# khác đúng n lần.
TAX_KEY = "Tax on resource"
TAX_FREE_KEY = "free"
TAX_RESOURCES = ("Food", "Wood", "Stone", "Iron")
TAX_CHOICES = (0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50)
TAX_DEFAULT = 10      # số lần mặc định mỗi loại (cấu hình chưa có)
TAX_FREE_DEFAULT = "Stone"   # loại tích Free mặc định (cấu hình chưa có)
SET_TRIES = 5          # popup: đọc ô số (OCR) -> bấm "+" / "−" bù chênh lệch, tối đa chừng này vòng
BACKS_AFTER_TAX = 3    # thu xong: Back (tối đa chừng này lần) tới khi màn Tax đóng, về thành
