"""
_pieces.py — split a line of text picked out by colour into pieces and read
them against samples (shared by read_boss_name and read_power).

A piece is a run of columns with text pixels. It is kept "soft" (a 0-255
text-likeness image, anti-aliased edges included) so a glyph drawn half a
pixel off still looks like its sample. Samples live in Images/OCR/<font>/ as
"<label>_<n>.png"; a label may be several characters for glyphs the font
draws touching (e.g. "ot_1.png").
"""
import numpy as np

from ._digits import _normalize, _samples


def split(bw: np.ndarray, soft: np.ndarray, space_gap: int | None = None,
          dot_ratio: float | None = None) -> list:
    """Pieces of the text in mask `bw` left to right, each cut from `soft`
    to the rows/columns `bw` covers. A gap of `space_gap` px or more adds " ";
    a piece shorter than `dot_ratio` x the tallest one is "." (decimal point)."""
    soft = np.where(_grow(bw), soft, 0).astype(np.uint8)
    pieces, start, end = [], None, None
    for x, lit in enumerate(list(bw.any(axis=0)) + [False]):
        if lit and start is None:
            if space_gap is not None and end is not None and x - end >= space_gap:
                pieces.append(" ")
            start = x
        elif not lit and start is not None:
            rows = np.flatnonzero(bw[:, start:x].any(axis=1))
            pieces.append(soft[rows[0]:rows[-1] + 1, start:x])
            start, end = None, x
    if dot_ratio is not None:
        tallest = max((p.shape[0] for p in pieces if not isinstance(p, str)), default=0)
        pieces = ["." if not isinstance(p, str) and p.shape[0] < tallest * dot_ratio else p
                  for p in pieces]
    return pieces


def read(pieces: list, font: str, min_score: float) -> str | None:
    """Text of `pieces`: strings as they are, each image as the label of its
    best sample, or "?" if no sample scores `min_score`. None if no pieces."""
    if not pieces:
        return None
    labels, samples = _samples(font)
    text = ""
    for piece in pieces:
        if isinstance(piece, str):
            text += piece
            continue
        scores = samples @ _normalize(piece)
        best = int(scores.argmax())
        text += labels[best] if scores[best] >= min_score else "?"
    return text


def _grow(bw: np.ndarray) -> np.ndarray:
    """`bw` plus the pixel just above and below each lit pixel: keeps the
    faint anti-aliased edge of a glyph without pulling in background."""
    grown = bw > 0
    grown[1:] |= bw[:-1] > 0
    grown[:-1] |= bw[1:] > 0
    return grown
