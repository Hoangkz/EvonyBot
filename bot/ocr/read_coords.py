"""
read_coords.py — a "X:Y" map coordinate in a screen region (port of the
C# boss-coordinate OCR in Boss).
"""
import re

import cv2
import numpy as np

from ._tesseract import pytesseract


def run(image: np.ndarray) -> tuple[int, int] | None:
    """A "X:Y" map coordinate in `image` (BGR), or None if it can't be read.
    Scaled up 3x and turned black & white (threshold 150) first, like the
    C# PreProcessImage."""
    tess = pytesseract()
    if image.size == 0:
        return None
    big = cv2.resize(image, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(big, cv2.COLOR_BGR2GRAY)
    _, bw = cv2.threshold(gray, 149, 255, cv2.THRESH_BINARY)
    text = tess.image_to_string(bw, config="--psm 7")
    parts = re.sub(r"[^0-9:]", "", text).split(":")
    try:
        return int(parts[0]), int(parts[1])
    except (IndexError, ValueError):
        return None
