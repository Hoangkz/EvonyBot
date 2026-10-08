"""
constants.py — ảnh của nhiệm vụ Daily Activities "Resource Gathering" (thư mục ảnh ActivitiesSourceGathering/).
"""
from ..constants import ROOT, OPEN

KEY = "daily_resource_gathering"   # key nhiệm vụ trong bot/worker/priority.py
LABEL = "Resource Gathering"   # ô tích ở tab Daily Activities, key daily_done
FOLDER = "ActivitiesSourceGathering"
FOLDER_PATH = f"{ROOT}/{FOLDER}"
# Ảnh "đã xong" (thấy là nhiệm vụ hôm nay xong).
DONE_IMAGES = ()   # không có: xong khi dòng nhiệm vụ hết nút Go
# (ảnh, action) theo thứ tự ưu tiên. Action chung (OPEN / TAP / ...) do common.run_task xử lý,
# action riêng (chuỗi) chuyển cho run.handle.
ACTIONS = (
    ("HandCurrent.png", "hand"),
    ("GatherCityCurrent.png", OPEN),
)
AFTER_OPEN_TAP = None   # sau Go: không bấm thêm
