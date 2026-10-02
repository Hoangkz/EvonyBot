"""
read_milestone.py — tiến độ rương mốc "Progress:12 / 70" dưới hàng rương ở đầu màn Gather
Troops -> số đã làm (12).

Chữ trắng ngà, mảnh (cao ~8 px), nằm trên thanh tiến độ màu cam / nâu nên ngưỡng Otsu tách
cả nền: lọc theo màu (cả 3 kênh > _MIN — chữ ít bão hoà, thanh cam có kênh xanh dương thấp).
Dòng chữ căn giữa nên vị trí số đổi theo số chữ số: bỏ mọi thứ bên trái dấu ":" (cột hẹp có
hai chấm tách rời), phần còn lại chia mảnh như read_progress ("/" nhận theo hình dạng).
Mẫu chữ số: Images/OCR/Milestone/ (add_sample.py, VD "1|2|/|7|0").
"""
import re

import numpy as np

from ._digits import read_chars
from .read_progress import _groups, _runs

FONT = "Milestone"
_MIN = 95   # cả 3 kênh màu > mức này = điểm ảnh của chữ


def _binarize(image: np.ndarray) -> np.ndarray:
    return ((image.min(axis=2) > _MIN) * 255).astype(np.uint8)


def _is_colon(bw: np.ndarray, x0: int, x1: int) -> bool:
    """Cột hẹp (<= 2 px) mà các hàng có mực tách làm hai cụm (hai chấm của ":")."""
    if x1 - x0 > 2:
        return False
    rows = np.flatnonzero(bw[:, x0:x1].any(axis=1))
    return rows.size >= 2 and bool((np.diff(rows) > 1).any())


def split(image: np.ndarray) -> list:
    """Ảnh BGR cả dòng "Progress:12 / 70" -> mảnh sau dấu ":" trái -> phải: ảnh từng chữ số
    và "/"."""
    if image.size == 0:
        return []
    bw = _binarize(image)
    colons = [x1 for x0, x1 in _runs(bw) if _is_colon(bw, x0, x1)]
    if colons:
        bw = bw.copy()
        bw[:, :colons[-1]] = 0
    return _groups(bw)


def run(image: np.ndarray) -> int | None:
    """Số đã làm (bên trái "/") trong ảnh BGR dòng "Progress:<số> / <số>", hoặc None nếu
    đọc lỗi."""
    chars = split(image)
    slashes = [i for i, c in enumerate(chars) if isinstance(c, str) and c == "/"]
    if len(slashes) != 1:
        return None
    left = [c for c in chars[:slashes[0]] if not isinstance(c, str)]
    if not left:
        return None
    text = read_chars(left, FONT)
    digits = re.sub(r"\D", "", text or "")
    return int(digits) if digits and len(digits) == len(left) else None
