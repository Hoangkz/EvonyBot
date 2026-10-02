"""
constants.py — Event Center image folders, limits and action names (dùng chung mọi nhiệm vụ).

Toạ độ đo trên màn 396x704.
"""
EC = "EventCenter"

# Bấm CHÍNH nút Event Center (icon cúp ngay trên chữ "Event Center"), không phải nút event
# bên dưới như activity Event: lệch so với tâm chữ (tâm chữ (359, 241) -> cúp (359, 216)).
# Chữ "Event Center" tìm bằng event.common.find_event_center.
EVENT_CENTER_TAP_OFFSET = (0, -25)

# Hàng tab Limited / Activities / Competition của màn Event Center. Tiêu đề màn đổi theo
# event đầu danh sách (VD "Pan's Trials") nên nhận màn bằng chữ trên tab "Competition" (lúc nào
# cũng có): 1,00 khi đang ở tab Limited lẫn Activities; màn khác <= 0,55.
COMPETITION_TAB = f"{EC}/competitionTab.png"
# Tab cần mở (chỉ để bấm): ảnh chưa chọn và đang chọn khớp chéo nhau 0,91 -> không phân biệt,
# thấy ảnh nào cũng bấm rồi tìm icon (bấm tab đang chọn không sao). Mỗi ảnh 1,00 trên màn của
# nó; màn khác <= 0,48.
ACTIVITIES = "activities"
TABS = {
    ACTIVITIES: (f"{EC}/activitiesTab.png", f"{EC}/activitiesTabOn.png"),
}
TAB_REGION = (0, 5, 100, 18)   # % màn hình: hàng tab (cả 3 tab)
TAB_THRESHOLD = 0.85

# Danh sách event trong tab: không thấy icon thì cuộn xuống, quá LIST_MAX_SCROLLS lần vẫn
# không thấy thì BACK.
LIST_SWIPE = (50, 80, 50, 50)   # % màn hình, ngón tay kéo lên = cuộn danh sách xuống
LIST_MAX_SCROLLS = 8
# Không thấy tab cần mở / icon event (cuộn hết vẫn không có, VD danh sách bị cuộn sẵn quá icon):
# run_task_with_retry thử tới ATTEMPTS lần (mỗi lần BACK rồi vào lại Event Center), vẫn không được
# thì tắt game (force-stop; run_task tự mở lại qua go_home) rồi thử thêm AFTER_RESTART_ATTEMPTS lần.
ATTEMPTS = 3
AFTER_RESTART_ATTEMPTS = 2
RESTART_WAIT = 3   # giây chờ sau force-stop

# Số màn hình tối đa một lượt run_task.
MAX_STEPS = 40

# ---- Actions -----------------------------------------------------------
ON_EVENT_CENTER = "on_event_center"
ON_MAIN_SCREEN = "on_main_screen"
BACK, TAP = "back", "tap"
