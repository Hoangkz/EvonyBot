"""
constants.py — ảnh của nhiệm vụ Daily Activities "Resource Collecting" (thư mục ảnh ActivitiesSourceCollecting/).
"""
from ..constants import ROOT, OPEN_COLLECTING_HELPER, VERIFY_COLLECTING

KEY = "daily_resource_collecting"   # key nhiệm vụ trong bot/worker/priority.json
LABEL = "Resource Collecting"   # ô tích ở tab Daily Activities, key daily_done
FOLDER = "ActivitiesSourceCollecting"
FOLDER_PATH = f"{ROOT}/{FOLDER}"
# Ảnh "đã xong" (thấy là nhiệm vụ hôm nay xong).
DONE_IMAGES = ()   # không có: xong khi dòng nhiệm vụ hết nút Go
# (ảnh, action) theo thứ tự ưu tiên. Action chung (OPEN / TAP / ...) do common.run_task xử lý,
# action riêng (chuỗi) chuyển cho run.handle.
ACTIONS = (
    ("Collection.png", "collection"),
    ("ClaimCollecting.png", VERIFY_COLLECTING),
    ("ActivitiesSourceCollecting.png", OPEN_COLLECTING_HELPER),
)
