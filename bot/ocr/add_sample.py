"""
add_sample.py — cut a screenshot of a number into per-digit OCR samples.

    python -m bot.ocr.add_sample <font> <image> <text>

<text> spells every piece of the image left to right: digits, "," and ":"
as they appear, and "_" for a piece to skip (e.g. the location pin before
a coordinate). Example:

    python -m bot.ocr.add_sample Coords shot.png _0951:0663
"""
import sys
from pathlib import Path

import cv2
import numpy as np

from ._digits import OCR_DIR, split


def add_sample(font: str, image_path: str, text: str) -> list[Path]:
    """Save each digit of the image as Images/OCR/<font>/<digit>_<n>.png."""
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(image_path)
    chars = split(image)
    if len(chars) != len(text):
        raise ValueError(f"image splits into {len(chars)} pieces, text has {len(text)}")

    folder = OCR_DIR / font
    folder.mkdir(parents=True, exist_ok=True)
    saved = []
    for expected, char in zip(text, chars):
        if expected == "_":
            continue
        if isinstance(char, str) or not expected.isdigit():
            got = char if isinstance(char, str) else "a digit"
            if got != expected:
                raise ValueError(f"expected {expected!r}, image has {got!r}")
            continue
        n = 1
        while (folder / f"{expected}_{n}.png").exists():
            n += 1
        path = folder / f"{expected}_{n}.png"
        cv2.imwrite(str(path), np.asarray(char))
        saved.append(path)
    return saved


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    for p in add_sample(*sys.argv[1:]):
        print(p)
