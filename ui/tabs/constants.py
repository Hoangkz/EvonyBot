"""
constants.py — hằng số của các tab (ui/tabs).
"""
from bot.activities import EXCLUSIVE_ACTIVITIES

from ..theme import COLORS

# ---- Tab Initialization: bố cục (rebuild 1:1 từ Form3_Designer.cs) ----
DESIGNER_DATA = {
    "ButtonJoinMonsterWar": {"loc": [85, 53], "size": [230, 40], "text": "Join Monster War", "type": "Button"},
    "ButtonOpenGiftBox": {"loc": [85, 117], "size": [230, 40], "text": "Open Gift Box", "type": "Button"},
    "buttonEvent": {"loc": [740, 53], "size": [230, 40], "text": "Event", "type": "Button"},
    # button9 (Start All) nằm cạnh buttonStopAll (Stop All) dưới GroupBox; 2 nút
    # 125x40 (nhỏ lại so với 140x50 gốc) căn phải theo mép phải GroupBox (x=1075).
    "button9": {"loc": [815, 473], "size": [125, 40], "text": "Start All", "type": "Button"},
    "buttonStopAll": {"loc": [950, 473], "size": [125, 40], "text": "Stop All", "type": "Button"},
    "buttonAllianceCapacity": {"loc": [409, 117], "size": [230, 40], "text": "Alliance Capacity", "type": "Button"},
    "buttonBlackMarket": {"loc": [740, 117], "size": [230, 40], "text": "Black Market", "type": "Button"},
    "buttonRecruitGeneral": {"loc": [85, 181], "size": [230, 40], "text": "Recruit General", "type": "Button"},
    "buttonFindBoss": {"loc": [409, 181], "size": [230, 40], "text": "Find Boss", "type": "Button"},
    "buttonCraft": {"loc": [740, 181], "size": [230, 40], "text": "Craft", "type": "Button"},
    "buttonGatherResources": {"loc": [85, 245], "size": [230, 40], "text": "Gather Resources", "type": "Button"},
    "buttonDailyActivities": {"loc": [409, 53], "size": [230, 40], "text": "Daily Activities", "type": "Button"},
    "buttonInitializationApplyAll": {"loc": [935, 16], "size": [132, 43], "text": "Apply ALL", "type": "Button"},
    "buttonStart": {"loc": [449, 499], "size": [217, 51], "text": "Start", "type": "Button"},
    "groupBox2": {
        "children": ["ButtonJoinMonsterWar", "buttonDailyActivities", "buttonEvent", "ButtonOpenGiftBox",
                      "buttonAllianceCapacity", "buttonBlackMarket", "buttonRecruitGeneral", "buttonFindBoss", "buttonCraft", "buttonGatherResources"],
        "loc": [13, 150], "size": [1062, 305], "text": "Select Activity", "type": "GroupBox",
    },
    "checkBoxBubble": {"loc": [13, 62], "size": [75, 28], "text": "Bubble", "type": "CheckBox"},
    "comboBoxBubbleType": {"loc": [90, 62], "size": [60, 28], "type": "ComboBox"},
    "labelBubbleTime": {"loc": [158, 62], "size": [100, 28], "type": "Label"},
    "labelCivilization": {"loc": [180, 22], "size": [72, 28], "text": "Civilization:", "type": "Label"},
    "comboBoxCivilization": {"loc": [254, 22], "size": [100, 28], "type": "ComboBox"},
    "labelID": {"loc": [506, 18], "size": [200, 32], "text": "labelID", "type": "Label"},
    "labelServer": {"loc": [13, 22], "size": [48, 28], "text": "Server:", "type": "Label"},
    "textBoxServer": {"loc": [63, 22], "size": [100, 28], "type": "TextBox"},
    "tabPage1": {
        "children": ["button9", "buttonStopAll", "buttonInitializationApplyAll", "buttonStart",
                     "labelID",
                     "labelServer", "textBoxServer", "checkBoxBubble", "labelBubbleTime",
                     "comboBoxBubbleType", "labelCivilization", "comboBoxCivilization",
                     "groupBox2"],
        "loc": [4, 31], "size": [1088, 609], "text": "Initialization", "type": "TabPage",
    },
}
# Loại bubble (khiên) có thể dùng.
BUBBLE_TYPES = ["8h", "24h", "3d", "7d"]
DEFAULT_BUBBLE_TYPE = "24h"
# Nền văn minh: số 1..7 (devices.civilization) = vị trí trong danh sách; mục đầu = chưa biết (bot tự nhận).
CIVILIZATIONS = ["Europe", "China", "Japan", "Korea", "America", "Russia", "Arabia"]
CIVILIZATION_UNKNOWN = "(auto)"
COMBO_ITEMS = {"comboBoxBubbleType": BUBBLE_TYPES,
               "comboBoxCivilization": [CIVILIZATION_UNKNOWN, *CIVILIZATIONS]}
