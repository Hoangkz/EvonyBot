"""
read_boss_count.py — số boss đang chờ tham gia: số trắng trong huy hiệu đỏ ở góc trên phải icon listboss (nút danh sách boss ở
màn thành, Images/JoinBoss/listboss.png) -> 3. Không có huy hiệu (không icon) = 0, do người gọi quyết định.

Chữ sáng trên nền đỏ sẫm: lấy kênh sáng nhất-nhỏ (min của B, G, R) rồi ngưỡng, so với font riêng Images/OCR/BossCount. Ảnh vào là
vùng CROP so với góc trên-trái ảnh listboss (OFFSET + SIZE) trên màn 396x704.
"""
import re

import numpy as np

from ._digits import read

FONT = "BossCount"
OFFSET = (25, -15)   # (dx, dy) từ góc trên-trái ảnh listboss tới góc trên-trái vùng số
SIZE = (18, 14)      # (w, h) vùng số: vừa huy hiệu, đủ cho hai chữ số (chữ nhỏ lại khi có hai chữ số)
LIGHT = 110          # kênh min lớn hơn mức này = nét chữ (nền đỏ ~0-60, nhiễu ngoài huy hiệu tới ~140 nhưng ở ngoài vùng)


def mask(image: np.ndarray) -> np.ndarray:
    """Nét chữ sáng của `image` (BGR) thành ảnh 0/255."""
    return ((image.min(axis=2) > LIGHT) * 255).astype(np.uint8)


def run(image: np.ndarray) -> int | None:
    """Số trong ảnh BGR vùng số của huy hiệu, hoặc None nếu không đọc được."""
    digits = re.sub(r"\D", "", read(mask(image), FONT) or "")
    return int(digits) if digits else None


def crop(screen: np.ndarray, icon: tuple[int, int]) -> np.ndarray:
    """Vùng số của `screen` khi ảnh listboss có góc trên-trái ở `icon` (x, y)."""
    x, y = icon[0] + OFFSET[0], icon[1] + OFFSET[1]
    return screen[max(0, y):y + SIZE[1], x:x + SIZE[0]]
