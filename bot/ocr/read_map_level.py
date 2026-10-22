"""
read_map_level.py — cấp độ trong huy hiệu tròn bên trái nhãn tên quái / boss trên bản đồ thế giới (1-2 chữ số cam sáng trên nền tối), VD "4" trước "(Boss) Skeleton Dragon".

Chọn điểm cam sáng theo màu, tách theo cột trống, so từng chữ số với mẫu ở Images/OCR/MapLevel/ (`<số>_<n>.png`, thêm bằng add_sample). `badge()` cắt huy hiệu từ hộp dòng nhãn
của read_map_label.lines().
"""
import numpy as np

from . import _pieces

FONT = "MapLevel"
MIN_SCORE = 0.75
MIN_DIGIT_HEIGHT = 5            # hàng: mảnh cam thấp hơn là đốm (vật khác màu cam gần nhãn), không phải chữ số
BADGE = (-34, -4, 10, 12)       # (x1, y1, x2, y2) so với góc trên trái hộp dòng nhãn: huy hiệu nằm ngay bên trái chữ (lấy rộng, chữ be kem không lọt qua mặt nạ cam)


def badge(screen: np.ndarray, box: tuple[int, int, int, int]) -> np.ndarray:
    """Ảnh huy hiệu cấp độ bên trái dòng nhãn `box` (x, y, w, h)."""
    x, y = box[0], box[1]
    return screen[max(0, y + BADGE[1]):y + BADGE[3], max(0, x + BADGE[0]):max(0, x + BADGE[2])]


def mask(image: np.ndarray) -> np.ndarray:
    """Điểm chữ số cam sáng của `image` (BGR) dạng 0/255."""
    b, g, r = (image[..., i].astype(np.int16) for i in range(3))
    return (((r > 190) & (g > 110) & (g < 210) & (r - b > 110)) * 255).astype(np.uint8)


def _softness(image: np.ndarray) -> np.ndarray:
    """Độ giống chữ số 0-255 (viền khử răng cưa còn giữ lại)."""
    r, b = image[..., 2].astype(np.int16), image[..., 0].astype(np.int16)
    return np.clip((r - b - 60) * 2, 0, 255).astype(np.uint8)


def split(image: np.ndarray) -> list:
    """Các chữ số của huy hiệu từ trái sang phải (ảnh mềm đã cắt theo nét)."""
    pieces = _pieces.split(mask(image), _softness(image))
    return [p for p in pieces if isinstance(p, str) or p.shape[0] >= MIN_DIGIT_HEIGHT]


def run(image: np.ndarray) -> int | None:
    """Cấp độ trong huy hiệu `image`, hoặc None nếu không có chữ số / chữ số lạ."""
    text = _pieces.read(split(image), FONT, MIN_SCORE)
    return int(text) if text and text.isdigit() else None
