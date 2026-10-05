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
- read_milestone: tiến độ rương mốc "Progress:12 / 70" (Gather Troops) -> 12
- read_bubble_time: thời gian bubble còn lại "06:55:22" -> số giây
- read_train_count: số lính tối đa một lần train (ô bên phải nút "+") -> 20812
- read_heal_count: số lính bị thương của một dòng ở màn Hospital "0 / 8,147" -> 8147
- read_offer_cost: số kim cương ô "Cost" của popup Offer Gems "126,175" -> 126175
- read_market_balance: số dư vàng / kim cương trên màn Black Market
- read_tax_count: ô số lần của popup Tax (Chợ) "11" -> 11
"""
from .read_boss_name import run as read_boss_name
from .read_bubble_time import run as read_bubble_time
from .read_coords import run as read_coords
from .read_heal_count import run as read_heal_count
from .read_milestone import run as read_milestone
from .read_market_balance import MarketBalance, run as read_market_balance
from .read_number import run as read_number
from .read_offer_cost import run as read_offer_cost
from .read_power import run as read_power
from .read_progress import run as read_progress
from .read_server import run as read_server
from .read_tax_count import run as read_tax_count
from .read_train_count import run as read_train_count

__all__ = ["MarketBalance", "read_boss_name", "read_bubble_time", "read_coords", "read_heal_count", "read_market_balance", "read_milestone", "read_number", "read_offer_cost", "read_power", "read_progress",
           "read_server", "read_tax_count", "read_train_count"]
