"""
read_boss_name.py — the boss name label of a War rally card, e.g.
"(Boss) Peryton" or "(Boss) Junior Hydra", as lower-case text.

The label is yellow text on a dark bar: pixels are kept by colour (not Otsu,
the card behind is busy), split at empty columns, and a gap of SPACE_GAP px
or more is a space. Each piece is matched against samples in
Images/OCR/Name/, named "<text>_<n>.png" in lower case; <text> may be more
than one letter for letters the font draws touching (e.g. "ot_1.png").
A piece that matches no sample well enough reads as "?", so the caller can
still fuzzy-match the text against the known boss names.
"""
import numpy as np

from . import _pieces

FONT = "Name"
SPACE_GAP = 4           # px of empty columns between two words
MIN_LINE_HEIGHT = 5     # rows: a shorter run of text pixels is a speck, not a line
LINE_PITCH = 15         # rows from one line's top to the next ("Legendary Bayar" / "Knight")
MAX_LINE_HEIGHT = 20    # rows: a taller run is two lines touching (descender of g/y on K/h)
MIN_SCORE = 0.75        # below this a piece reads as "?"


def mask(image: np.ndarray) -> np.ndarray:
    """Yellow text pixels of `image` (BGR) as a 0/255 mask."""
    b, g, r = (image[..., i].astype(np.int16) for i in range(3))
    return (((r > 110) & (g > 90) & (r - b > 50)) * 255).astype(np.uint8)


def _yellowness(image: np.ndarray) -> np.ndarray:
    """How yellow each pixel is, 0-255 (soft, anti-aliased edges kept)."""
    b, r = image[..., 0].astype(np.int16), image[..., 2].astype(np.int16)
    return np.clip((r - b - 20) * 2, 0, 255).astype(np.uint8)


def split(image: np.ndarray) -> list:
    """Pieces of the label left to right: " " for a word gap, else the
    piece's soft crop."""
    return _pieces.split(mask(image), _yellowness(image), space_gap=SPACE_GAP)


def lines(image: np.ndarray) -> list[np.ndarray]:
    """The label's text lines, top to bottom: a long name wraps onto two lines
    ("(Boss) Skeleton" / "Dragon"). Lines are split at empty rows; runs shorter
    than MIN_LINE_HEIGHT rows are specks, not text. A run taller than
    MAX_LINE_HEIGHT is two lines with no empty row between them (a descender
    touches the line below), cut LINE_PITCH rows below its top."""
    lit = list(mask(image).any(axis=1)) + [False]
    result, start = [], None
    for y, on in enumerate(lit):
        if on and start is None:
            start = y
        elif not on and start is not None:
            if y - start > MAX_LINE_HEIGHT:
                result.append(image[max(start - 1, 0):start + LINE_PITCH])
                result.append(image[start + LINE_PITCH:y + 1])
            elif y - start >= MIN_LINE_HEIGHT:
                result.append(image[max(start - 1, 0):y + 1])
            start = None
    return result


def run(image: np.ndarray) -> str | None:
    """Text of the name label in `image` (BGR), lower case, with "?" for
    unknown pieces; lines of a wrapped name are joined with a space. None if
    there is no text at all."""
    texts = [_pieces.read(split(line), FONT, MIN_SCORE) for line in lines(image)]
    return " ".join(t for t in texts if t) or None
