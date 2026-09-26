"""
read_number.py — digits in a screen region as an int (port of the C#
Xulyanh.ImageToNumber).
"""
import re

import numpy as np

from ._digits import read

FONT = "Number"
_INT_MAX = 2**31 - 1    # C# int.TryParse limit


def run(image: np.ndarray) -> int:
    """Digits in `image` (BGR) as an int, thousands separators dropped;
    -1 if none could be read or the number is too big, like
    Xulyanh.ImageToNumber."""
    text = read(image, FONT)
    digits = re.sub(r"\D", "", text or "")
    if not digits or int(digits) > _INT_MAX:
        return -1
    return int(digits)
