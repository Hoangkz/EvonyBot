"""
read_tax_count.py — số lần trong ô số của popup Tax (Chợ -> Tax, Daily Activities / Resource Tax):
"11" -> 11. Mở popup ô số mặc định là số lượt Tax miễn phí còn lại.

Chữ trắng trên nền nâu, tách bằng Otsu như read_number; so với font riêng Images/OCR/TaxCount (font
Number đọc nhầm / không đọc được, VD "8"). Ảnh vào là vùng CROP (x, y, w, h) trên màn 396x704.
"""
import re

import numpy as np

from ._digits import read

FONT = "TaxCount"
CROP = (143, 287, 110, 28)   # ô số (198, 300) của popup Tax


def run(image: np.ndarray) -> int | None:
    """Số trong ảnh BGR ô số popup Tax (vùng CROP), hoặc None nếu đọc lỗi."""
    digits = re.sub(r"\D", "", read(image, FONT) or "")
    return int(digits) if digits else None
