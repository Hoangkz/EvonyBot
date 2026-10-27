"""
read_refine_lines.py — 4 dòng thuộc tính ở màn Refine Equipment (khung "Original" và khung "New"): tên thuộc tính + màu chữ của từng dòng.

    new = read_new(screen, catalog)     # [{"name": "Ground Troop Load", "color": "gold", "kind": "percent", "score": 0.88}, ...] 4 dòng từ trên xuống, hoặc None nếu không thấy khung New
    original = read_original(screen, catalog)
    meets(new, {"Ground Troop Load": ("orange", "percent")}, gold=1, orange=1)     # đủ yêu cầu chưa

`catalog` là danh sách tên thuộc tính CỦA TRANG BỊ đang làm (constants.SLOTS): chỉ so với các tên đó nên rất chắc (đo trên 224 dòng của nhẫn ở 21913: mọi dòng đều
nhận tên, tên đúng hơn tên thứ hai >= 0,11; so với cả 26 tên thì 14 % dòng không đủ chắc).

Hàng định vị theo tiêu đề khung (headerNew.png / headerOriginal.png, 1,00 trên màn đúng): dòng thứ i của khung New nằm ở y tiêu đề + NEW_OFFSETS[i], của khung
Original ở y tiêu đề + ORIGINAL_OFFSETS[i] (đo trên 21913, 396x704; khung Original ở y 246 sau khi bấm Refine, y 368 khi chưa bấm: theo tiêu đề nên đúng cả hai).

Khoá: mỗi dòng Original có ổ khoá bên trái (x ~32): vàng = đã khoá (lockOn.png), xám = chưa khoá (lockOff.png), khớp 0,85 .. 1,00 trên 21913, trạng thái kia <= 0,63 (ngưỡng 0,8). Khung New (đã cuộn) không có
ổ khoá nên `locked` = None. Dòng đã khoá giữ nguyên trong khung New (đo 21913: dòng khoá Ranged Troop Attack +35 giống hệt ở Original và New, chỉ các dòng khác đổi). Mỗi dòng
trả thêm `y` (toạ độ y trên màn hình) để bấm ổ khoá ở (LOCK_X, y). Khung Original dịch lên xuống tuỳ màn (y tiêu đề 246 / 303 / 368) nên luôn tính theo tiêu đề.

Loại tăng: dòng tăng % có "%" ở cuối giá trị ("+3.9%", khoảng "1%~10%"), dòng tăng chỉ số thì không ("+128", "1~333"). Nhận bằng mẫu ký tự "%" (percent.png) trên cột giá trị:
dòng % khớp >= 0,85, dòng chỉ số <= 0,45 (đo 224 dòng ở 21913) -> ngưỡng PERCENT_THRESHOLD.

Tên: so mặt nạ chữ với mẫu render sẵn (Images/RefineEquipment/Names/<tên>/, sinh bằng make_refine_name_samples.py; Arial ~13 px). Tên một dòng: mẫu `s.png`; tên dài
xuống hai dòng: hai mẫu `w<n>_1.png` / `w<n>_2.png`, dòng 1 phải nằm trên dòng 2, cùng lề trái. Chọn tên điểm cao nhất nếu (>= MIN_SCORE và hơn tên thứ hai >= MIN_MARGIN) hoặc (>= LOW_SCORE và hơn tên thứ hai >= LOW_MARGIN).

Màu: trung vị 1/4 điểm sáng nhất của chữ (V > 120) đổi sang HSV, phân loại theo hue + độ bão hòa (đo trên 224 dòng của 21913: thường S 60-100, tím H 143-144,
cam H 11-12 S 220-234, vàng H 24 S 195). Cam và vàng khác nhau ở hue chứ không ở độ sáng (chữ bị khử răng cưa nên V dao động).
"""
import re
from functools import lru_cache

import cv2
import numpy as np

from ..context.templates import TEMPLATE_DIR, read_image

FOLDER = "RefineEquipment"     # Images/RefineEquipment/ (khai báo riêng, không import gói activity: tránh vòng import)


