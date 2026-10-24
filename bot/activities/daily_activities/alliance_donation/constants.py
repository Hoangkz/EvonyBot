"""
constants.py — hằng số của nhiệm vụ Daily Activities "Alliance Donation".
"""

KEY = "daily_alliance_donation"   # key nhiệm vụ trong bot/worker/priority.py
LABEL = "Alliance Donation"   # ô tích ở tab Daily Activities, key daily_done
FOLDER = "ActivitiesDonateAlliance"
# ---- Donate lượt miễn phí, lặp lại theo giờ (run.donate_free) ------------------------------------------------------
# Liên minh -> kéo xuống Alliance Science -> bấm "Donate" thẻ khoa học trên cùng tới khi hết lượt miễn phí (nút thành kim
# cương) — KHÔNG mua lượt bằng kim cương. Donate được thì lưu giờ vào DB (TRIED_KEY) rồi ra danh sách nhiệm vụ nhận thưởng.
# Lượt free hồi theo thời gian -> làm lại sau INTERVAL_KEY giờ (ô chọn ở tab UI): tới giờ thì worker làm ngay.
INTERVAL_KEY = LABEL                 # settings["Alliance Donation"] = số giờ (0 = không làm)
INTERVAL_CHOICES = (0, 1, 2, 3, 4)   # giờ
INTERVAL_DEFAULT = 4
TRIED_KEY = f"{KEY}_tried"           # daily_done: lúc thử donate gần nhất (tính giờ chờ lần sau)
LEAVE_BACKS = 2                      # xong donate: Back đóng Alliance Science rồi màn Liên minh -> về thành
MAX_FREE_DONATIONS = 50              # chặn vòng lặp (lượt free mỗi lần hồi ít hơn nhiều)
