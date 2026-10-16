"""
constants.py — ảnh của nhiệm vụ Daily Activities "Research technologies" (thư mục ảnh ActivitiesResearch/).
"""
from ..constants import ROOT

KEY = "daily_alliance_research"   # key nhiệm vụ trong bot/worker/priority.py
LABEL = "Research"   # ô tích ở tab Daily Activities, key daily_done
FOLDER = "ActivitiesResearch"
FOLDER_PATH = f"{ROOT}/{FOLDER}"

# ---- Sau Go (run.after_go) --------------------------------------------------------------------
# Học viện ở giữa -> open_menu (icon "Research") -> màn Academy: các tab (Advancement, Defense, ...) và cây
# công nghệ. Nút công nghệ có nhãn "Lv N / M": XANH = học được, trắng = tối đa hoặc chưa mở khoá. Chọn nút xanh
# đầu tiên (từ trên xuống, trái sang phải) của tab đang mở, không có thì cuộn cây xuống (TREE_SCROLLS lần),
# vẫn không có thì sang tab kế bên (4 tab, TAB_TAPS); cả 4 tab không có gì thì báo xong hôm nay. Bấm nút -> màn "Technology" -> Research:
#   - nghiên cứu xong ngay (0 giây): màn Technology còn mở, cấp tăng;
#   - tốn thời gian: popup "Researching" -> Speed Up xanh (vật phẩm, KHÔNG bấm nút Speed Up có kim cương)
#     -> màn Research Speedup -> Finish All -> Confirm.
# Học viện đang nghiên cứu sẵn (thanh thời gian trên mái, menu có thêm Speed Up / Cancel Research / Instant Finish):
# chỉ bấm icon Speed Up -> màn Research Speedup -> Finish All -> Confirm. Không bấm Instant Finish (kim cương).
MENU_RESEARCH = f"{FOLDER_PATH}/Research.png"
MENU_SPEED_UP = f"{FOLDER_PATH}/MenuSpeedUp.png"   # icon Speed Up của menu Học viện đang nghiên cứu sẵn
ACADEMY_TITLE = f"{FOLDER_PATH}/AcademyTitle.png"
TECH_TITLE = f"{FOLDER_PATH}/TechnologyTitle.png"
RESEARCH_BUTTON = f"{FOLDER_PATH}/ResearchButton.png"
SPEED_UP = f"{FOLDER_PATH}/SpeedUp.png"            # nút Speed Up xanh (bên phải) của popup Researching
SPEED_UP_REGION = (50, 72, 100, 82)                # % màn hình, loại nút Speed Up kim cương bên trái
SPEEDUP_TITLE = f"{FOLDER_PATH}/SpeedupTitle.png"  # tiêu đề màn Research Speedup
FINISH_ALL = f"{FOLDER_PATH}/FinishAll.png"
SPEEDUP_SETTINGS = f"{FOLDER_PATH}/SpeedupSettings.png"   # "Speedup Settings >>" góc dưới trái màn Research Speedup
CONFIRM = f"{FOLDER_PATH}/Confirm.png"             # nút Confirm của popup Finish All
# Ô tích "You can use corresponding common speedups when special speedups are insufficient" của popup Finish All:
# chưa tích (lần đầu) thì phải tích trước khi Confirm. Hai ảnh khớp chéo 0,79, ảnh đúng 1,00.
COMMON_CHECKED = f"{FOLDER_PATH}/CommonChecked.png"
COMMON_UNCHECKED = f"{FOLDER_PATH}/CommonUnchecked.png"
COMMON_THRESHOLD = 0.9

TREE_Y = (190, 690)         # vùng cây công nghệ theo y (px, màn 396x704)
GREEN_LOW, GREEN_HIGH = (40, 150, 140), (85, 255, 255)   # HSV chữ "Lv N / M" xanh
LEVEL_SIZE = ((40, 70), (6, 14))   # (rộng, cao) px của chữ Lv sau khi nối chữ; icon xanh to hơn / nhỏ hơn
TREE_SWIPE = (50, 75, 50, 35)      # % màn hình, vuốt cây lên (cuộn xuống)
TREE_SWIPE_BACK = (50, 35, 50, 75)  # % màn hình, vuốt cây xuống (cuộn lên đầu) sau khi chuyển tab
TREE_END_DIFF = 2.0                # vuốt mà vùng cây đổi ít hơn mức xám trung bình này = đã hết cây
TREE_SCROLLS = 2                   # cuộn cây tối đa chừng này lần ở mỗi tab trước khi sang tab khác
# Bốn tab được kiểm tra (Advancement, Defense, Military, Medical Aid). Thanh tab tự cuộn khi chọn tab: tab đang
# chọn nằm giữa (x ~195), tab kế bên phải ở x ~320; riêng lúc đầu Advancement ở x ~75 nên Defense ở x ~195.
TAB_TAPS = ((49, 19), (81, 19), (81, 19))   # % màn hình, bấm lần lượt để sang tab 2, 3, 4
MENU_WAIT = 10                     # giây chờ màn Academy sau khi bấm icon Research
POPUP_WAIT = 4                     # giây chờ màn Technology / popup / màn Speedup hiện
RESULT_WAIT = 2                    # giây chờ sau khi bấm Research / Confirm
INFO_BOX = (20, 235, 356, 210)     # (x, y, rộng, cao) vùng cấp / điều kiện / chi phí của màn Technology (không có nút Research,
                                   # không có thông báo nổi): đổi sau khi bấm Research = nghiên cứu xong ngay (cấp, chi phí đổi)
PIXEL_DIFF = 40                    # độ lệch mức xám coi là điểm ảnh đã đổi
CHANGED_PIXELS = 40                # số điểm ảnh đổi tối thiểu (đo: nghiên cứu xong ngay 118, không đổi 0)
BACKS_AFTER = 6                    # xong: Back (tối đa chừng này lần) tới khi về thành
