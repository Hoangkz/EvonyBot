"""
read_power.py — a boss's power on a War rally card, e.g. "6.5M" -> 6_500_000.

White-grey text on the blue bar at the top of the card. Digits and the unit
("k" / "m" / "b") are matched against samples in Images/OCR/Power/ (same
naming as the other fonts, lower case); the decimal point is recognised by
its height and needs no sample.
"""
import re

import numpy as np

from . import _pieces

FONT = "Power"
MIN_SCORE = 0.75
DOT_RATIO = 0.4         # a piece shorter than this x the digits is "."
UNITS = {"": 1, "k": 1_000, "m": 1_000_000, "b": 1_000_000_000}
_NUMBER = re.compile(r"(\d+(?:\.\d+)?)([kmb]?)")


def mask(image: np.ndarray) -> np.ndarray:
    """Light grey text pixels of `image` (BGR) as a 0/255 mask."""
    return ((image.min(axis=2) > 140) * 255).astype(np.uint8)


def _lightness(image: np.ndarray) -> np.ndarray:
    """How light (and grey) each pixel is, 0-255 (soft)."""
    low = image.min(axis=2).astype(np.int16)
    return np.clip((low - 60) * 2, 0, 255).astype(np.uint8)


def split(image: np.ndarray) -> list:
    bw = mask(image)
    # Mảnh dính mép trái là phần biểu tượng kiếm bị cắt (vùng cắt phải rộng sang trái
    # cho số dài như "147.5M"), không phải chữ số: bỏ đi.
    if bw[:, 0].any():
        empty = np.flatnonzero(~bw.any(axis=0))
        bw[:, :empty[0] if len(empty) else bw.shape[1]] = 0
    return _pieces.split(bw, _lightness(image), dot_ratio=DOT_RATIO)


def text(image: np.ndarray) -> str | None:
    """The power as read, e.g. "6.5m" ("?" for unknown glyphs)."""
    return _pieces.read(split(image), FONT, MIN_SCORE)


def parse(value: str | None) -> int | None:
    """"6.5m" / "36.5K" / "2B" -> the number, or None if it isn't one."""
    found = _NUMBER.fullmatch((value or "").strip().lower())
    if not found:
        return None
    return round(float(found.group(1)) * UNITS[found.group(2)])


def run(image: np.ndarray) -> int | None:
    """The boss power in `image` (BGR), or None if it can't be read."""
    return parse(text(image))
