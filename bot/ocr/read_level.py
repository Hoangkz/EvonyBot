"""
read_level.py — số cấp mỏ ở bảng Search của bản đồ thế giới (ô bên phải nút "+", Gather Resources) -> int.

Font riêng Images/OCR/GatherLevel: font chung "Number" đọc nhầm 3 và 6 thành 8 ở ô này (13 -> 18, 16 -> 18).
"""
import re

import numpy as np

from ._digits import read

FONT = "GatherLevel"


def run(image: np.ndarray) -> int | None:
    """Số cấp, hoặc None nếu không đọc được."""
    digits = re.sub(r"\D", "", read(image, FONT) or "")
    return int(digits) if digits else None
