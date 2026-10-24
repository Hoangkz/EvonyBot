"""
read_general_name.py — the General name under the portrait on the Recruit General screen
("Rustam", "Frederick the Great"), as lower-case text.

The name sits in a dark bar and its colour follows the quality (white, green, blue, purple, gold), so
text pixels are the bright ones INSIDE the bar: the biggest dark blob (V < BAR_MAX_VALUE) is the bar,
its outline filled and shrunk by BAR_MARGIN px (drops the metal border), bright pixels (V > TEXT_MIN_VALUE)
in it are text. Pieces split at empty columns, a gap of SPACE_GAP px or more is a space, each piece is
matched against samples in Images/OCR/GeneralName/ ("<text>_<n>.png", lower case, several letters for glyphs
drawn touching). A piece that matches no sample reads "?", so the caller can still fuzzy-match the text
(`similarity`) against the wanted names. Only letters count: punctuation, digits and accents are dropped. A dim screen (popup open) has no bar -> None.
"""
import re
import unicodedata
from difflib import SequenceMatcher

import cv2
import numpy as np

from . import _pieces

FONT = "GeneralName"
BAR_MAX_VALUE = 60      # V below this is the inside of the bar
TEXT_MIN_VALUE = 100    # V above this inside the bar is text
BAR_MARGIN = 3          # px: shrink the bar outline so its border is not read as text
SPACE_GAP = 4           # px of empty columns between two words
MIN_SCORE = 0.75        # below this a piece reads as "?"
SPAN_SLACK = 2          # similarity: the matched letters must lie within a stretch of the name at most len(text) + this long
MIN_MATCHED = 3         # similarity: fewer matched letters than this (or than the whole name if shorter) is no match
DOT_RATIO = 0.45        # a piece shorter than this x the tallest one is punctuation (. , ' -), dropped


def mask(image: np.ndarray) -> np.ndarray:
    """Text pixels of `image` (BGR, the name strip) as a 0/255 mask."""
    value = image.max(axis=2)
    count, labels, stats, _ = cv2.connectedComponentsWithStats((value < BAR_MAX_VALUE).astype(np.uint8), connectivity=4)
    if count < 2:
        return np.zeros(value.shape, np.uint8)
    bar = (labels == 1 + int(stats[1:, cv2.CC_STAT_AREA].argmax())).astype(np.uint8)
    outline, _ = cv2.findContours(bar, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    filled = np.zeros_like(bar)
    cv2.drawContours(filled, outline, -1, 1, -1)
    inner = cv2.erode(filled, np.ones((3, 3), np.uint8), iterations=BAR_MARGIN)
    return (((value > TEXT_MIN_VALUE) & (inner > 0)) * 255).astype(np.uint8)


def split(image: np.ndarray) -> list:
    """Pieces of the name left to right: " " for a word gap, else the piece's soft crop."""
    return _pieces.split(mask(image), image.max(axis=2), space_gap=SPACE_GAP, dot_ratio=DOT_RATIO)


def run(image: np.ndarray) -> str | None:
    """Text of the name in `image` (BGR), lower case, letters and spaces only ("?" for unknown pieces, punctuation dropped); None if
    there is no text."""
    text = _pieces.read(split(image), FONT, MIN_SCORE)
    return " ".join(text.replace(".", "").split()) or None if text else None


def similarity(text: str | None, name: str) -> float:
    """0..1 how much of the OCR `text` is found INSIDE `name` (the text may be only a part of the name, e.g. "?athanael" for "Nathanael Greene"):
    matched letters / letters of the text ("?" counts in the text but never matches). Only letters count (case, spaces, digits, punctuation, accents
    and the "(...)" part of the name ignored; i = l). Fewer than MIN_MATCHED matched letters (or the whole name when it is shorter) gives 0, so a
    two-letter read does not match everything. The tiny ratio term only breaks ties towards the name that fits the whole text best."""
    if not text:
        return 0.0
    a, b = _letters(text, keep="?"), _letters(re.sub(r"\([^)]*\)", "", name))
    if not a or not b:
        return 0.0
    matcher = SequenceMatcher(None, a, b, autojunk=False)
    blocks = [block for block in matcher.get_matching_blocks() if block.size]
    matched = sum(block.size for block in blocks)
    if matched < min(MIN_MATCHED, len(b)):
        return 0.0
    if blocks[-1].b + blocks[-1].size - blocks[0].b > len(a) + SPAN_SLACK:   # chữ khớp rải khắp tên dài: không phải một đoạn của tên
        return 0.0
    return matched / len(a) + matcher.ratio() / 1000


def _letters(text: str, keep: str = "") -> str:
    """Only the letters a-z of `text` (lower case, accents removed) plus the characters in `keep`: spaces, digits and punctuation dropped."""
    plain = unicodedata.normalize("NFD", text.lower()).replace("i", "l")   # i / l / I are one vertical stroke in this font: read as either
    return "".join(c for c in plain if "a" <= c <= "z" or c in keep)
