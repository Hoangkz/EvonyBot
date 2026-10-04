"""
constants.py — ảnh của nhiệm vụ Daily Activities "Material Composing" (thư mục ảnh ActivitiesComposeMaterials/).
"""
from ..constants import ROOT, OPEN

KEY = "daily_material_composing"   # key nhiệm vụ trong bot/worker/priority.json
LABEL = "Material Composing"   # ô tích ở tab Daily Activities, key daily_done
FOLDER = "ActivitiesComposeMaterials"
FOLDER_PATH = f"{ROOT}/{FOLDER}"
# Ảnh "đã xong" (thấy là nhiệm vụ hôm nay xong).
DONE_IMAGES = ("ComposeMaterialsFinishCurrent.png", "ComposeMaterialsFinish.png", )
# (ảnh, action) theo thứ tự ưu tiên. Action chung (OPEN / TAP / ...) do common.run_task xử lý,
# action riêng (chuỗi) chuyển cho run.handle.
ACTIONS = (
    ("Compose.png", "compose"),
    ("Crystal.png", "crystal"),
    ("Lv1Crystal.png", "level_one"),
    ("ActivitiesComposeMaterials.png", OPEN),
)
AFTER_OPEN_TAP = None   # sau Go: không bấm thêm
