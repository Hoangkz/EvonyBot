"""
find_valuable_event.py — tìm nút "Valuable Event" ở hàng nút đáy màn thành:

    pos = find_valuable_event(screen)     # (x, y) tâm dòng chữ "Event" dưới icon, hoặc None
    captions(screen)                      # [(chữ / đoạn chữ đọc được, (x, y, w, h))] mọi dòng đọc được trong vùng, để debug

Hai bước, cùng vùng tìm REGION:
1. So các ảnh mẫu chữ "Event" trong thư mục TEXT_DIR (cắt từ nút thật; nền sau chữ đổi theo icon nên cần nhiều mẫu, cắt thêm thì thả vào thư mục), ngưỡng
   TEXT_THRESHOLD. Khớp thì trả về tâm chỗ khớp.
2. Không mẫu nào khớp: OCR dòng chữ vàng dưới icon như dưới đây.

Cách đọc: cắt hàng nút đáy (REGION), lấy độ vàng của từng điểm (min(R, G) - B: chữ vàng sáng, viền tối, cỏ / thành nhạt màu bị loại), tách các dòng chữ rồi
đọc từng dòng bằng mẫu từng chữ cái (read_map_label, bộ mẫu Images/OCR/Caption/ sinh bằng make_caption_samples.py): đọc cả từ "Valuable" / "Event", không được thì đọc
một đoạn ít nhất MIN_PART chữ cái nằm trong một từ.

Quy tắc: ở vùng này chỉ "Valuable Event" có các chữ đó, nên dòng nào đọc ra "Valuable", "Event" hay một đoạn của hai từ này (VD "Val", "abl", "Eve" khi OCR
lỗi một phần) là chỗ Valuable Event. Nhiều dòng khớp: lấy dòng có y lớn nhất.
Ảnh rộng khác 396 px được thu về 396 px trước khi đọc.
"""
import cv2
import numpy as np

from . import read_map_label
from ..context.templates import TEMPLATE_DIR, read_image

FONT = "Caption"
REFERENCE_WIDTH = 396
REGION = (0, 75, 77, 87)            # % màn hình: x0, y0, x1, y1 = hàng nút đáy, x 0-305 y 528-612 trên màn 396x704 (chữ Valuable Event ở y 571-597)
# Mẫu chữ "Event" (mọi *.png trong thư mục, cắt trên màn 396x704; 5 mẫu đầu 36x11 sát chữ ở x 242 y 584 từ 5 ảnh 24/10 có nền khác nhau nhất).
TEXT_DIR = "GiftClaims/ValuableEvent/event_text"
TEXT_THRESHOLD = 0.8
INK_FROM, INK_RANGE = 60, 120       # nét chữ: (min(R, G) - B - 60) / 120 trong 0..1
LINE_INK = 0.45                     # điểm có nét từ mức này mới dùng để tách dòng
LINE_MIN_W, LINE_MIN_H, LINE_MAX_H = 14, 6, 15
STRIP_H = 16                        # dòng chữ cắt từ y - 3 xuống chừng này hàng (đủ chữ cao + đuôi p)
PAD_X = 3                           # cột lấy thêm hai bên dòng
MIN_PART = 3                        # đọc một đoạn: ít nhất chừng này chữ cái
# Chỉ hai từ này: chữ các nút khác ở hàng đổi theo sự kiện, không liệt kê được. Dòng chữ khác có đoạn trùng (VD "vent" trong "Adventure") không khớp
# vì phần nét nằm ngoài đoạn ("Ad", "ure") bị trừ điểm (read_map_label.LAMBDA).
WORDS = ("Valuable", "Event")
LEXICON = read_map_label.Lexicon(WORDS, names=WORDS)
# Mọi chữ cái phải giống từ mức này (không cho chữ yếu nào như nhãn boss): chỉ có hai từ nên chữ khác bị ép vào ("Depot" -> "Event", "Advanced" -> "Valuable")
# luôn có một chữ 0.47-0.57; chữ thật kém nhất >= 0.69.
LETTER_MIN = 0.63

_cache: dict = {}

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


