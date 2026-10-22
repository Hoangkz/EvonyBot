"""
read_event_countdown.py — "Event Quest Countdown: 3d 14:22" ở màn King's Path / Gather Troops (chữ xanh lá sau hình đồng hồ cát)
-> số giây còn lại. Cách đọc như read_bubble_time nhưng mẫu riêng Images/OCR/EventCountdown: từ 1 ngày trở lên hiện "3d 14:22"
(ngày, giờ:phút), dưới 1 ngày "06:55:22". Tách chữ theo màu xanh lá (G sáng, R thấp), không phải màu kem.
"""
import cv2
import numpy as np

from ._digits import split as split_digits
from ._digits import MIN_SCORE, _normalize, _samples
from .read_bubble_time import _CLOCK, _DAYS

FONT = "EventCountdown"   # mẫu Images/OCR/EventCountdown (chữ xanh lá; mẫu Timer là chữ màu kem, không khớp)

# Hình đồng hồ cát đứng trước chữ đếm ngược (cả King's Path lẫn Gather Troops): tìm nó rồi cắt vùng chữ ngay bên phải, nên
# không phụ thuộc vị trí cố định. Đo trên 396x704: đồng hồ cát tâm (248, 173), chữ x 259..313, y 167..178.
HOURGLASS = "Event/countdownHourglass.png"
HOURGLASS_REGION = (0, 20, 100, 30)   # % màn hình
# Vùng chữ so với tâm đồng hồ cát: (dx, dy, rộng, cao) — cao 13 px (đúng dải chữ số).
TEXT_FROM_HOURGLASS = (11, -6, 62, 13)


def mask(image: np.ndarray) -> np.ndarray:
    """Ảnh BGR -> ảnh đen trắng chỉ còn chữ xanh lá (255)."""
    b, g, r = (image[..., i].astype(int) for i in range(3))
    return ((g > 110) & (g - r > 50) & (g - b > 50)).astype(np.uint8) * 255


def split(image: np.ndarray) -> list:
    """Ảnh BGR -> mảnh trái -> phải (ảnh chữ hoặc ":"), dùng cho add_sample."""
    return split_digits(mask(image)) if image.size else []


def _char(piece: np.ndarray) -> str | None:
    """Chữ số hoặc "d" của mảnh, None nếu không giống mẫu nào."""
    labels, samples = _samples(FONT)
    scores = samples @ _normalize(piece)
    best = int(scores.argmax())
    return labels[best] if scores[best] >= MIN_SCORE else None


def read(bot, screen) -> int | None:
    """Số giây còn lại của event trên `screen` (màn event King's Path / Gather Troops): tìm đồng hồ cát, cắt chữ bên phải
    rồi OCR. None nếu không thấy đồng hồ cát hoặc không đọc được."""
    icon = bot.find(HOURGLASS, screen=screen, region=HOURGLASS_REGION)
    if icon is None:
        return None
    dx, dy, w, h = TEXT_FROM_HOURGLASS
    return run(bot.crop(screen, icon[0] + dx, icon[1] + dy, w, h))


def run(image: np.ndarray) -> int | None:
    """Số giây còn lại của event, hoặc None nếu không đọc được."""
    text = ""
    for piece in split(image):
        if isinstance(piece, str):
            text += piece
            continue
        char = _char(piece)
        if char is None:
            return None
        text += char
    match = _DAYS.fullmatch(text)
    if match is not None:
        days, hours, minutes = map(int, match.groups())
        return None if hours >= 24 or minutes >= 60 else days * 86400 + hours * 3600 + minutes * 60
    match = _CLOCK.fullmatch(text)
    if match is None:
        return None
    hours, minutes, seconds = map(int, match.groups())
    return None if minutes >= 60 or seconds >= 60 else hours * 3600 + minutes * 60 + seconds


# Màn event 3 ngày (Event Center > Limited): "Ends in 2d 21:27" (hoặc "Ends in 17:10:11" dưới 1 ngày) ngay trên banner, chữ xanh lá,
# không có đồng hồ cát nên neo bằng chữ "Ends in": cắt vùng ngay bên phải chữ đó.
ENDS_IN = "EventCenter/ThreeDay/endsIn.png"
ENDS_IN_REGION = (20, 27, 60, 36)     # % màn hình
ENDS_IN_THRESHOLD = 0.8               # 1,00 trên màn của nó (máy 21943 0,90); màn khác <= 0,48
# Vùng chữ so với mép phải của chữ "Ends in": (dx, dy, rộng, cao) — cao 16 px bao dải chữ số (cao 10 px), rộng 72 px chưa chạm
# hình quả bên phải banner.
TEXT_FROM_ENDS_IN = (3, 0, 72, 16)


def read_ends_in(bot, screen) -> int | None:
    """Số giây còn lại của event 3 ngày trên `screen` (màn event, tab nhiệm vụ hoặc Redeem): tìm chữ "Ends in", cắt chữ bên phải rồi
    OCR. None nếu không thấy chữ hoặc không đọc được."""
    from ..context.templates import read_image, TEMPLATE_DIR   # import trong hàm: tránh vòng import khi nạp bot.ocr
    pos = bot.find(ENDS_IN, threshold=ENDS_IN_THRESHOLD, screen=screen, region=ENDS_IN_REGION)
    template = read_image(TEMPLATE_DIR / ENDS_IN)
    if pos is None or template is None:
        return None
    dx, dy, w, h = TEXT_FROM_ENDS_IN
    height, width = template.shape[:2]
    return run(bot.crop(screen, pos[0] + width // 2 + dx, pos[1] - h // 2 + dy, w, h))
