"""
ocr.py — read a number out of a small screen region (port of the C#
Xulyanh.RunOcr + Xulyanh.ImageToNumber). The C# app ran a bundled
data/Tesseract/main.exe; here Tesseract is called via pytesseract.

tesseract.exe is looked up in this order: the TESSERACT_CMD environment
variable, a Tesseract-OCR folder next to the app, the default install
folder, then PATH.
"""
import os
import re
import shutil
import sys
from pathlib import Path

import cv2
import numpy as np

_APP_DIR = (Path(sys.executable).resolve().parent if getattr(sys, "frozen", False)
            else Path(__file__).resolve().parent.parent)
_CANDIDATES = [
    _APP_DIR / "Tesseract-OCR" / "tesseract.exe",
    Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
    Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
]

_tesseract_cmd: str | None = None
_INT_MAX = 2**31 - 1    # C# int.TryParse limit


def _find_tesseract() -> str:
    global _tesseract_cmd
    if _tesseract_cmd is None:
        env = os.environ.get("TESSERACT_CMD")
        found = next((str(p) for p in _CANDIDATES if p.exists()), None)
        _tesseract_cmd = env or found or shutil.which("tesseract")
        if not _tesseract_cmd:
            raise RuntimeError("Tesseract OCR not found (install it or set TESSERACT_CMD)")
    return _tesseract_cmd


def read_number(image: np.ndarray) -> int:
    """Digits in `image` (BGR) as an int; -1 if none could be read or the
    number is too big, like Xulyanh.ImageToNumber."""
    import pytesseract

    pytesseract.pytesseract.tesseract_cmd = _find_tesseract()
    if image.size == 0:
        return -1
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Small game fonts read much better scaled up.
    gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    text = pytesseract.image_to_string(
        gray, config="--psm 7 -c tessedit_char_whitelist=0123456789,."
    )
    digits = re.sub(r"\D", "", text)
    if not digits or int(digits) > _INT_MAX:
        return -1
    return int(digits)
