"""
city — bản đồ thành và đường đi giữa các công trình (dùng chung, không thuộc activity nào): activity (VD Black Market) và worker (tìm
route khi rảnh) cùng gọi.

- city_map.py:  tìm công trình trên màn, vuốt tới công trình (goto), quét thành (scan), tìm Thành chính (find_keep), tìm route khi
                rảnh (scan_city); bản đồ lưu DB (cột devices.city_map)
- city_tour.py: dữ liệu tĩnh theo nền văn minh (hiện chỉ civ1): công trình cố định (FIXED), đường vuốt giữa chúng (ROUTES), 13 ô quét (DATA)
- FLOW.md:      luồng + hướng dẫn đo route cho một nền văn minh
- TODO.md:      việc còn lại
"""
from .. import activities  # noqa: F401 — nạp bot.activities trước: city_map dùng hằng số của activity, activity (Black Market) lại gọi city_map
