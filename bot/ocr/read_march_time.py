"""
read_march_time.py — giờ ở màn March (Gather Resources): thời gian thu thập cạnh đồng hồ cát "00:48:57" và thời gian đi
dưới nút March "00:02:31" -> số giây.

Chữ trắng trên nền tối, tách chữ giống read_bubble_time (mask theo màu sáng) nhưng font nhỏ hơn nên có bộ mẫu riêng
Images/OCR/MarchTime. Đọc từ phải sang trái tới khi gặp mảnh không nhận ra (icon đồng hồ bên trái), nên vùng cắt được phép
rộng hơn phần số.
"""
import re

import numpy as np

from ._digits import MIN_SCORE, _normalize, _samples
from .read_bubble_time import split

FONT = "MarchTime"
_CLOCK = re.compile(r"(\d+):(\d{2}):(\d{2})")     # 00:48:57

__all__ = ["FONT", "run", "split"]


def _char(piece: np.ndarray) -> str | None:
    labels, samples = _samples(FONT)
    scores = samples @ _normalize(piece)
    best = int(scores.argmax())
    return labels[best] if scores[best] >= MIN_SCORE else None


def run(image: np.ndarray) -> int | None:
    """Số giây, hoặc None nếu không đọc được."""
    text = ""
    for piece in reversed(split(image)):
        if isinstance(piece, str):
            if piece != ":" or text.count(":") == 2:
                break
            text = ":" + text
            continue
        char = _char(piece)
        if char is None:
            break
        text = char + text
    match = _CLOCK.fullmatch(text)
    if match is None:
        return None
    hours, minutes, seconds = map(int, match.groups())
    if minutes >= 60 or seconds >= 60:
        return None
    return hours * 3600 + minutes * 60 + seconds
