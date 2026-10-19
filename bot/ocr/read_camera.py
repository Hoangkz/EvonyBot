"""
read_camera.py — toạ độ "X:0628 Y:0128" ở thanh dưới màn hình bản đồ thế giới (điểm giữa màn hình camera đang nhìn).
"""
import cv2
import numpy as np

from ._digits import read

FONT = "Camera"
X_REGION = (169, 614, 36, 18)    # (x, y, w, h) trên màn 396 x 704: bốn chữ số của X, sau "X:"
Y_REGION = (224, 614, 36, 18)    # bốn chữ số của Y, sau "Y:"
DIGITS = 4
BRIGHT = 180                     # chữ trắng ngà sáng hơn mọi nền bản đồ: lấy điểm sáng >= ngưỡng này (Otsu trên nền loang bị nhiễu)


def _value(screen: np.ndarray, region) -> int | None:
    return _parse(read(_bright(screen, region), FONT, colon=False))


def _bright(screen: np.ndarray, region) -> np.ndarray:
    x, y, w, h = region
    gray = cv2.cvtColor(screen[y:y + h, x:x + w], cv2.COLOR_BGR2GRAY)
    return np.where(gray >= BRIGHT, 255, 0).astype(np.uint8)


def _parse(text) -> int | None:
    return int(text) if text is not None and len(text) == DIGITS and text.isdigit() else None


def run(screen: np.ndarray) -> tuple[int, int] | None:
    """(X, Y) camera trên ảnh màn hình đầy đủ `screen` (BGR), hoặc None nếu không đọc được."""
    x, y = _value(screen, X_REGION), _value(screen, Y_REGION)
    return None if x is None or y is None else (x, y)
