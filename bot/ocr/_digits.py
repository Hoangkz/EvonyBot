"""
_digits.py — read a line of digits by matching each character against
samples of the game's font (replaces Tesseract).

Samples live in Images/OCR/<font>/, one black & white PNG per sample named
"<digit>_<n>.png" and cropped to the character. Several samples per digit
make reads more reliable; add them with add_sample.py.
"""
import cv2
import numpy as np

from ..context.templates import TEMPLATE_DIR

OCR_DIR = TEMPLATE_DIR / "OCR"
MIN_SCORE = 0.6          # below this a character is treated as unreadable
_SIZE = (12, 20)         # (w, h) characters are scaled to before comparing

_fonts: dict[str, tuple[list[str], np.ndarray]] = {}


def split(image: np.ndarray) -> list:
    """Characters of `image` (BGR or gray) left to right: "," for a short
    mark (comma / dot), ":" for a colon, else the character's black & white
    crop. Split at native size — scaled up, digits 1px apart run together."""
    if image.size == 0:
        return []
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    crops, start = [], None
    for x, lit in enumerate(list(bw.any(axis=0)) + [False]):
        if lit and start is None:
            start = x
        elif not lit and start is not None:
            column = bw[:, start:x]
            rows = np.flatnonzero(column.any(axis=1))
            crops.append(column[rows[0]:rows[-1] + 1])
            start = None
    if not crops:
        return []

    height = max(c.shape[0] for c in crops)
    chars = []
    for c in crops:
        h, w = c.shape
        if h < height * 0.5:
            chars.append(",")
        elif w <= h * 0.5 and not c.any(axis=1).all():   # two dots stacked
            chars.append(":")
        else:
            chars.append(c)
    return chars


def _normalize(char: np.ndarray) -> np.ndarray:
    """`char` scaled to _SIZE, flattened, zero-mean and unit-length, so a
    dot product of two is their correlation (TM_CCOEFF_NORMED)."""
    v = cv2.resize(char, _SIZE, interpolation=cv2.INTER_AREA).astype(np.float32).ravel()
    v -= v.mean()
    norm = np.linalg.norm(v)
    return v / norm if norm else v


def _samples(font: str) -> tuple[list[str], np.ndarray]:
    """(digits, normalized sample rows) for `font`, loaded once."""
    if font not in _fonts:
        digits, rows = [], []
        for path in sorted((OCR_DIR / font).glob("*.png")):
            image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
            if image is not None:
                digits.append(path.stem.split("_")[0])
                rows.append(_normalize(image))
        if not rows:
            raise FileNotFoundError(f"No OCR samples in {OCR_DIR / font}")
        _fonts[font] = digits, np.stack(rows)
    return _fonts[font]


def read(image: np.ndarray, font: str) -> str | None:
    """Digits, "," and ":" in `image`, or None if there are no digits or
    one doesn't match any sample of `font` well enough."""
    digits, samples = _samples(font)
    text = ""
    for char in split(image):
        if isinstance(char, str):
            text += char
            continue
        scores = samples @ _normalize(char)
        best = int(scores.argmax())
        if scores[best] < MIN_SCORE:
            return None
        text += digits[best]
    return text if any(ch.isdigit() for ch in text) else None
