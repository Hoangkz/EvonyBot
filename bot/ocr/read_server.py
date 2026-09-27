"""
read_server.py — số server trong dòng "Empire Name: S. 1257" (vùng ảnh
ngay sau chữ "Empire Name:").
"""
import cv2
import numpy as np

from ._digits import read_chars, split

FONT = "Server"
MAX_RATIO = 1.0     # chữ số rộng hơn chiều cao -> 2 số dính nhau (VD: "44")


def run(image: np.ndarray) -> str | None:
    """Số server (VD: "1257") trong `image` (BGR) — phần sau "S.", hoặc None
    nếu không đọc được."""
    if image.size == 0:
        return None
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Chữ tối trên nền sáng -> đảo màu để chữ thành phần sáng (split cần vậy).
    if np.median(gray) > 127:
        gray = 255 - gray
    chars = split(gray, MAX_RATIO)
    # Bỏ chữ "S" và dấu "." phía trước, chỉ giữ phần sau dấu chấm.
    dots = [i for i, c in enumerate(chars) if isinstance(c, str) and c == ","]
    if not dots:
        return None
    chars = chars[dots[0] + 1:]
    text = read_chars(chars, FONT)
    if text is None or not text.isdigit():
        return None
    return text
