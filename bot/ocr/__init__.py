"""
ocr — read numbers out of small screen regions by matching each digit
against samples of the game's font in Images/OCR/ (port of the C#
Xulyanh.RunOcr + Xulyanh.ImageToNumber, which used Tesseract). One module
per reader, each exposing `run(image)`:

- read_number: digits -> int
- read_coords: "X:Y" map coordinate -> (x, y)
- read_server: "S. 1257" (sau "Empire Name:") -> "1257"
- read_boss_name: "(Boss) Peryton" trên thẻ rally -> "(boss) peryton"
- read_power: lực boss "6.5M" trên thẻ rally -> 6500000
"""
from .read_boss_name import run as read_boss_name
from .read_coords import run as read_coords
from .read_number import run as read_number
from .read_power import run as read_power
from .read_server import run as read_server
from .read_server_time import run as read_server_time

__all__ = ["read_boss_name", "read_coords", "read_number", "read_power", "read_server", "read_server_time"]
