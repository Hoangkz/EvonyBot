"""
read_input_bar.py — số đang gõ trong thanh nhập số ở đáy màn hình (Hospital: bấm ô số lượng -> ô trắng chữ đen, nút OK bên phải;
VD "30000"). Font hệ thống của Android, mẫu riêng Images/OCR/InputBar. Con trỏ nhập nhấp nháy màu xanh ngay sau số nên chỉ lấy điểm
tối ở cả 3 kênh màu (chữ đen / xám đậm), điểm xanh của con trỏ bị loại.
"""
import re

import numpy as np

from ._digits import read_chars, split as split_digits

FONT = "InputBar"
DARK = 140   # điểm có cả 3 kênh màu < mức này là chữ (chữ ~0-60; con trỏ xanh có kênh B cao; nền trắng 255)
MIN_WIDTH = 3   # chữ số "1" rộng 4 px; con trỏ nhập nhấp nháy sau số hẹp hơn (1-2 px, đôi khi còn lọt qua DARK): bỏ mảnh hẹp hơn mức này


def mask(image: np.ndarray) -> np.ndarray:
    """Ảnh BGR -> ảnh đen trắng chỉ còn chữ (255)."""
    return (image.max(axis=2) < DARK).astype(np.uint8) * 255


def split(image: np.ndarray) -> list:
    """Ảnh BGR -> mảnh trái -> phải (ảnh từng chữ số, ",": mảnh thấp), dùng cho lấy mẫu; con trỏ nhập bị bỏ."""
    if not image.size:
        return []
    return [piece for piece in split_digits(mask(image)) if isinstance(piece, str) or piece.shape[1] >= MIN_WIDTH]


def run(image: np.ndarray) -> int | None:
    """Số trong ảnh BGR `image` (vùng ô trắng của thanh nhập), hoặc None nếu trống / đọc lỗi."""
    if image.size == 0:
        return None
    digits = re.sub(r"\D", "", read_chars(split(image), FONT) or "")
    return int(digits) if digits else None
