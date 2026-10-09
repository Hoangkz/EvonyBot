"""
black_market — activity "Black Market": mua các món được tích ở tab Black Market (Chợ -> Black Market), Instant
Refresh rồi mua tiếp tới khi gặp điều kiện dừng.

- run.py:       `run(bot, settings)` — mở màn Black Market, quét 6 ô, mua, refresh (gộp Market cũ vào đây)
- constants.py: vùng / ngưỡng nhận diện món, điều kiện dừng
- city_map.py:  bản đồ thành theo thiết bị (DB) để tới Chợ khi không có Go; vòng quét: city_tour.py
- items.py:   danh mục vật phẩm (tab UI dựng ô tích từ đây), icon ở Images/Black Market/Items/
- TODO.md:      việc còn lại
"""
from .run import run

__all__ = ["run"]
