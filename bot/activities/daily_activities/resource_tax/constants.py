"""
constants.py — ảnh của nhiệm vụ Daily Activities "Resource Tax" (thư mục ảnh ActivitiesTaxResource/).
"""
from ..constants import ROOT

KEY = "daily_resource_tax"   # key nhiệm vụ trong bot/worker/priority.py
LABEL = "Resource Tax"   # ô tích ở tab Daily Activities, key daily_done
FOLDER = "ActivitiesTaxResource"
FOLDER_PATH = f"{ROOT}/{FOLDER}"

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