PAGE_SIZE = (1088, 609)
# Hàng hồ sơ (dưới Bubble, trên Select Activity): nhãn + các nút hồ sơ sát nhau + nút "+".
PROFILE_ROW_POS = (13, 104)
PROFILE_BUTTON_HEIGHT = 34
PROFILE_BUTTON_MIN_WIDTH = 70
PROFILE_BUTTON_GAP = 8   # khoảng cách giữa các nút hồ sơ và nút "+"
PROFILE_MAX = 5  # số hồ sơ tối đa mỗi thiết bị (không tính default ẩn)
PROFILE_NAME_MAX = 20   # số ký tự tối đa của tên hồ sơ; nút luôn hiện đủ tên

# ---- Tab Initialization: nút Select Activity ----

# Danh sách nút Select Activity: tên control -> {"target": tên activity (= tên tab), "exclusive": ...}.
# Original button.Tag values in the C# form matched the activity's display text, which in turn matches this app's
# tab titles. exclusive=True: activity chạy MỘT MÌNH — tích nó thì bỏ tích mọi nút khác, tích nút khác thì bỏ tích nó;
# (nguồn: bot.activities.EXCLUSIVE_ACTIVITIES, worker cũng đọc: activity exclusive không dính Bubble / nhiệm vụ khác)
# exclusive=False: chạy chung được với các activity còn lại.
ACTIVITY_BUTTONS = {
    "ButtonJoinMonsterWar": {"target": "Join Monster War", "exclusive": False},
    "buttonAllianceCapacity": {"target": "Alliance Capacity", "exclusive": False},
    "buttonDailyActivities": {"target": "Daily Activities", "exclusive": False},
    "ButtonOpenGiftBox": {"target": "Open Gift Box", "exclusive": False},
    "buttonBlackMarket": {"target": "Black Market", "exclusive": False},
    "buttonEvent": {"target": "Event", "exclusive": False},
    "buttonRecruitGeneral": {"target": "Recruit General", "exclusive": "Recruit General" in EXCLUSIVE_ACTIVITIES},
    "buttonFindBoss": {"target": "Find Boss", "exclusive": False},
    "buttonCraft": {"target": "Craft", "exclusive": False},
    "buttonGatherResources": {"target": "Gather Resources", "exclusive": False},
}
ACTIVITY_BUTTON_TARGETS = {name: info["target"] for name, info in ACTIVITY_BUTTONS.items()}

# Set on each button directly: the designer page's own "background: white"
# stylesheet would otherwise win over the app-level theme.
ACTIVITY_BUTTON_STYLE = f"""
QPushButton:checked {{
    background: {COLORS['success']};
    border-color: {COLORS['success']};
    color: white;
    font-weight: 600;
}}
QPushButton:checked:hover {{
    background: #28985f;
    color: white;
}}
"""

