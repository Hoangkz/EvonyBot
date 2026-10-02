"""
find_first.py — the first known image on a screenshot.
"""
from ..context import DEFAULT_THRESHOLD


def find_first(bot, screen, targets, top_left=(), regions=None, thresholds=None):
    """First (action, pos) in `targets` — a list of (image path, action)
    checked in order — whose image is on `screen`, else (None, None).
    `pos` is the image's center, or its top-left corner for the actions in
    `top_left` (those tap at an offset from that corner).
    `regions` ({ảnh: (x0, y0, x1, y1) %}): ảnh có trong đó chỉ được tìm trong
    vùng của nó; ảnh không có thì tìm cả màn hình.
    `thresholds` ({ảnh: ngưỡng}): ngưỡng riêng; ảnh không có dùng DEFAULT_THRESHOLD."""
    regions = regions or {}
    thresholds = thresholds or {}
    for path, action in targets:
        pos = bot.find(path, threshold=thresholds.get(path, DEFAULT_THRESHOLD), screen=screen,
                       center=action not in top_left, region=regions.get(path))
        if pos is not None:
            return action, pos
    return None, None
