"""
read_number.py — digits in a screen region as an int (port of the C#
Xulyanh.ImageToNumber).
"""
import re

import cv2
import numpy as np

from ._tesseract import pytesseract

_INT_MAX = 2**31 - 1    # C# int.TryParse limit


def run(image: np.ndarray) -> int:
    """Digits in `image` (BGR) as an int; -1 if none could be read or the
    number is too big, like Xulyanh.ImageToNumber."""
    tess = pytesseract()
    if image.size == 0:
        return -1
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Small game fonts read much better scaled up.
    gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    text = tess.image_to_string(
        gray, config="--psm 7 -c tessedit_char_whitelist=0123456789,."
    )
    digits = re.sub(r"\D", "", text)
    if not digits or int(digits) > _INT_MAX:
        return -1
    return int(digits)
