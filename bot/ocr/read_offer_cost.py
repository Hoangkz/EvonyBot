"""
read_offer_cost.py — số kim cương ở ô "Cost" của popup Offer Gems (Daily Activities / Offering):
"126,175" -> 126175.

Chữ vàng trên nền be-nâu, ngay sau icon kim cương (xanh nhạt): tách chữ theo màu vàng (HSV) rồi theo
vùng liên thông; dấu "," là khối thấp riêng (bỏ qua); khối rộng (chữ số dính nhau) chia theo PITCH.
So với font riêng Images/OCR/OfferCost. Ảnh vào là vùng CROP (x, y, w, h) trên màn 396x704.
"""
import re

import cv2
import numpy as np

from ._digits import read_chars
from .read_progress import _trim

FONT = "OfferCost"
CROP = (195, 370, 110, 22)   # chữ số từ x 199 (6 chữ số) .. 254, y 375 .. 388
PITCH = 8                    # mỗi chữ số ~8 px
SNAP = 2                     # chữ số dính nhau: dời chỗ cắt tới cột ít điểm ảnh nhất trong ±SNAP px
HUE = (12, 38)               # vàng
MIN_SATURATION = 100
MIN_VALUE = 150


def split(image: np.ndarray) -> list:
    """Ảnh BGR ô Cost -> mảnh trái -> phải (ảnh chữ số đen trắng, "," cho dấu phẩy)."""
    if image.size == 0:
        return []
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    bw = (((h >= HUE[0]) & (h <= HUE[1]) & (s >= MIN_SATURATION) & (v >= MIN_VALUE)) * 255
          ).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(bw, connectivity=8)
    blobs = sorted((tuple(int(x) for x in stats[i][:4]), i) for i in range(1, count)
                   if stats[i][cv2.CC_STAT_AREA] > 2)
    if not blobs:
        return []
    # Chiều cao chữ số = chiều cao hay gặp nhất (dấu "," dính vào chữ số trước làm khối cao hơn).
    heights = [bh for (_, _, _, bh), _ in blobs]
    height = max(set(heights), key=heights.count)
    top = min(y for (_, y, _, bh), _ in blobs if bh == height)
    chars = []
    for (x, y, w, bh), label in blobs:
        if bh < height * 0.6:
            chars.append(",")
            continue
        blob = ((labels[y:y + bh, x:x + w] == label) * 255).astype(np.uint8)
        below = top + height - y   # hàng đầu tiên dưới chân chữ số
        if 0 < below < bh:
            # Dấu "," dính vào chữ số trước / sau (VD "2,075", "1,475"): cột có nét thò xuống dưới
            # chân là dấu phẩy -> tách khối thành phần trái, ",", phần phải.
            comma = np.flatnonzero(blob[below:].any(axis=0))
            if comma.size:
                body = blob[:below]
                for part in (body[:, :comma[0]], None, body[:, comma[-1] + 1:]):
                    if part is None:
                        chars.append(",")
                    elif part.any():
                        chars.extend(_digits_of(part))
                continue
            blob = blob[:below]
        chars.extend(_digits_of(blob))
    return chars


def _digits_of(part: np.ndarray) -> list:
    """Khối đen trắng `part` (một hay nhiều chữ số dính nhau) -> các chữ số: số chữ số theo PITCH (x,5 làm
    tròn xuống: "1" có chân đế rộng, "150" dính liền rộng 27 px là 3 chữ số), cắt ở cột ít điểm ảnh nhất
    trong khoảng ±SNAP quanh chỗ chia đều."""
    part = _trim(part)
    w = part.shape[1]
    digits = max(1, int((w + 1) / PITCH + 0.4))
    density = (part > 0).sum(axis=0)
    cuts = [0]
    for k in range(1, digits):
        even = k * w // digits
        lo, hi = max(cuts[-1] + 1, even - SNAP), min(w - 1, even + SNAP)
        cuts.append(lo + int(np.argmin(density[lo:hi + 1])) if lo <= hi else even)
    cuts.append(w)
    pieces = [_trim(part[:, a:b]) for a, b in zip(cuts, cuts[1:])]
    return [p for p in pieces if p.size and p.any()]


def run(image: np.ndarray) -> int | None:
    """Số kim cương trong ảnh BGR ô Cost (vùng CROP), hoặc None nếu đọc lỗi."""
    chars = split(image)
    pieces = [c for c in chars if not isinstance(c, str)]
    if not pieces:
        return None
    digits = re.sub(r"\D", "", read_chars(chars, FONT) or "")
    return int(digits) if len(digits) == len(pieces) else None
