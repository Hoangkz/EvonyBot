"""Read the gold and gem wallets shown inside the Black Market.

Do not OCR fixed absolute rectangles blindly: the top resource bar uses the
same number font and small UI shifts can move the market wallet a few pixels.
Instead, locate each currency icon inside the Black Market wallet band and
crop its number relative to that icon.  The number itself still uses the
project's sampled ``Number`` OCR (not Tesseract).
"""
from dataclasses import dataclass

import cv2
import numpy as np

from ..context import TEMPLATE_DIR
from .read_number import run as read_number


# Evony's automation viewport is 396 x 704.  Restrict matching to the wallet
# row below the Black Market banner so item prices and the top resource bar
# cannot be mistaken for the player's balance.
WALLET_REGION = (40, 195, 320, 55)  # x, y, w, h
ICON_THRESHOLD = 0.85

# (template, number dx/dy from template top-left, number width/height).
# goldCheck matches the full coin icon.  gems.png is a stable 10x9 fragment of
# the diamond, hence its different vertical offset.
GOLD_FIELD = ("Black Market/goldCheck.png", 24, -3, 130, 24)
GEMS_FIELD = ("Black Market/gems.png", 15, -14, 120, 24)


@dataclass(frozen=True)
class MarketBalance:
    gold: int | None
    gems: int | None


def _icon_position(image: np.ndarray, template_path: str) -> tuple[int, int] | None:
    """Top-left of a wallet icon, or ``None`` when this is not a market wallet."""
    if image is None or image.size == 0:
        return None
    x, y, w, h = WALLET_REGION
    region = image[y:y + h, x:x + w]
    template = cv2.imread(str(TEMPLATE_DIR / template_path))
    if template is None or region.shape[0] < template.shape[0] or region.shape[1] < template.shape[1]:
        return None
    result = cv2.matchTemplate(region, template, cv2.TM_CCOEFF_NORMED)
    _, score, _, point = cv2.minMaxLoc(result)
    if score < ICON_THRESHOLD:
        return None
    return x + point[0], y + point[1]


def _read(image: np.ndarray, field: tuple[str, int, int, int, int]) -> int | None:
    template, dx, dy, w, h = field
    position = _icon_position(image, template)
    if position is None:
        return None
    x, y = position[0] + dx, position[1] + dy
    if x < 0 or y < 0 or x + w > image.shape[1] or y + h > image.shape[0]:
        return None
    value = read_number(image[y:y + h, x:x + w])
    return value if value >= 0 else None


def run(image: np.ndarray) -> MarketBalance:
    """Return the Black Market wallet values; unreadable fields are ``None``."""
    return MarketBalance(_read(image, GOLD_FIELD), _read(image, GEMS_FIELD))
