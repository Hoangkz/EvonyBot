"""
ocr — read numbers out of small screen regions by matching each digit
against samples of the game's font in Images/OCR/ (port of the C#
Xulyanh.RunOcr + Xulyanh.ImageToNumber, which used Tesseract). One module
per reader, each exposing `run(image)`:

- read_number: digits -> int
- read_coords: "X:Y" map coordinate -> (x, y)
- read_server: "S. 1257" (sau "Empire Name:") -> "1257"
"""
from .read_coords import run as read_coords
from .read_number import run as read_number
from .read_server import run as read_server

__all__ = ["read_coords", "read_number", "read_server"]
