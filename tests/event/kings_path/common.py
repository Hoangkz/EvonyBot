"""
common.py — phần dùng chung của các test King's Path: thư mục ảnh chung screens/, biến thể ảnh, hàm chạy
flow (_run). Mỗi nhiệm vụ có thư mục test riêng (patrol/, donate/, ...); ảnh vẫn nằm ở screens/ này.
"""
from pathlib import Path

from bot.activities import event
from bot.activities.event.kings_path.black_market.constants import SLOTS as BM_SLOTS
from tests.event import run_event_tasks
from tests.flow import run_flow

SCREENS = Path(__file__).parent / "screens"

KP = "Event/KingsPath"

EVENT_BUTTON = (361, 280)   # nút event: đuôi ruy băng cột phải (331, 308) + (30, -28)

def _blank(y0, y1, x0, x1):
    """Biến thể ảnh: tô đen một vùng."""
    def fn(bgr):
        bgr[y0:y1, x0:x1] = 0
        return bgr
    return fn

def _sold_out(bgr):
    """Black Market: mọi nút giá xám (đã mua hết) — tô đen 6 nút giá."""
    for x, y in BM_SLOTS:
        bgr[y - 10:y + 10, x - 44:x + 44] = 40
    return bgr

VARIANTS = {
    # Black Market đã mua hết 6 món (nút giá không còn xanh).
    "sold_out": _sold_out,
    # Màn chính đã nhận quà: không còn icon Login Gifts (cột phải + góc dưới trái).
    "main_claimed": lambda bgr: _blank(525, 575, 0, 60)(_blank(130, 170, 330, 396)(bgr)),
    # Đã bấm Claim All: xoá nút Claim All ở đáy màn.
    "claimed": _blank(655, 695, 140, 256),
    # Màn event cùng khung nhưng không phải King's Path (VD Gather Troops): xoá tiêu đề.
    "not_kp": _blank(5, 40, 120, 280),
    # Refine: thanh trang bị không có món viền xanh — tô đen 2 món xanh (x 94, 249).
    "no_blue": lambda bgr: _blank(555, 602, 70, 118)(_blank(555, 602, 225, 273)(bgr)),
    # Refine: thanh trang bị trống (không có món nào).
    "no_items": _blank(550, 606, 0, 396),
    # Bấm nút event mà chưa vào được danh sách: không có tiêu đề "Wine Festival Event", không có
    # icon King's Path (45, 512).
    "no_list": lambda bgr: _blank(0, 45, 40, 356)(_blank(470, 555, 0, 100)(bgr)),
}

def _run(testcase, flow, settings, **kw):
    return run_flow(testcase, run_event_tasks, SCREENS, flow, settings, variants=VARIANTS, **kw)

WALLS_POS = (246, 345)
