"""
find_valuable_event.py — OCR dòng chữ vàng dưới icon ở hàng nút đáy màn thành, tìm "Valuable Event" (icon đổi liên tục nên chỉ dựa vào CHỮ):

    pos = find_valuable_event(screen)     # (x, y) tâm hai dòng chữ "Valuable / Event", hoặc None
    captions(screen)                      # [(chữ đọc được, (x, y, w, h))] mọi dòng chữ đọc được trong dải đáy, để debug

Cách đọc: cắt hàng nút đáy (REGION), lấy độ vàng của từng điểm (min(R, G) - B: chữ vàng sáng, viền tối, cỏ / thành nhạt màu bị loại), tách các dòng chữ rồi
đọc từng dòng bằng read_map_label.read (so mẫu từng chữ cái trượt dọc dòng, chọn từ khớp nhất trong LEXICON) với bộ mẫu chữ Images/OCR/Caption/
(make_caption_samples.py). Thấy dòng đọc ra "Event" thì đọc tiếp đúng chỗ ngay trên nó phải ra "Valuable": dòng này hay dính hình icon nên không tách riêng được.
Ảnh rộng khác 396 px được thu về 396 px trước khi đọc.
"""
import cv2
import numpy as np

from . import read_map_label

FONT = "Caption"
REFERENCE_WIDTH = 396
REGION = (0, 75, 77, 85.3)          # % màn hình: x0, y0, x1, y1 = hàng nút đáy, x 0-305 y 528-600 trên màn 396x704 (chữ Valuable Event ở y 571-597)
INK_FROM, INK_RANGE = 60, 120       # nét chữ: (min(R, G) - B - 60) / 120 trong 0..1
LINE_INK = 0.45                     # điểm có nét từ mức này mới dùng để tách dòng
LINE_MIN_W, LINE_MIN_H, LINE_MAX_H = 14, 6, 15
STRIP_H = 16                        # dòng chữ cắt từ y - 3 xuống chừng này hàng (đủ chữ cao + đuôi p)
PAD_X = 3                           # cột lấy thêm hai bên dòng
ABOVE_DY = 12                       # dòng "Valuable" nằm trên dòng "Event" chừng này hàng
ABOVE_PAD_X = 12                    # "Valuable" dài hơn "Event": lấy thêm chừng này cột mỗi bên
# Cả các chữ khác ở hàng nút: để dòng nào đọc ra đúng chữ của dòng đó, không bị ép thành "Event" / "Valuable".
LEXICON = read_map_label.Lexicon(["Valuable", "Event", "Empire", "Depot", "Adventure"])
# "Valuable" chỉ để xác nhận dòng "Event" (đã đọc chắc): hào quang icon hay lấp lánh đè lên "Va" nên chỉ đòi độ giống TB các chữ, không đòi từng chữ rõ như read().
# Đo trên ~400 ảnh có chữ thật: >= 0.69.
VALUABLE_MIN = 0.60

# Khoảng cách chữ của bộ mẫu này (chữ dính nhau tới -2 cột); read_map_label tra theo tên font.
read_map_label.FONT_GAPS.setdefault(FONT, ((-2, -1, 0, 1, 2), tuple(range(2, 10))))


def ink(area: np.ndarray) -> np.ndarray:
    """Ảnh nét chữ vàng (0-1) của vùng ảnh BGR."""
    area = area.astype(np.float32)
    return np.clip((np.minimum(area[..., 2], area[..., 1]) - area[..., 0] - INK_FROM) / INK_RANGE, 0, 1)


def lines(text: np.ndarray) -> list[tuple[int, int, int, int]]:
    """Hộp (x, y, w, h) các dòng chữ trên ảnh nét: chữ cách nhau dưới 6 cột gộp thành một dòng."""
    mask = (text > LINE_INK).astype(np.uint8) * 255
    merged = cv2.dilate(mask, np.ones((1, 6), np.uint8))
    _, _, stats, _ = cv2.connectedComponentsWithStats(merged)
    return [tuple(int(v) for v in s[:4]) for s in stats[1:]
            if s[2] >= LINE_MIN_W and LINE_MIN_H <= s[3] <= LINE_MAX_H]


def _strip(text: np.ndarray, x: int, y: int, w: int, pad: int = PAD_X) -> np.ndarray:
    """Dòng chữ STRIP_H hàng từ y - 3; phần ra ngoài dải (dòng sát mép) để trống."""
    top = y - 3
    strip = text[max(0, top):top + STRIP_H, max(0, x - pad):x + w + pad]
    missing_above = max(0, -top)
    return np.pad(strip, ((missing_above, STRIP_H - missing_above - strip.shape[0]), (0, 0)))


def _band(screen: np.ndarray) -> tuple[np.ndarray, int, int, float]:
    """(ảnh nét của dải đáy đã thu về 396 px, left, top, tỉ lệ màn hình / 396)."""
    height, width = screen.shape[:2]
    x0, y0, x1, y1 = REGION
    left, top = int(width * x0 / 100), int(height * y0 / 100)
    area = screen[top:int(height * y1 / 100), left:int(width * x1 / 100)]
    scale = width / REFERENCE_WIDTH
    if abs(scale - 1.0) >= 0.005:
        area = cv2.resize(area, None, fx=1 / scale, fy=1 / scale, interpolation=cv2.INTER_AREA)
    return ink(area), left, top, scale


def _valuable_score(strip: np.ndarray) -> float:
    """Độ giống trung bình các chữ của "Valuable" khi xếp vào dòng `strip` theo cách tốt nhất; 0 nếu dòng không có nét."""
    prepared = read_map_label._prepare(strip, FONT)
    if prepared is None:
        return 0.0
    return float(np.mean(read_map_label._letter_scores(prepared, "Valuable")))


def captions(screen: np.ndarray) -> list[tuple[str, tuple[int, int, int, int]]]:
    """Các dòng chữ đọc được trong dải đáy: [(chữ, hộp trên dải đã thu về 396 px)]."""
    text = _band(screen)[0]
    found = []
    for x, y, w, h in lines(text):
        result = read_map_label.read(_strip(text, x, y, w), LEXICON, font=FONT)
        if result is not None:
            found.append((result["text"], (x, y, w, h)))
    return found


def find_valuable_event(screen: np.ndarray) -> "tuple[int, int] | None":
    """Tâm hai dòng chữ "Valuable / Event" trên ảnh màn thành (BGR), hoặc None nếu không đọc được."""
    text, left, top, scale = _band(screen)
    for x, y, w, h in lines(text):
        word = read_map_label.read(_strip(text, x, y, w), LEXICON, font=FONT)
        if word is None or word["text"] != "Event":
            continue
        above = _strip(text, x, y - ABOVE_DY, w, pad=ABOVE_PAD_X)
        if _valuable_score(above) < VALUABLE_MIN:
            continue
        center_x = x + w / 2
        center_y = (y - ABOVE_DY + y + h) / 2
        return left + round(center_x * scale), top + round(center_y * scale)
    return None
