"""
constants.py — ảnh của nhiệm vụ Daily Activities "Resource Tax" (thư mục ảnh ActivitiesTaxResource/).
"""
from ..constants import ROOT, OPEN

KEY = "daily_resource_tax"   # key nhiệm vụ trong bot/worker/priority.json
LABEL = "Resource Tax"   # ô tích ở tab Daily Activities, key daily_done
FOLDER = "ActivitiesTaxResource"
FOLDER_PATH = f"{ROOT}/{FOLDER}"
# Ảnh "đã xong" (thấy là nhiệm vụ hôm nay xong).
DONE_IMAGES = ("TaxFinish2.png", "TaxFinish.png", "TaxFinish1.png", )
# (ảnh, action) theo thứ tự ưu tiên. Action chung (OPEN / TAP / ...) do common.run_task xử lý,
# action riêng (chuỗi) chuyển cho run.handle.
ACTIONS = (
    ("TapTax1.png", "tax_amount"),
    ("TaxRevenue.png", "revenue"),
    ("Tax.png", "tax"),
    ("ActivitiesTaxResource.png", OPEN),
)
