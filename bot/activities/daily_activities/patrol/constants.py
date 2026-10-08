"""
constants.py — ảnh của nhiệm vụ Daily Activities "Patrol" (thư mục ảnh ActivitiesPatrol/).
"""
from ...event.kings_path.patrol.constants import PER_ROUND, ROUNDS_PER_DAY
from ..constants import ROOT, OPEN

KEY = "daily_patrol"   # key nhiệm vụ trong bot/worker/priority.py
LABEL = "Patrol"   # ô tích ở tab Daily Activities, key daily_done
FOLDER = "ActivitiesPatrol"
FOLDER_PATH = f"{ROOT}/{FOLDER}"
# Ảnh "đã xong" (thấy là nhiệm vụ hôm nay xong).
DONE_IMAGES = ("PatrolFinishCurrent.png", "PatrolFinish.png", )
# (ảnh, action) theo thứ tự ưu tiên. Action chung (OPEN / TAP / ...) do common.run_task xử lý,
# action riêng (chuỗi) chuyển cho run.handle.
ACTIONS = (
    ("Patrol1.png", "patrol"),
    ("Patrol.png", "patrol_button"),
    ("ActivitiesPatrol.png", OPEN),
)

# ---- Luồng mới sau Go (run.after_go), giống hệt King's Path Patrol sau Go ---------------------------
# Go -> về thành, Tường thành ở giữa -> menu "Patrol" -> màn Patrol -> event/kings_path/patrol patrol_rounds:
# Select All -> Patrol (+10 tiến độ mỗi lượt) -> Refresh ... làm HẾT lượt trong ngày (ROUNDS_PER_DAY = 10 lượt)
# dù nhiệm vụ "Patrol for 3 time(s)" chỉ cần 1 lượt; dừng sớm khi hết Refresh. Số lượt hôm nay đếm riêng
# (daily_done "daily_patrol_round_<n>"); King's Path đếm riêng của nó và tự dừng khi nút Refresh xám.
PATROL_GOAL = PER_ROUND * ROUNDS_PER_DAY   # không bao giờ đạt trước khi hết 10 lượt
