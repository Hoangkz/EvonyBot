"""
constants.py — ảnh của nhiệm vụ Daily Activities "Alliance Donation" (thư mục ảnh ActivitiesDonateAlliance/).
"""
from ..constants import ROOT, OPEN

KEY = "daily_alliance_donation"   # key nhiệm vụ trong bot/worker/priority.py
LABEL = "Alliance Donation"   # ô tích ở tab Daily Activities, key daily_done
FOLDER = "ActivitiesDonateAlliance"
FOLDER_PATH = f"{ROOT}/{FOLDER}"
# Ảnh "đã xong" (thấy là nhiệm vụ hôm nay xong).
DONE_IMAGES = ("AllianceDonateFinish1.png", "AllianceDonateFinish.png", )
# (ảnh, action) theo thứ tự ưu tiên. Action chung (OPEN / TAP / ...) do common.run_task xử lý,
# action riêng (chuỗi) chuyển cho run.handle.
ACTIONS = (
    ("AllianceCapacity.png", "donate"),
    ("ActivitiesDonateAlliance1.png", OPEN),
)

# ---- Luồng mới: donate lượt miễn phí, lặp lại theo giờ (run.donate_free) ----------------------------
# Giống King's Path Donate khi không làm Patrol (event/kings_path/donate/alliance.py): màn chính -> Liên minh
# -> cuộn -> Alliance Science -> bấm "Donate" thẻ khoa học trên cùng tới khi hết lượt miễn phí (nút thành
# kim cương) — KHÔNG mua lượt bằng kim cương. Không có lượt free nào -> dừng, sang nhiệm vụ khác. Có donate ->
# mở danh sách Activity kiểm tra dòng (open_task tap_go=False): hết Go -> xong hôm nay.
# Lượt free hồi theo thời gian -> chưa xong thì làm lại sau INTERVAL_KEY giờ (ô chọn ở tab UI), không ưu tiên
# (cuối Daily Activities; worker hẹn chạy lại Daily với độ ưu tiên thấp, xem bot/worker/scheduler.py).
INTERVAL_KEY = LABEL                 # settings["Alliance Donation"] = số giờ (0 = không làm)
INTERVAL_CHOICES = (0, 1, 2, 3, 4)   # giờ
INTERVAL_DEFAULT = 4
TRIED_KEY = f"{KEY}_tried"           # daily_done: lúc thử donate gần nhất (tính giờ chờ lần sau)
MAX_FREE_DONATIONS = 50              # chặn vòng lặp (lượt free mỗi lần hồi ít hơn nhiều)
