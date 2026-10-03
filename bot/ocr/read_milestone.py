"""
read_milestone.py — tiến độ rương mốc "Progress:12 / 70" dưới hàng rương ở đầu màn Gather
Troops -> số đã làm (12).

Chữ trắng ngà, mảnh (cao ~8 px), nằm trên thanh tiến độ màu cam / nâu nên ngưỡng Otsu tách
cả nền: lọc theo màu (cả 3 kênh > ngưỡng — chữ ít bão hoà, thanh cam có kênh xanh dương thấp).
Độ sáng chữ đổi theo màn (VD tối hơn khi băng "Congratulations!" đang hiện: ngưỡng 95 đọc được
màn thường, màn đó cần 55..65) -> thử lần lượt _THRESHOLDS, chỉ nhận khi số bên phải "/" đúng
`total` (mốc cuối, VD 70) để không nhận nhầm khi ngưỡng lệch.
Dòng chữ căn giữa nên vị trí số đổi theo số chữ số: bỏ mọi thứ bên trái dấu ":" (cột hẹp có
hai chấm tách rời), phần còn lại chia mảnh như read_progress ("/" nhận theo hình dạng).
Mẫu chữ số: Images/OCR/Milestone/ (add_sample.py, VD "1|2|/|7|0").
"""
import re

import numpy as np

from ._digits import read_chars
from .read_progress import _groups, _runs

FONT = "Milestone"
# Cả 3 kênh màu > ngưỡng = điểm ảnh của chữ. Mẫu chữ số cắt ở ngưỡng đầu (95).
_THRESHOLDS = (95, 85, 75, 65, 55)


def _binarize(image: np.ndarray, threshold: int = _THRESHOLDS[0]) -> np.ndarray:
    return ((image.min(axis=2) > threshold) * 255).astype(np.uint8)


def _is_colon(bw: np.ndarray, x0: int, x1: int) -> bool:
    """Cột hẹp (<= 2 px) mà các hàng có mực tách làm hai cụm (hai chấm của ":")."""
    if x1 - x0 > 2:
        return False
    rows = np.flatnonzero(bw[:, x0:x1].any(axis=1))
    return rows.size >= 2 and bool((np.diff(rows) > 1).any())


def split(image: np.ndarray, threshold: int = _THRESHOLDS[0]) -> list:
    """Ảnh BGR cả dòng "Progress:12 / 70" -> mảnh sau dấu ":" trái -> phải: ảnh từng chữ số
    và "/"."""
    if image.size == 0:
        return []
    bw = _binarize(image, threshold)
    colons = [x1 for x0, x1 in _runs(bw) if _is_colon(bw, x0, x1)]
    if colons:
        bw = bw.copy()
        bw[:, :colons[-1]] = 0
    return _groups(bw)


def run(image: np.ndarray, total: int | None = None) -> int | None:
    """Số đã làm (bên trái "/") trong ảnh BGR dòng "Progress:<số> / <số>", hoặc None nếu
    đọc lỗi. Có `total`: chỉ nhận khi số bên phải "/" bằng `total`."""
    for threshold in _THRESHOLDS:
        chars = split(image, threshold)
        slashes = [i for i, c in enumerate(chars) if isinstance(c, str) and c == "/"]
        if len(slashes) != 1:
            continue
        left = _number(chars[:slashes[0]])
        right = _number(chars[slashes[0] + 1:])
        if left is None or right is None or (total is not None and right != total):
            continue
        return left
    return None


def _number(pieces) -> int | None:
    """Các mảnh chữ số -> số, None nếu không có mảnh hoặc có mảnh đọc lỗi."""
    digits = [c for c in pieces if not isinstance(c, str)]
    if not digits:
        return None
    text = re.sub(r"\D", "", read_chars(digits, FONT) or "")
    return int(text) if len(text) == len(digits) else None
