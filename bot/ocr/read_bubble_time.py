"""
read_bubble_time.py — thời gian bubble còn lại trên thanh xanh (City Buff,
dòng Truce Agreement) hoặc sau "Remaining Time:" (Use Item) -> số giây.
Dưới 1 ngày game hiện "06:55:22" (giờ:phút:giây), từ 1 ngày trở lên hiện
"2d 23:38" (ngày, giờ:phút).

Chữ màu kem trên nền thanh xanh lá / xám tối: tách chữ theo màu (R, G, B
đều sáng; nền xanh có R thấp), chỉ giữ dải hàng của chữ để bỏ vệt sáng ở mép
thanh. Đọc từ phải sang trái tới dấu ":" của nhãn "Remaining Time:" (dấu ":"
thứ ba, hoặc dấu ":" sau chữ "d") hoặc mảnh không nhận ra, nên vùng cắt được
phép rộng hơn phần số.
"""
import re

import cv2
import numpy as np

from ._digits import MIN_SCORE, _normalize, _samples
from ._digits import split as split_digits

FONT = "Timer"
_CLOCK = re.compile(r"(\d+):(\d{2}):(\d{2})")     # 06:55:22
_DAYS = re.compile(r"(\d+)d(\d{1,2}):(\d{2})")     # 2d 23:38 (dấu cách không thành mảnh)


def mask(image: np.ndarray) -> np.ndarray:
    """Ảnh BGR -> ảnh đen trắng chỉ còn chữ (255) trong dải hàng của chữ."""
    b, g, r = (image[..., i].astype(int) for i in range(3))
    bw = ((r > 170) & (g > 170) & (b > 120)).astype(np.uint8) * 255
    count, _, stats, _ = cv2.connectedComponentsWithStats(bw)
    heights = [stats[i, cv2.CC_STAT_HEIGHT] for i in range(1, count)]
    if not heights:
        return bw
    # Dải hàng của chữ số: các mảnh cao gần bằng mảnh cao nhất.
    tall = [i for i in range(1, count) if stats[i, cv2.CC_STAT_HEIGHT] >= max(heights) * 0.6]
    top = min(stats[i, cv2.CC_STAT_TOP] for i in tall)
    bottom = max(stats[i, cv2.CC_STAT_TOP] + stats[i, cv2.CC_STAT_HEIGHT] for i in tall)
    bw[:top] = 0
    bw[bottom:] = 0
    return bw


def split(image: np.ndarray) -> list:
    """Ảnh BGR -> mảnh trái -> phải (ảnh chữ hoặc ":"), dùng cho add_sample."""
    if image.size == 0:
        return []
    return split_digits(mask(image))


def ink(image: np.ndarray) -> bool:
    """Vùng có chữ sáng nào không (không có = không có thanh thời gian)."""
    return image.size > 0 and bool(mask(image).any())


def _char(piece: np.ndarray) -> str | None:
    """Chữ số hoặc "d" của mảnh, None nếu không giống mẫu nào."""
    labels, samples = _samples(FONT)
    scores = samples @ _normalize(piece)
    best = int(scores.argmax())
    return labels[best] if scores[best] >= MIN_SCORE else None


def run(image: np.ndarray) -> int | None:
    """Số giây còn lại, hoặc None nếu không đọc được."""
    text = ""
    for piece in reversed(split(image)):
        if isinstance(piece, str):
            # Dấu ":" thứ ba / sau "d" là của nhãn "Remaining Time:".
            if piece != ":" or text.count(":") == 2 or "d" in text:
                break
            text = ":" + text
            continue
        char = _char(piece)
        if char is None:
            break
        text = char + text
    match = _DAYS.fullmatch(text)
    if match is not None:
        days, hours, minutes = map(int, match.groups())
        if hours >= 24 or minutes >= 60:
            return None
        return days * 86400 + hours * 3600 + minutes * 60
    match = _CLOCK.fullmatch(text)
    if match is None:
        return None
    hours, minutes, seconds = map(int, match.groups())
    if minutes >= 60 or seconds >= 60:
        return None
    return hours * 3600 + minutes * 60 + seconds
