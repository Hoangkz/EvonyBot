"""
constants.py — ảnh của nhiệm vụ Daily Activities "Monster Killing" (thư mục ảnh ActivitiesAttackMonster/).
"""
from ..constants import ROOT, OPEN_MONSTER_FIRST, OPEN_MONSTER_SECOND, TAP

KEY = "daily_monster_killing"   # key nhiệm vụ trong bot/worker/priority.json
LABEL = "Monster Killing"   # ô tích ở tab Daily Activities, key daily_done
FOLDER = "ActivitiesAttackMonster"
FOLDER_PATH = f"{ROOT}/{FOLDER}"
# Ảnh "đã xong" (thấy là nhiệm vụ hôm nay xong).
DONE_IMAGES = ()   # không có: xong khi dòng nhiệm vụ hết nút Go
# (ảnh, action) theo thứ tự ưu tiên. Action chung (OPEN / TAP / ...) do common.run_task xử lý,
# action riêng (chuỗi) chuyển cho run.handle.
ACTIONS = (
    ("March.png", "march"),
    ("AttackMonster.png", "monster"),
    ("TapMonster.png", "tap_monster"),
    ("FindMonster.png", TAP),
    ("ActivitiesAttackMonsterNext.png", OPEN_MONSTER_SECOND),
    ("ActivitiesAttackMonster.png", OPEN_MONSTER_FIRST),
)
AFTER_OPEN_TAP = None   # sau Go: không bấm thêm
