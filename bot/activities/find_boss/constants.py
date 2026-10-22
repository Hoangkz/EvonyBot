"""
constants.py — Find Boss: key lưu DB, nút chuyển bản đồ, giá trị mặc định của tab.
"""
KEY = "find_boss"                  # key nhiệm vụ trong priority.py / daily_done (lỗi lưu `find_boss_error`)

# Cùng một nút ở góc dưới phải đổi giữa thành <-> bản đồ thế giới: ở thành bấm nó để ra thế giới (chưa có ảnh mẫu, bấm theo % màn hình
# vào chỗ nút toCity.png nằm trên màn thế giới).
TO_WORLD_TAP = (92, 93)            # % màn hình
TO_WORLD_WAIT = 4                  # giây chờ game chuyển sang bản đồ thế giới
TO_WORLD_TRIES = 3

# Tab (settings["Find Boss"]): key -> mặc định
START_KEY, START_DEFAULT = "start_deg", 0          # góc màn hình bắt đầu (0° = phải, ngược chiều kim đồng hồ)
END_KEY, END_DEFAULT = "end_deg", 360              # góc kết thúc (360 - bắt đầu = cả vòng)
RADIUS_KEY, RADIUS_DEFAULT = "radius", 300       # km
SHARE_KEY, SHARE_DEFAULT = "share", True           # chia sẻ boss đang tích vào liên minh
BOSSES_KEY = "selected_bosses"                     # [{"category_key", "name", "levels": [...]}, ...] như tab Join Monster War; chỉ tìm boss được tích
EXCLUDED_BOSSES = ("Viking",)                      # không có trong danh sách chọn của tab, không tìm
ANGLE_STEP = 15                                   # các góc chọn được: 0, 15, ... 360
RADIUS_MAX = 600
