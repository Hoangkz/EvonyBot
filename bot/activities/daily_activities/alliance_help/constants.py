"""
constants.py — ảnh của nhiệm vụ Daily Activities "Alliance Help" (thư mục ảnh ActivitiesAllianceHelp/).
"""
from ..constants import ROOT

KEY = "daily_alliance_help"   # key nhiệm vụ trong bot/worker/priority.json
LABEL = "Alliance Help"       # tên ở tab Daily Activities, key daily_done
FOLDER = "ActivitiesAllianceHelp"
FOLDER_PATH = f"{ROOT}/{FOLDER}"
# Không có luồng C# cũ: không có ảnh "đã xong" / action cho common.run_task.
DONE_IMAGES = ()
ACTIONS = ()

# ---- Theo giờ (../hourly.py try_task, gọi từ ../run.py), như Alliance Donation ------------------------
# Nhiệm vụ "Complete Alliance Help for 5 time(s)". Màn chính -> Liên minh -> dòng "Alliance Help" -> màn Alliance
# Help: "No records" (không ai cần giúp) -> Back, sang nhiệm vụ khác, KHÔNG lưu gì vào DB (không kiểm tra Activity);
# có "Help All" -> bấm -> Back -> lưu giờ thử -> kiểm tra dòng / thẻ Activity (như Alliance Donation): xong -> đánh dấu.
INTERVAL_KEY = LABEL                 # settings["Alliance Help"] = số giờ (0 = không làm)
INTERVAL_CHOICES = (0, 1, 2, 3, 4)   # giờ
INTERVAL_DEFAULT = 4
TRIED_KEY = f"{KEY}_tried"           # daily_done: lúc thử gần nhất (tính giờ chờ lần sau)

# Ảnh đo trên màn 396x704 (tests/daily_activities/alliance_help/screens/):
# - dòng "Alliance Help" ở màn Liên minh (135, 606): 1,00 (máy 21913), 0,995 (21943), sau khi cuộn 0,98; màn khác
#   <= 0,60.
# - tiêu đề "Alliance Help" (199, 23): 1,00 có yêu cầu / 0,99 "No records"; màn khác <= 0,76.
# - nút "Help All" (198, 667): 1,00; màn khác <= 0,61.
# - chữ "No records" (199, 377) (help_no_records.png): 1,00; màn khác <= 0,55.
# Kiểm tra Activity (giao diện cũ, common.open_task): Card.png (thẻ chưa xong, 0,95 .. 1,00 ở mọi ảnh lưới) / Done.png
# (thẻ "Completed", 1,00; thẻ chưa xong <= 0,65; Completed nhiệm vụ khác <= 0,60). Giao diện mới: chưa có Title.png.
HELP_ROW = f"{FOLDER_PATH}/HelpRow.png"
HELP_TITLE = f"{FOLDER_PATH}/HelpTitle.png"
HELP_ALL = f"{FOLDER_PATH}/HelpAll.png"
NO_RECORDS = f"{FOLDER_PATH}/NoRecords.png"
HELP_WAIT = 3          # giây chờ sau khi bấm Help All
LIST_WAIT = 5          # giây chờ danh sách yêu cầu (Help All) hoặc "No records" hiện
NAV_MAX_STEPS = 30
