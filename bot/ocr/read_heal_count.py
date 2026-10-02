"""
read_heal_count.py — số lính bị thương của một dòng ở màn Hospital (King's Path Heal): ô
"0 / 8,147" -> 8147 (số bên phải "/"; bên trái là số đang chọn).

Chữ nhỏ, số bên phải màu be mờ trên nền nâu có vân nên không dùng Otsu: lấy điểm sáng hơn
THRESHOLD, xoá mọi cột tới hết dấu "/", phần còn lại tách theo vùng liên thông (dấu "," là khối
thấp riêng — tách theo cột thì "," dính vào chữ số trước nó); khối rộng là nhiều chữ số dính nhau
(font đơn cách PITCH px) -> chia đều. So với font riêng Images/OCR/HealCount.
Ảnh vào là vùng CROP (so với tâm nút Dismiss của dòng) — cao 12 px: rộng hơn sẽ dính viền dưới ô
số làm dấu "/" không tách được.
"""
import re

import cv2
import numpy as np

from ._digits import read_chars
from .read_progress import _is_slash, _runs, _trim

FONT = "HealCount"
THRESHOLD = 105      # chữ be ~110-150, nền ô <= ~100
PITCH = 6            # mỗi chữ số chiếm 6 px (5 px nét + 1 px khoảng; "1" hẹp hơn)
CROP = (-93, -38, 130, 12)   # (dx, dy, w, h) so với tâm nút Dismiss của dòng


def split(image: np.ndarray) -> list:
    """Ảnh BGR ô số -> mảnh bên phải "/" trái -> phải (ảnh chữ số, ","); [] nếu không thấy
    đúng một dấu "/"."""
    if image.size == 0:
        return []
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    bw = ((gray > THRESHOLD) * 255).astype(np.uint8)
    slashes = [x1 for x0, x1 in _runs(bw) if _is_slash(_trim(bw[:, x0:x1]))]
    if len(slashes) != 1:
        return []
    bw[:, :slashes[0]] = 0
    count, labels, stats, _ = cv2.connectedComponentsWithStats(bw, connectivity=4)
    # Khối 1 px là nhiễu nền.
    blobs = sorted((tuple(int(v) for v in stats[i][:4]), i) for i in range(1, count)
                   if stats[i][cv2.CC_STAT_AREA] > 1)
    if not blobs:
        return []
    height = max(h for (_, _, _, h), _ in blobs)
    chars = []
    for (x, y, w, h), label in blobs:
        if h < height * 0.5:
            chars.append(",")
            continue
        blob = ((labels[y:y + h, x:x + w] == label) * 255).astype(np.uint8)
        digits = max(1, round((w + 1) / PITCH))
        for k in range(digits):
            piece = _trim(blob[:, k * w // digits:(k + 1) * w // digits])
            if piece.size:
                chars.append(piece)
    return chars


def run(image: np.ndarray) -> int | None:
    """Số lính bị thương (bên phải "/") trong ảnh BGR ô số, hoặc None nếu đọc lỗi."""
    chars = split(image)
    pieces = [c for c in chars if not isinstance(c, str)]
    if not pieces:
        return None
    text = read_chars(chars, FONT) or ""
    digits = re.sub(r"\D", "", text)
    return int(digits) if len(digits) == len(pieces) else None
