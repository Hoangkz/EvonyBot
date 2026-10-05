"""
read_balance.py — số dư vàng / kim cương ở màn Black Market (hàng dưới banner: icon vàng "2,199,030", icon kim cương
"105,947"; chữ trắng ngà trên nền tối) -> int.

Hàng này căn giữa nên số dài thì icon + chữ dịch sang trái (7 chữ số: icon vàng x 74..93; 10 chữ số "2,788,084,225"
máy 21913: x 60..79) -> không cắt vùng cố định: tìm mép phải icon theo màu (icon vàng: vàng đậm; icon kim cương:
xanh) trong ROW, cắt chữ ngay sau icon. Màn tối (hộp xác nhận che) không thấy icon -> None.

Font riêng Images/OCR/Balance (mẫu của font Number + mẫu cắt từ màn Black Market: font Number đọc nhầm 8 -> 3,
6 -> 5).
"""
import re

import cv2
import numpy as np

from ._digits import read

FONT = "Balance"
ROW = (217, 236)              # y của hàng số dư
GOLD_ICON_X = (40, 140)       # vùng tìm icon vàng
GEMS_ICON_X = (200, 320)      # vùng tìm icon kim cương
ICON_MIN_PIXELS = 3           # cột có >= chừng ấy điểm màu icon thì thuộc icon
TEXT_GAP = 3                  # chữ bắt đầu sau mép phải icon chừng ấy px
GOLD_TEXT_END_GAP = 10        # chữ vàng kết thúc trước icon kim cương chừng ấy px
GEMS_TEXT_WIDTH = 110         # đủ cho 10 chữ số + dấu phẩy


def run(image: np.ndarray) -> int | None:
    """Số trong ảnh BGR đã cắt sát vùng chữ (không có icon), dấu phẩy bỏ qua; None nếu đọc lỗi."""
    digits = re.sub(r"\D", "", read(image, FONT) or "")
    return int(digits) if digits else None


def read_gold(screen: np.ndarray) -> int | None:
    """Số vàng trên màn Black Market `screen` (BGR 396x704), None nếu không thấy icon / đọc lỗi."""
    gold = _icon_right(screen, GOLD_ICON_X, _yellow)
    if gold is None:
        return None
    gems = _icon_left(screen, GEMS_ICON_X, _blue)
    end = gems - GOLD_TEXT_END_GAP if gems is not None else GEMS_ICON_X[0]
    return run(screen[ROW[0]:ROW[1], gold + TEXT_GAP:end])


def read_gems(screen: np.ndarray) -> int | None:
    """Số kim cương trên màn Black Market `screen` (BGR 396x704), None nếu không thấy icon / đọc lỗi."""
    gems = _icon_right(screen, GEMS_ICON_X, _blue)
    if gems is None:
        return None
    start = gems + TEXT_GAP
    return run(screen[ROW[0]:ROW[1], start:min(screen.shape[1], start + GEMS_TEXT_WIDTH)])


def _yellow(hsv: np.ndarray) -> np.ndarray:
    return (hsv[..., 0] >= 10) & (hsv[..., 0] <= 35) & (hsv[..., 1] > 150) & (hsv[..., 2] > 120)


def _blue(hsv: np.ndarray) -> np.ndarray:
    return (hsv[..., 0] >= 90) & (hsv[..., 0] <= 130) & (hsv[..., 1] > 60) & (hsv[..., 2] > 120)


def _icon_columns(screen, span, color) -> np.ndarray:
    x0, x1 = span
    hsv = cv2.cvtColor(screen[ROW[0] - 2:ROW[1] + 2, x0:x1], cv2.COLOR_BGR2HSV)
    return np.where(color(hsv).sum(0) >= ICON_MIN_PIXELS)[0] + x0


def _icon_right(screen, span, color) -> int | None:
    cols = _icon_columns(screen, span, color)
    return int(cols.max()) if len(cols) else None


def _icon_left(screen, span, color) -> int | None:
    cols = _icon_columns(screen, span, color)
    return int(cols.min()) if len(cols) else None
