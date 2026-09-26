"""
read_coords.py — a "X:Y" map coordinate in a screen region (port of the
C# boss-coordinate OCR in Boss).
"""
import numpy as np

from ._digits import read

FONT = "Coords"


def run(image: np.ndarray) -> tuple[int, int] | None:
    """A "X:Y" map coordinate in `image` (BGR), or None if it can't be read.
    `image` should start after the location pin."""
    text = read(image, FONT)
    if text is None:
        return None
    parts = text.replace(",", "").split(":")
    if len(parts) != 2 or not all(parts):
        return None
    return int(parts[0]), int(parts[1])