def _area(screen: np.ndarray) -> tuple[np.ndarray, int, int, float]:
    """(vùng REGION đã thu về 396 px, left, top, tỉ lệ màn hình / 396)."""
    height, width = screen.shape[:2]
    x0, y0, x1, y1 = REGION
    left, top = int(width * x0 / 100), int(height * y0 / 100)
    area = screen[top:int(height * y1 / 100), left:int(width * x1 / 100)]
    scale = width / REFERENCE_WIDTH
    if abs(scale - 1.0) >= 0.005:
        area = cv2.resize(area, None, fx=1 / scale, fy=1 / scale, interpolation=cv2.INTER_AREA)
    return area, left, top, scale


def _band(screen: np.ndarray) -> tuple[np.ndarray, int, int, float]:
    """(ảnh nét của vùng đã thu về 396 px, left, top, tỉ lệ màn hình / 396)."""
    area, left, top, scale = _area(screen)
    return ink(area), left, top, scale


def _text_templates() -> list[np.ndarray]:
    """Các mẫu chữ "Event" trong TEXT_DIR; quét lại thư mục mỗi lần gọi để mẫu mới thả vào được dùng ngay (ảnh đã đọc thì nhớ lại)."""
    templates = []
    for path in sorted((TEMPLATE_DIR / TEXT_DIR).glob("*.png")):
        key = ("text", str(path))
        if key not in _cache:
            _cache[key] = read_image(path)
        if _cache[key] is not None:
            templates.append(_cache[key])
    return templates


def find_text(screen: np.ndarray) -> "tuple[int, int] | None":
    """Bước 1: tâm chỗ khớp nhất với một mẫu chữ "Event" (>= TEXT_THRESHOLD), hoặc None."""
    area, left, top, scale = _area(screen)
    best = None
    for template in _text_templates():
        if area.shape[0] < template.shape[0] or area.shape[1] < template.shape[1]:
            continue
        _, score, _, (x, y) = cv2.minMaxLoc(cv2.matchTemplate(area, template, cv2.TM_CCOEFF_NORMED))
        if score >= TEXT_THRESHOLD and (best is None or score > best[0]):
            best = (score, x + template.shape[1] / 2, y + template.shape[0] / 2)
    if best is None:
        return None
    return left + round(best[1] * scale), top + round(best[2] * scale)


def read_line(strip: np.ndarray) -> str | None:
    """Chữ đọc được trên một dòng: cả một từ trong WORDS, không thì một đoạn (>= MIN_PART chữ cái) nằm trong một từ; mọi chữ cái >= LETTER_MIN. None nếu không đọc được."""
    full = read_map_label.read(strip, LEXICON, font=FONT)
    if full is not None and full["min"] >= LETTER_MIN:
        return full["text"]
    prepared = read_map_label._prepare(strip, FONT)
    if prepared is None:
        return None
    mean, part = read_map_label._search(prepared, LEXICON.fragment_root(), any_end=True, min_letters=MIN_PART)
    if part is None or mean < read_map_label.MIN_MEAN - 0.1:
        return None
    scores = read_map_label._letter_scores(prepared, part)
    if min(scores) < LETTER_MIN or read_map_label._check(scores, MIN_PART, 0) is None:
        return None
    return part


def captions(screen: np.ndarray) -> list[tuple[str, tuple[int, int, int, int]]]:
    """Các dòng đọc được trong vùng: [(chữ / đoạn chữ, hộp trên vùng đã thu về 396 px)]."""
    text = _band(screen)[0]
    found = []
    for x, y, w, h in lines(text):
        part = read_line(_strip(text, x, y, w))
        if part is not None:
            found.append((part, (x, y, w, h)))
    return found


def find_ocr(screen: np.ndarray) -> "tuple[int, int] | None":
    """Bước 2: tâm dòng chữ của Valuable Event đọc bằng OCR, hoặc None. Nhiều dòng khớp thì lấy dòng có y lớn nhất."""
    text, left, top, scale = _band(screen)
    best = None
    for x, y, w, h in lines(text):
        part = read_line(_strip(text, x, y, w))
        if part is None:
            continue
        center = (x + w / 2, y + h / 2)
        if best is None or center[1] > best[1]:
            best = center
    if best is None:
        return None
    return left + round(best[0] * scale), top + round(best[1] * scale)


def find_valuable_event(screen: np.ndarray) -> "tuple[int, int] | None":
    """Tâm dòng chữ "Event" của nút Valuable Event trên ảnh màn thành (BGR), hoặc None: so mẫu chữ "Event" trước, không khớp thì OCR."""
    return find_text(screen) or find_ocr(screen)
