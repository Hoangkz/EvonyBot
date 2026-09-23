"""
ocr — read text out of small screen regions with Tesseract (port of the
C# Xulyanh.RunOcr + Xulyanh.ImageToNumber). One module per reader, each
exposing `run(image)`:

- read_number: digits -> int
- read_coords: "X:Y" map coordinate -> (x, y)
"""
from .read_coords import run as read_coords
from .read_number import run as read_number

__all__ = ["read_coords", "read_number"]
