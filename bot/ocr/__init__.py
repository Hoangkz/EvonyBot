"""
ocr — read numbers out of small screen regions by matching each digit
against samples of the game's font in Images/OCR/ (port of the C#
Xulyanh.RunOcr + Xulyanh.ImageToNumber, which used Tesseract). One module
per reader, each exposing `run(image)`:

- read_number: digits -> int
- read_camera: thanh toạ độ "X:0628 Y:0128" của bản đồ thế giới (ảnh cả màn hình) -> (628, 128)
- read_coords: "X:Y" map coordinate -> (x, y)
- read_server: "S. 1257" (sau "Empire Name:") -> "1257"
- read_boss_count: số boss chờ ở huy hiệu đỏ của icon listboss (màn thành) -> 3
- read_boss_name: "(Boss) Peryton" trên thẻ rally -> "(boss) peryton"
- read_general_name: tên tướng dưới ảnh tướng ở màn Recruit General -> "rustam" ("?" = glyph chưa có mẫu); similarity() so khớp mờ với tên cần mua
- read_power: lực boss "6.5M" trên thẻ rally -> 6500000
- read_progress: tiến độ nhiệm vụ event "300 / 500" -> 300 (số đã làm)
- read_milestone: tiến độ rương mốc "Progress:12 / 70" (Gather Troops) -> 12
- read_bubble_time: thời gian bubble còn lại "06:55:22" -> số giây
- read_march_time: giờ ở màn March (thu thập / đi) "00:48:57" -> số giây
- read_train_count: số lính tối đa một lần train (ô bên phải nút "+") -> 20812
- read_heal_count: số lính bị thương của một dòng ở màn Hospital "0 / 8,147" -> 8147
- read_offer_cost: số kim cương ô "Cost" của popup Offer Gems "126,175" -> 126175
- read_tax_count: ô số lần của popup Tax (Chợ) "11" -> 11
- read_balance: số dư vàng / kim cương ở màn Black Market "2,199,030" -> 2199030 (read_gold / read_gems cắt theo icon)
"""
from .read_balance import run as read_balance
from .read_boss_count import run as read_boss_count
from .read_boss_name import run as read_boss_name
from .read_bubble_time import run as read_bubble_time
from .read_camera import run as read_camera
from .read_coords import run as read_coords
from .read_general_name import run as read_general_name
from .read_heal_count import run as read_heal_count
from .read_march_time import run as read_march_time
from .read_milestone import run as read_milestone
from .read_number import run as read_number
from .read_offer_cost import run as read_offer_cost
from .read_power import run as read_power
from .read_progress import run as read_progress
from .read_server import run as read_server
from .read_tax_count import run as read_tax_count
from .read_train_count import run as read_train_count

__all__ = ["read_balance", "read_boss_count", "read_boss_name", "read_bubble_time", "read_camera", "read_coords", "read_general_name", "read_heal_count", "read_march_time", "read_milestone", "read_number", "read_offer_cost", "read_power", "read_progress",
           "read_server", "read_tax_count", "read_train_count"]