# ---- Tab Recruit General ----
RECRUIT_TAB_TITLE = "Recruit General"   # = tên activity = khoá settings (bot/activities/constants.py, database.TAB_COLUMNS)
RECRUIT_SETTING_GROUP = "Setting"
# Cách mua tướng ở màn chi tiết tướng (hai nút dưới cùng); chỉ một lựa chọn được tích.
RECRUIT_BUY_OPTIONS = ("Recruit General", "Buy General Token")
RECRUIT_BUY_DEFAULT = "Recruit General"
RECRUIT_BUY_KEY = "buy_with"   # key trong settings của tab: {"buy_with": "Recruit General" | "Buy General Token"}
# Số lần Refresh tối đa / số tướng mua tối đa mỗi lượt chạy; "ALL" (mặc định) = không giới hạn.
RECRUIT_ALL = "ALL"
RECRUIT_REFRESH_OPTIONS = (RECRUIT_ALL,) + tuple(range(100, 1001, 100))
RECRUIT_REFRESH_DEFAULT = RECRUIT_ALL
RECRUIT_REFRESH_KEY = "refresh_count"   # key trong settings của tab: {"refresh_count": "ALL" | 100..1000}
RECRUIT_REFRESH_TEXT = "Refresh count"
RECRUIT_GENERALS_GROUP = "Generals"
RECRUIT_GENERALS_KEY = "generals"   # key trong settings của tab: {"generals": [tên tướng đã tích, ...]}
RECRUIT_GENERAL_COUNT_OPTIONS = (1, 2, 3, 10, 15, 20, RECRUIT_ALL)   # số lượng cần mua của từng tướng (ô dưới ô tích)
RECRUIT_GENERAL_COUNT_DEFAULT = 1
RECRUIT_GENERAL_COUNTS_KEY = "general_counts"   # key trong settings của tab: {"general_counts": {tên tướng: 1|2|3|10|15|20|"ALL"}}
RECRUIT_CIV_ALL = "All"             # mục "không lọc" của ô chọn civ
RECRUIT_TYPE_ORDER = ("Ground Troop", "Mounted Troop", "Ranged Troop", "Siege Machine", "Defense", "Mixed",
                      "Administration", "Duty", "Subordinate City")   # thứ tự ô chọn type như trong game
RECRUIT_TYPE_ALL = "All"                #  mục "không lọc" của ô chọn type (type1)
RECRUIT_SEARCH_PLACEHOLDER = "Search general name..."
GENERAL_COUNT_WIDTH = 64   # độ rộng (px) ô chọn số lượng, đủ hiện "10" / "ALL"
GENERAL_NAME_WIDTH = 110   # độ rộng cố định (px) của tên tướng, dài hơn thì xuống dòng
GENERAL_COLUMNS = 4   # số cột ô tích tướng trong group Generals
RECRUIT_OPEN_GOLD_TEXT = "Open Gold"
RECRUIT_OPEN_GOLD_KEY = "open_gold"   # key trong settings của tab: {"open_gold": bool}, mặc định tắt
RECRUIT_SELECT_ALL_TEXT = "Select All"
RECRUIT_DESELECT_ALL_TEXT = "Deselect All"
RECRUIT_RESET_TEXT = "Reset"
RECRUIT_SELECTED_NAME_WIDTH = 150   # độ rộng cố định (px) của "tên xN" trong danh sách tướng đã chọn
RECRUIT_SELECTED_GROUP = "Selected generals"   # group bao danh sách tướng đã tích trong group Setting
RECRUIT_PICKER_HEIGHT = 170    # chiều cao tối thiểu (px) lưới chọn tướng; cả tab vừa một màn hình, không cuộn dọc
RECRUIT_SELECTED_ROWS = 3      # số hàng hiện cùng lúc của danh sách tướng đã chọn, nhiều hơn thì cuộn dọc
RECRUIT_SELECTED_SPACING = 4   # khoảng cách dọc (px) giữa các hàng
RECRUIT_SELECTED_COLUMNS = 4   # số cột của danh sách tướng đã chọn (thêm tướng thì thêm hàng, cuộn dọc)
