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
- read_progress: tiến độ nhiệm vụ event "300 / 500" -> 300 (số đã làm)
- read_bubble_time: thời gian bubble còn lại "06:55:22" -> số giây
- read_train_count: số lính tối đa một lần train (ô bên phải nút "+") -> 20812
"""
from .read_boss_name import run as read_boss_name
from .read_bubble_time import run as read_bubble_time
from .read_coords import run as read_coords
from .read_number import run as read_number
from .read_power import run as read_power
from .read_progress import run as read_progress
from .read_server import run as read_server
from .read_server_time import run as read_server_time
from .read_train_count import run as read_train_count

__all__ = ["read_boss_name", "read_bubble_time", "read_coords", "read_number", "read_power", "read_progress",
           "read_server", "read_server_time", "read_train_count"]