def slug(name: str) -> str:
    """Tên thư mục mẫu của một thuộc tính (giống make_refine_name_samples.slug)."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")

HEADER_NEW = f"{FOLDER}/headerNew.png"
HEADER_ORIGINAL = f"{FOLDER}/headerOriginal.png"
HEADER_THRESHOLD = 0.9
NEW_OFFSETS = (36, 75, 114, 153)        # y dòng so với y tâm tiêu đề "New" (435 trên màn đo)
ORIGINAL_OFFSETS = (37, 76, 115, 154)   # y dòng so với y tâm tiêu đề "Original" (246 trên màn đo)
NAME_X = (12, 198)                      # cột tên (px): chữ của dòng
ROW_HALF = 21                           # nửa chiều cao vùng một dòng (chứa cả tên xuống hai dòng chữ)
INK_FROM = 50                           # nét chữ: (V - 50) / (V sáng nhất - 50), chuẩn hoá theo từng dòng (chữ cam / vàng / tím sáng khác chữ thường)
INK_TOP_MIN = 120
MIN_SCORE = 0.6
LOW_SCORE = 0.5                          # điểm thấp hơn MIN_SCORE (VD "Siege Machine HP" chỉ 0,59 .. 0,61 dù tên thứ hai chỉ 0,2) vẫn nhận nếu hơn tên thứ hai >= LOW_MARGIN
LOW_MARGIN = 0.25
OVERRUN_FROM, OVERRUN_TO = 4, 60        # sau chỗ mẫu khớp: nếu cách mép phải mẫu 4 .. 60 px còn chữ thì mẫu ngắn hơn dòng thật (VD "March Speed" trong "March Speed to Monsters")
OVERRUN_COLUMNS = 4                     # từng đó cột có chữ thì tính là còn chữ
OVERRUN_PENALTY = 0.3                   # điểm trừ cho mẫu chưa phủ hết dòng
WORD_GAP = 3                            # cột trống liên tiếp giữa hai từ trong mẫu (px)
MIN_WORD_WIDTH = 3                      # từ hẹp hơn thế (dấu chấm...) không chấm riêng
MIN_MARGIN = 0.08
LINE_GAP = (10, 20)                     # tên hai dòng: khoảng cách y giữa dòng 1 và dòng 2 (px)
LEFT_SLACK = 6                          # tên hai dòng: lệch x tối đa giữa hai dòng (px)
LOCK_ON = f"{FOLDER}/lockOn.png"
LOCK_OFF = f"{FOLDER}/lockOff.png"
COLOR_X_ORIGINAL = 50                    # khung Original: màu chữ chỉ đo từ cột này (bên phải ổ khoá): ổ khoá ĐÓNG màu vàng nằm trong vùng chữ làm dòng trắng / tím bị đọc thành vàng
LOCK_X = 32                             # tâm ổ khoá (px)
LOCK_BOX = (18, 48)                     # cột vùng ổ khoá khi so mẫu
LOCK_HALF = 15
LOCK_THRESHOLD = 0.8                    # đã khoá 0,92 .. 0,94, chưa khoá 0,85 .. 1,00; trạng thái kia <= 0,63
VALUE_X = (200, 286)                    # cột giá trị ("+3.9%", "+128")
VALUE_HALF = 13
PERCENT = f"{FOLDER}/percent.png"
PERCENT_THRESHOLD = 0.7
TEXT_MIN_VALUE = 120                    # điểm chữ (để tính màu): V > mức này
MIN_TEXT_PIXELS = 25                    # ít hơn thì coi là không có chữ

COLORS = ("normal", "purple", "orange", "gold")   # thứ hạng thấp -> cao; game chỉ có 4 màu: trắng ("normal", chữ be kem), tím, cam, vàng
SATURATED = 150          # cam / vàng: S từ mức này
TINTED = 100             # tím: S từ mức này


def classify(hue: int, sat: int) -> str:
    """Màu chữ của dòng theo hue (0..179) và độ bão hòa (0..255)."""
    if sat >= SATURATED and hue < 18:
        return "orange"
    if sat >= SATURATED and 18 <= hue <= 34:
        return "gold"
    if sat >= TINTED and 126 <= hue <= 165:
        return "purple"
    return "normal"


def rank(color: str | None) -> int:
    return COLORS.index(color) if color in COLORS else -1


def text_color(strip: np.ndarray) -> str | None:
    """Màu chữ của một vùng dòng (BGR); None nếu gần như không có chữ."""
    mask = strip.max(axis=2) > TEXT_MIN_VALUE
    if mask.sum() < MIN_TEXT_PIXELS:
        return None
    pixels = strip[mask]
    top = pixels[np.argsort(-pixels.max(axis=1))[:max(10, len(pixels) // 4)]]
    hue, sat, _ = cv2.cvtColor(np.median(top, axis=0).astype(np.uint8).reshape(1, 1, 3), cv2.COLOR_BGR2HSV)[0, 0]
    return classify(int(hue), int(sat))


@lru_cache(maxsize=None)
def _variants(name: str) -> dict[str, list[np.ndarray]]:
    """Mẫu của một tên: {"s": [mặt nạ]} và {"w<n>": [dòng 1, dòng 2]}."""
    out: dict[str, list] = {}
    for path in sorted((TEMPLATE_DIR / FOLDER / "Names" / slug(name)).glob("*.png")):
        key = "s" if path.stem == "s" else path.stem.split("_")[0]
        out.setdefault(key, []).append(read_image(path, cv2.IMREAD_GRAYSCALE))
    return out


def _ink(strip: np.ndarray) -> np.ndarray:
    value = strip.max(axis=2).astype(np.float32)
    top = max(float(np.percentile(value, 99.5)), float(INK_TOP_MIN))
    return (np.clip((value - INK_FROM) / (top - INK_FROM), 0, 1) * 255).astype(np.uint8)


def _fits(ink: np.ndarray, template: np.ndarray) -> bool:
    return template.shape[0] <= ink.shape[0] and template.shape[1] <= ink.shape[1]


def _match(ink: np.ndarray, template: np.ndarray):
    _, score, _, location = cv2.minMaxLoc(cv2.matchTemplate(ink, template, cv2.TM_CCOEFF_NORMED))
    return float(score), location


def _words(template: np.ndarray) -> list[tuple[int, int]]:
    """Các từ của mẫu một dòng: (cột đầu, cột cuối + 1), tách ở khoảng trống >= WORD_GAP cột."""
    cols = np.where(template.max(axis=0) > 60)[0]
    words, start, previous = [], cols[0], cols[0]
    for col in cols[1:]:
        if col - previous > WORD_GAP:
            words.append((int(start), int(previous) + 1))
            start = col
        previous = col
    return words + [(int(start), int(previous) + 1)]


def _line_score(ink: np.ndarray, template: np.ndarray):
    """(điểm, vị trí) của mẫu một dòng: trung bình điểm cả dòng và điểm TỪ YẾU NHẤT. Các tên chỉ khác một từ (Food / Lumber / Stone / Ore Gathering Speed) nên
    điểm cả dòng khó tách, còn từ khác nhau thì rất thấp."""
    whole, (x, y) = _match(ink, template)
    right = ink[y:y + template.shape[0], x + template.shape[1] + OVERRUN_FROM:x + template.shape[1] + OVERRUN_TO]
    if right.size and int((right.max(axis=0) > 100).sum()) >= OVERRUN_COLUMNS:
        whole -= OVERRUN_PENALTY         # còn chữ bên phải: mẫu này ngắn hơn dòng thật
    region = ink[y:y + template.shape[0], x:x + template.shape[1]]
    words = []
    for a, b in _words(template):
        if b - a >= MIN_WORD_WIDTH and region[:, a:b].std() > 0:
            words.append(float(cv2.matchTemplate(region[:, a:b], template[:, a:b], cv2.TM_CCOEFF_NORMED)[0, 0]))
        else:
            words.append(0.0)
    return (whole + min(words)) / 2, (x, y)


def score_name(ink: np.ndarray, name: str) -> float:
    """Điểm cao nhất của một tên trên vùng chữ `ink` (một dòng hoặc hai dòng)."""
    best = -1.0
    for key, templates in _variants(name).items():
        if key == "s":
            if _fits(ink, templates[0]):
                best = max(best, _line_score(ink, templates[0])[0])
        elif len(templates) == 2 and all(_fits(ink, t) for t in templates):
            first, (x1, y1) = _line_score(ink, templates[0])
            second, (x2, y2) = _line_score(ink, templates[1])
            if LINE_GAP[0] <= y2 - y1 <= LINE_GAP[1] and abs(x2 - x1) <= LEFT_SLACK:
                best = max(best, min(first, second))     # dòng YẾU HƠN (trung bình bị pha loãng khi hai tên chung dòng 2, VD "... Troop / Defense")
    return best


def read_name(strip: np.ndarray, catalog) -> tuple[str | None, float]:
    """(tên thuộc tính trong `catalog`, điểm) của vùng một dòng (BGR); tên None nếu không đủ chắc."""
    ink = _ink(strip)
    scores = sorted(((score_name(ink, name), name) for name in catalog), reverse=True)
    best, name = scores[0]
    second = scores[1][0] if len(scores) > 1 else -1.0
    margin = best - second
    if (best >= MIN_SCORE and margin >= MIN_MARGIN) or (best >= LOW_SCORE and margin >= LOW_MARGIN):
        return name, best
    return None, best


def kind_of(screen: np.ndarray, y: int) -> str:
    """Loại tăng của dòng ở y: "percent" nếu cột giá trị có ký tự %, không thì "flat"."""
    value = screen[max(0, y - VALUE_HALF):y + VALUE_HALF, VALUE_X[0]:VALUE_X[1]]
    template = _percent()
    if value.shape[0] < template.shape[0] or value.shape[1] < template.shape[1]:
        return "flat"
    return "percent" if _match(_ink(value), template)[0] >= PERCENT_THRESHOLD else "flat"


@lru_cache(maxsize=None)
def _percent() -> np.ndarray:
    return read_image(TEMPLATE_DIR / PERCENT, cv2.IMREAD_GRAYSCALE)


@lru_cache(maxsize=None)
def _lock_templates():
    return read_image(TEMPLATE_DIR / LOCK_ON), read_image(TEMPLATE_DIR / LOCK_OFF)


def lock_state(screen: np.ndarray, y: int) -> bool | None:
    """Ổ khoá của dòng ở y: True = đã khoá, False = chưa khoá, None = không thấy ổ khoá (khung đã cuộn)."""
    area = screen[max(0, y - LOCK_HALF):y + LOCK_HALF, LOCK_BOX[0]:LOCK_BOX[1]]
    on, off = _lock_templates()
    if area.shape[0] < on.shape[0] or area.shape[1] < on.shape[1]:
        return None
    on_score, off_score = _match(area, on)[0], _match(area, off)[0]
    if max(on_score, off_score) < LOCK_THRESHOLD:
        return None
    return on_score > off_score


def _header_y(screen: np.ndarray, header: str) -> int | None:
    template = read_image(TEMPLATE_DIR / header)
    score, location = _match(screen, template)
    return location[1] + template.shape[0] // 2 if score >= HEADER_THRESHOLD else None


def _read(screen: np.ndarray, header: str, offsets: tuple, catalog, locks: bool = False) -> list[dict] | None:
    y0 = _header_y(screen, header)
    if y0 is None:
        return None
    rows = []
    for offset in offsets:
        y = y0 + offset
        strip = screen[max(0, y - ROW_HALF):y + ROW_HALF, NAME_X[0]:NAME_X[1]]
        name, score = read_name(strip, catalog)
        color_strip = strip[:, COLOR_X_ORIGINAL - NAME_X[0]:] if locks else strip       # Original: bỏ cột ổ khoá
        rows.append({"name": name, "color": text_color(color_strip), "kind": kind_of(screen, y), "locked": lock_state(screen, y) if locks else None, "y": y, "score": round(score, 2)})
    return rows


def read_new(screen: np.ndarray, catalog) -> list[dict] | None:
    """4 dòng của khung New (sau khi bấm Refine), hoặc None nếu không thấy khung New."""
    return _read(screen, HEADER_NEW, NEW_OFFSETS, catalog)


def read_original(screen: np.ndarray, catalog) -> list[dict] | None:
    """4 dòng của khung Original (đang có), hoặc None nếu không thấy khung (trang bị chưa tinh luyện)."""
    return _read(screen, HEADER_ORIGINAL, ORIGINAL_OFFSETS, catalog, locks=True)


def satisfies(row: dict, wanted: dict[str, tuple[str, str]]) -> bool:
    """Dòng `row` có thuộc về yêu cầu không: đúng thuộc tính đã chọn, màu từ mức tối thiểu của thuộc tính đó trở lên và đúng loại tăng ("all" = cả % lẫn chỉ số)."""
    if row["name"] not in wanted:
        return False
    color, kind = wanted[row["name"]]
    return rank(row["color"]) >= rank(color) and kind in ("all", row["kind"])


def meets(rows: list[dict] | None, wanted: dict[str, tuple[str, str]], gold: int, orange: int) -> bool:
    """4 dòng `rows` đủ yêu cầu chưa. Chỉ tính các dòng thuộc yêu cầu (`satisfies`; `wanted` = {tên: (màu tối thiểu, loại tăng)}). Đủ khi có ít nhất `gold` dòng vàng và ít
    nhất `gold + orange` dòng cam trở lên của các dòng đó (vàng cũng tính là cam: yêu cầu 3 cam mà chỉ chọn Ground Troop Load thì cả 3 dòng phải là Ground Troop Load màu cam
    trở lên, 2 cam + 1 vàng vẫn đạt). Không đọc được tên / màu thì dòng đó không tính."""
    if not rows:
        return False
    eligible = [row["color"] for row in rows if satisfies(row, wanted)]
    return sum(color == "gold" for color in eligible) >= gold and sum(color in ("orange", "gold") for color in eligible) >= gold + orange
