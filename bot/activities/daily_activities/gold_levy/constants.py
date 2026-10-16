"""
constants.py — ảnh của nhiệm vụ Daily Activities "Gold Levy" (thư mục ảnh ActivitiesLevyGold/).
"""
from ..constants import ROOT

KEY = "daily_gold_levy"   # key nhiệm vụ trong bot/worker/priority.py
LABEL = "Gold Levy"   # ô tích ở tab Daily Activities, key daily_done
FOLDER = "ActivitiesLevyGold"
FOLDER_PATH = f"{ROOT}/{FOLDER}"
LEVY_ALL_WAIT = 3       # giây chờ sau khi bấm Free Levy All
POPUP_WAIT = 10         # luồng mới (run.after_go): giây chờ tối đa popup Levy sau khi bấm icon "Levy"
BACKS_AFTER_LEVY = 3    # xong: Back (tối đa chừng này lần) tới khi popup Levy đóng
