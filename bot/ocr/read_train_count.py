"""
read_train_count.py — số lính tối đa một lần train, trong ô bên phải nút "+" ở màn Train
(VD "20812"; chữ trắng ngà trên nền tối, font riêng Images/OCR/TrainCount).
"""
import re

import numpy as np

from ._digits import read

FONT = "TrainCount"


def run(image: np.ndarray) -> int | None:
    """Số trong ảnh BGR `image`, hoặc None nếu đọc lỗi."""
    digits = re.sub(r"\D", "", read(image, FONT) or "")
    return int(digits) if digits else None
