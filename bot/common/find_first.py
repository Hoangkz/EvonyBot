"""
find_first.py — the first known image on a screenshot.
"""
from ..context import DEFAULT_THRESHOLD

# Ảnh luôn chỉ tìm trong vùng cố định (%), mọi nhiệm vụ: nút Liên minh ở màn chính (~91%, 79%). Ảnh là phần giữa chữ
# "Alliance" (32x8): khớp >= 0,99 trên mọi màn chính (nền thành khác nhau), nhưng chữ "Alliance" ở tiêu đề màn Alliance
# Science cũng khớp 0,94 nên không được tìm cả màn hình. Trong vùng này ảnh khác khớp nhầm cao nhất 0,78.
FIXED_REGIONS = {"JoinBoss/lienminh.png": (75, 70, 100, 90)}
FIXED_THRESHOLDS = {"JoinBoss/lienminh.png": 0.85}   # ngưỡng riêng của các ảnh trên (khớp nhầm trong vùng <= 0,78)


def _near_position(screen, position, padding):
    """Return a percentage region around a previously matched position."""
    height, width = screen.shape[:2]
    x, y = position
    pad_x, pad_y = padding
    center_x, center_y = x * 100 / width, y * 100 / height
    return (max(0, center_x - pad_x), max(0, center_y - pad_y),
            min(100, center_x + pad_x), min(100, center_y + pad_y))


def find_first(bot, screen, targets, top_left=(), regions=None, thresholds=None, *,
               position_cache=None, cache_padding=(14, 10), fallback_full=False):
    """First (action, pos) in `targets` — a list of (image path, action)
    checked in order — whose image is on `screen`, else (None, None).
    `pos` is the image's center, or its top-left corner for the actions in
    `top_left` (those tap at an offset from that corner).
    `regions` ({ảnh: (x0, y0, x1, y1) %}): ảnh có trong đó chỉ được tìm trong
    vùng của nó; ảnh không có thì tìm cả màn hình.
    `thresholds` ({ảnh: ngưỡng}): ngưỡng riêng; ảnh không có dùng DEFAULT_THRESHOLD.
    `position_cache`: {ảnh: vị trí lần khớp gần nhất}. Khi có, lần sau chỉ tìm
    quanh vị trí đó trước; `fallback_full=True` sẽ tìm lại toàn màn hình nếu
    giao diện đã dịch chuyển. Đây là ROI thích nghi, không làm mất khả năng
    phục hồi khi danh sách cuộn hoặc popup đổi vị trí."""
    regions = regions or {}
    thresholds = thresholds or {}
    for path, action in targets:
        search_regions = []
        if position_cache is not None and path in position_cache:
            search_regions.append(_near_position(screen, position_cache[path], cache_padding))
        configured = regions.get(path, FIXED_REGIONS.get(path))
        if configured is not None and configured not in search_regions:
            search_regions.append(configured)
        if not search_regions or (fallback_full and path not in FIXED_REGIONS):
            search_regions.append(None)

        for region in search_regions:
            pos = bot.find(path, threshold=thresholds.get(path, FIXED_THRESHOLDS.get(path, DEFAULT_THRESHOLD)), screen=screen,
                           center=action not in top_left, region=region)
            if pos is not None:
                if position_cache is not None:
                    position_cache[path] = pos
                return action, pos
    return None, None
