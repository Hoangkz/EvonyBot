"""Đọc thời gian đã trôi qua ở phần bên phải nhãn Server Time."""
import re
from datetime import datetime, timedelta

import cv2
import numpy as np

from ._digits import read_chars, split


def parse_elapsed(text: str) -> timedelta | None:
    """Bỏ phần ngày; coi HH:MM[:SS] là thời lượng đã trôi qua theo quy ước của bot."""
    # OCR hiện có nhận dấu gạch ngang thành dấu phẩy và bỏ khoảng trắng.
    match = re.fullmatch(
        r"(\d{4})[-,](\d{2})[-,](\d{2})\s*(\d{2}):(\d{2})(?::(\d{2}))?",
        text.strip(),
    )
    if match is None:
        return None
    year, month, day, hours, minutes = map(int, match.groups()[:5])
    seconds = int(match.group(6) or 0)
    try:
        # Kiểm tra ngày/giờ hợp lệ để tránh lưu kết quả OCR sai định dạng.
        datetime(year, month, day, hours, minutes, seconds)
    except ValueError:
        return None
    return timedelta(hours=hours, minutes=minutes, seconds=seconds)


def run(image: np.ndarray) -> timedelta | None:
    """Ảnh BGR chứa YYYY-MM-DD HH:MM[:SS] -> thời lượng, hoặc None nếu đọc lỗi."""
    if image.size == 0:
        return None
    # Lọc chữ vàng, loại nền tối/đường viền trước khi tách chữ số.
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array([10, 100, 110]), np.array([40, 255, 255]))
    text = read_chars(split(mask), "Server")
    return parse_elapsed(text) if text else None
