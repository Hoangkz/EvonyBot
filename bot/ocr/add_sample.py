"""
add_sample.py — cut a screenshot of a number into per-digit OCR samples.

    python -m bot.ocr.add_sample <font> <image> <text>

<text> spells every piece of the image left to right: digits, "," and ":"
as they appear, and "_" for a piece to skip (e.g. the location pin before
a coordinate). Example:

    python -m bot.ocr.add_sample Coords shot.png _0951:0663

The boss name font ("Name", read_boss_name.py) is split by colour and a
piece can be several touching letters, so its <text> lists the pieces
separated by "|": " " for a word gap, "_" to skip, anything else is saved
lower-cased. Example for "(Boss) Peryton" where "ryt" touch:

    python -m bot.ocr.add_sample Name name.png "(|b|o|s|s|)| |p|e|ryt|o|n"

The boss power font ("Power", read_power.py) works the same way; "." is
the decimal point (recognised by height, not saved). Example for "6.5M":

    python -m bot.ocr.add_sample Power power.png "6|.|5|m"

The event quest progress font ("Progress", read_progress.py) is split the
same way; "/" and "," are recognised by shape (not saved). Example:

    python -m bot.ocr.add_sample Progress progress.png "6|0|0|/|1|,|0|0|0"
"""
import sys
from pathlib import Path

import cv2
import numpy as np

from ._digits import OCR_DIR, split
from .read_boss_name import FONT as NAME_FONT
from .read_boss_name import split as split_name
from .read_power import FONT as POWER_FONT
from .read_power import split as split_power
from .read_progress import FONT as PROGRESS_FONT
from .read_progress import split as split_progress

# Fonts split into pieces by their own splitter (see _pieces.py / read_progress.py).
PIECE_FONTS = {NAME_FONT: split_name, POWER_FONT: split_power, PROGRESS_FONT: split_progress}


def add_sample(font: str, image_path: str, text: str) -> list[Path]:
    """Save each digit of the image as Images/OCR/<font>/<digit>_<n>.png."""
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(image_path)
    if font in PIECE_FONTS:
        return add_piece_sample(font, image, text.split("|"))
    chars = split(image)
    if len(chars) != len(text):
        raise ValueError(f"image splits into {len(chars)} pieces, text has {len(text)}")

    saved = []
    for expected, char in zip(text, chars):
        if expected == "_":
            continue
        if isinstance(char, str) or not expected.isdigit():
            got = char if isinstance(char, str) else "a digit"
            if got != expected:
                raise ValueError(f"expected {expected!r}, image has {got!r}")
            continue
        saved.append(_save(font, expected, char))
    return saved


def add_piece_sample(font: str, image: np.ndarray, tokens: list[str]) -> list[Path]:
    """Save each piece of the text as Images/OCR/<font>/<token>_<n>.png."""
    pieces = PIECE_FONTS[font](image)
    if len(pieces) != len(tokens):
        raise ValueError(f"image splits into {len(pieces)} pieces "
                         f"({''.join(p if isinstance(p, str) else '#' for p in pieces)!r}), "
                         f"text has {len(tokens)}")
    saved = []
    for token, piece in zip(tokens, pieces):
        if isinstance(piece, str) or token in (" ", "."):
            if token != piece and token != "_":
                got = repr(piece) if isinstance(piece, str) else "a glyph"
                raise ValueError(f"expected {token!r}, image has {got}")
            continue
        if token != "_":
            saved.append(_save(font, token.lower(), piece))
    return saved


def _save(font: str, label: str, piece) -> Path:
    folder = OCR_DIR / font
    folder.mkdir(parents=True, exist_ok=True)
    n = 1
    while (folder / f"{label}_{n}.png").exists():
        n += 1
    path = folder / f"{label}_{n}.png"
    cv2.imwrite(str(path), np.asarray(piece))
    return path


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    for p in add_sample(*sys.argv[1:]):
        print(p)
