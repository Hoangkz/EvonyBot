"""
constants.py — ảnh của nhiệm vụ Daily Activities "Troop Heading" (thư mục ảnh ActivitiesTroopHeal/).
"""
from ..constants import ROOT

KEY = "daily_troop_heading"   # key nhiệm vụ trong bot/worker/priority.py
LABEL = "Troop Heading"   # ô tích ở tab Daily Activities, key daily_done
FOLDER = "ActivitiesTroopHeal"
FOLDER_PATH = f"{ROOT}/{FOLDER}"

# ---- Luồng mới sau Go (run.after_go), giống King's Path Heal ----------------------------------------
# Go -> về thành, Bệnh viện ở giữa -> menu: Speed Up (đang chữa dở) -> Finish All rồi mở lại menu; Heal ->
# màn Hospital -> Reset -> cuộn xuống cuối -> chọn HEAL_GOAL lính từ dòng cấp thấp nhất lên -> Heal ->
# Speed Up -> Finish All -> xong. Ảnh / bước dùng chung với event/kings_path/heal.
HEAL_GOAL = 150         # nhiệm vụ "Heal 150 troops in the Main City"
MENU_ROUNDS = 3         # số lần mở menu Bệnh viện tối đa (lần đầu có thể phải Finish All lượt đang chữa)
