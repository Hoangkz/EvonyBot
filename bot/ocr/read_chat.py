"""
read_chat.py — tin "shared Coordinates: Lv7 (Boss) Yasha(K:1835 X:538,Y:133)" trong màn chat (tab Alliance / Whisper), ảnh cả màn hình 396 x 704.

Mỗi tin là một bong bóng màu kem (cột BUBBLE_X chạy dọc qua nó). Toạ độ là chữ XANH: tách từng ký tự cao 9-12 px (ngoặc, dấu hai chấm, phẩy bị bỏ vì thấp / cao
hơn), so với mẫu trong Images/OCR/Chat/ (số 0-9 và K, X, Y; tên file "<ký tự>_<n>.png", chữ HOA là "up" + chữ), ghép lại thành "K1835X538Y133". Tin xuống dòng giữa
"Y:" và số vẫn đọc được vì chỉ xét thứ tự các ký tự. Chỉ trả khi đọc đủ K, X, Y.

Chưa đọc: tên / cấp boss (chữ nâu cam), giờ gửi (chữ nhỏ xám) — xem FLOW.md của attack_boss.
"""
import difflib
import re

import cv2
import numpy as np

from ..context.templates import TEMPLATE_DIR, read_image
from . import _pieces

FONT = "Chat"
SHARED = "Chat/sharedCoordinates.png"      # cụm chữ "shared Coordinates:" mở đầu tin chia sẻ toạ độ
SHARED_THRESHOLD = 0.8
BUBBLE_X = 388                          # cột nằm trong lề phải của bong bóng, không có chữ
CREAM = (221, 237, 245)                 # BGR nền bong bóng
CREAM_TOL = (14, 12, 10)
MIN_BUBBLE = 50                         # px: đoạn kem ngắn hơn không phải bong bóng
AREA = (70, 660)                        # (y trên, y dưới) vùng danh sách tin; bong bóng chạm hai mép này là bị cắt
BLUE_MIN_DIFF, BLUE_MIN_B = 70, 110     # chữ xanh: (B - R) > 70 và B > 110
TEXT_X = 60                             # chữ nằm bên phải avatar
GLYPH_H = (9, 12)                       # chữ số / K X Y cao 11 px (ngoặc 15, phẩy 4, dấu hai chấm 1)
GLYPH_MIN_W = 3
SIZE = (8, 12)                          # (rộng, cao) ký tự được co về trước khi so
MAX_DIST = 0.3                          # khác biệt trung bình lớn hơn mức này: không nhận ra ký tự
LINE_GAP = 8                            # px: hai ký tự lệch tâm dọc hơn mức này là khác dòng
NAME_FONT = "ChatName"                  # mẫu chữ cam "(Boss) Yasha" / "Viking" (soft, như font Name của thẻ rally); chữ chưa có mẫu đọc thành "?"
NAME_MIN_SCORE = 0.75
NAME_SPACE_GAP = 4                      # px trống giữa hai từ
LV_WIDTH = 13                           # px: bề rộng chữ "Lv"; chữ số cấp nằm ngay sau (có thể dính vào chữ v)
DIGIT_MAX_WIDTH = 9                     # px: một chữ số rộng tối đa chừng này (rộng hơn = hai chữ số)
BAND_ABOVE, BAND_BELOW = 2, 6           # px: dòng chữ cam so với cụm "shared Coordinates:" (đuôi chữ g, y thấp hơn)
TIME_BELOW = (18, 5)                    # px: dòng giờ nằm trong khoảng này tính từ đáy bong bóng lên (y1 - 18 .. y1 - 5)
TIME_X = 68                             # chữ giờ bắt đầu ở đây (bên phải mép bong bóng)
TIME_DARK = 175                         # xám nhỏ hơn mức này là nét chữ giờ (nền kem ~ 235)
TIME_WORD_GAP = 3                       # px trống lớn hơn mức này giữa hai từ (số / đơn vị)
TIME_DIGIT_WIDTH = 7                    # px: một chữ số giờ rộng tối đa chừng này (rộng hơn = hai chữ số dính nhau)
TIME_UNIT_SCORE = 0.85                  # độ giống tối thiểu của cụm "mins ago" / "secs ago" / "day ago" với mẫu
TIME_UNITS = {"mins": 1, "secs": 1 / 60, "day": 24 * 60}    # mẫu Images/Chat/time_<đơn vị>.png -> số phút mỗi đơn vị
LIST_X = 57                             # cột trống của một dòng trong danh sách cuộc trò chuyện Whisper (giữa avatar và tên)
CONVERSATION_TOP = 36                   # mép trên vùng tin của một cuộc trò chuyện Whisper (chỉ có thanh tiêu đề)
NAME_LIST_BELOW = (3, 19)               # px: tên người gửi của dòng trong danh sách nằm trong khoảng này tính từ mép trên dòng
NAME_LIST_X = (58, 250)
NAME_LIST_DARK = 160
NAME_LIST_MIN_SCORE = 0.7
NAME_LIST_GAP = 3
NAME_MATCH = 0.75                       # độ giống tối thiểu giữa tên đọc được và tên cần tìm
CROP_ABOVE, CROP_BELOW = 2, 20          # ảnh cắt của tin: từ 2 px trên chữ "shared" tới 20 px trên đáy bong bóng (trên dòng giờ)
CROP_X = (66, 389)
CROP_THRESHOLD = 0.9
CROP_SAME_DIFF = 3.0                    # độ lệch điểm ảnh trung bình dưới mức này: hai ảnh cắt là cùng một tin
COORD = re.compile(r"K(\d+)X(\d+)Y(\d+)")

_bank: list | None = None


def label_file(char: str) -> str:
    return "up" + char if char.isupper() else char


def _samples() -> list[tuple[str, np.ndarray]]:
    global _bank
    if _bank is None:
        _bank = []
        folder = TEMPLATE_DIR / "OCR" / FONT
        for path in sorted(folder.glob("*.png")):
            name = path.stem.split("_")[0]
            image = read_image(path, cv2.IMREAD_GRAYSCALE)
            _bank.append((name[2:] if name.startswith("up") else name, _vector(image > 127)))
    return _bank


def _vector(mask: np.ndarray) -> np.ndarray:
    return cv2.resize(mask.astype(np.float32), SIZE, interpolation=cv2.INTER_AREA)


def bubbles(screen: np.ndarray, x: int = BUBBLE_X, top: int = AREA[0]) -> list[tuple[int, int]]:
    """Các bong bóng tin nhắn (y trên, y dưới) từ trên xuống; bong bóng bị cắt ở mép trên / dưới danh sách vẫn có mặt (xem `complete`). `x`: cột
    nằm trong bong bóng không có chữ (danh sách cuộc trò chuyện của Whisper: LIST_X); `top`: mép trên của vùng tin (cuộc trò chuyện Whisper không có thanh tab: CONVERSATION_TOP)."""
    column = screen[:, x].astype(int)
    cream = np.all([abs(column[:, i] - CREAM[i]) < CREAM_TOL[i] for i in range(3)], axis=0)
    cream[:top] = False
    cream[AREA[1]:] = False
    runs, start = [], None
    for y, on in enumerate(list(cream) + [False]):
        if on and start is None:
            start = y
        elif not on and start is not None:
            if y - start >= MIN_BUBBLE:
                runs.append((start, y - 1))
            start = None
    return runs


def complete(box: tuple[int, int], top: int = AREA[0]) -> bool:
    """Bong bóng nằm trọn trong danh sách (không bị cắt ở mép)."""
    return box[0] > top + 2 and box[1] < AREA[1] - 2


def _blue(screen: np.ndarray, y0: int, y1: int) -> np.ndarray:
    area = screen[y0:y1 + 1].astype(int)
    mask = ((area[..., 0] - area[..., 2]) > BLUE_MIN_DIFF) & (area[..., 0] > BLUE_MIN_B)
    mask[:, :TEXT_X] = False
    return mask.astype(np.uint8)


def glyphs(screen: np.ndarray, y0: int, y1: int) -> list[tuple[np.ndarray, tuple[int, int]]]:
    """Ký tự xanh (chữ số, K, X, Y) trong bong bóng, theo thứ tự đọc: [(mặt nạ 0/1 cắt sát, (x giữa, y giữa) trên màn hình)]."""
    mask = _blue(screen, y0, y1)
    count, _, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    found = []
    for i in range(1, count):
        x, y, w, h, _ = (int(v) for v in stats[i])
        if GLYPH_H[0] <= h <= GLYPH_H[1] and w >= GLYPH_MIN_W:
            found.append((x, y + y0, w, h))
    found.sort(key=lambda g: g[1] + g[3] / 2)
    lines, line = [], []
    for g in found:
        if line and g[1] + g[3] / 2 - (line[-1][1] + line[-1][3] / 2) > LINE_GAP:
            lines.append(line)
            line = []
        line.append(g)
    if line:
        lines.append(line)
    out = []
    for line in lines:
        for x, y, w, h in sorted(line):
            out.append((mask[y - y0:y - y0 + h, x:x + w], (x + w // 2, y + h // 2)))
    return out


def classify(mask: np.ndarray) -> str | None:
    vector = _vector(mask)
    best, label = MAX_DIST, None
    for name, sample in _samples():
        dist = float(np.abs(vector - sample).mean())
        if dist < best:
            best, label = dist, name
    return label


def blue_point(screen: np.ndarray, y0: int, y1: int) -> tuple[int, int] | None:
    """Một điểm nằm trên toạ độ xanh của bong bóng (y0, y1) để bấm vào (cả cụm "(K:1835 X:572,Y:112)" là một đường dẫn): tâm ký tự xanh ở giữa
    cụm. Không đọc chữ."""
    found = glyphs(screen, y0, y1)
    return found[len(found) // 2][1] if found else None


def message_crop(screen: np.ndarray, y0: int, y1: int):
    """Ảnh cắt của tin "shared Coordinates:" trong bong bóng (y0, y1) để tìm lại đúng tin đó trên một ảnh chụp khác (tin trôi lên khi có tin mới): phần chữ
    của tin, bỏ tên người gửi và dòng giờ (giờ đổi theo thời gian). Trả (ảnh, (dx, dy) vị trí bấm vào toạ độ so với góc trên-trái ảnh) hoặc None."""
    template = read_image(TEMPLATE_DIR / SHARED)
    area = screen[y0:y1 + 1]
    if area.shape[0] < template.shape[0] or area.shape[1] < template.shape[1]:
        return None
    _, score, _, (_, ty) = cv2.minMaxLoc(cv2.matchTemplate(area, template, cv2.TM_CCOEFF_NORMED))
    at = blue_point(screen, y0, y1)
    if score < SHARED_THRESHOLD or at is None:
        return None
    top, bottom = y0 + max(ty - CROP_ABOVE, 0), y1 - CROP_BELOW
    image = screen[top:bottom + 1, CROP_X[0]:CROP_X[1]].copy()
    return image, (at[0] - CROP_X[0], at[1] - top)


def same_crop(a: np.ndarray, b: np.ndarray) -> bool:
    """Hai ảnh cắt là cùng một nội dung tin (cùng cỡ, điểm ảnh gần như y hệt)."""
    return a.shape == b.shape and float(np.abs(a.astype(np.int16) - b.astype(np.int16)).mean()) < CROP_SAME_DIFF


def find_crop(screen: np.ndarray, image: np.ndarray, top: int) -> tuple[int, int] | None:
    """Góc trên-trái của ảnh cắt `image` trên `screen` (chỉ tìm từ hàng `top` trở xuống), hoặc None nếu không thấy."""
    area = screen[top:AREA[1]]
    if area.shape[0] < image.shape[0] or area.shape[1] < image.shape[1]:
        return None
    _, score, _, (x, y) = cv2.minMaxLoc(cv2.matchTemplate(area, image, cv2.TM_CCOEFF_NORMED))
    return (x, y + top) if score >= CROP_THRESHOLD else None


def is_shared(screen: np.ndarray, y0: int, y1: int) -> bool:
    """Bong bóng (y0, y1) có chữ "shared Coordinates:" (chỉ tin này mới được xét)."""
    template = read_image(TEMPLATE_DIR / SHARED)
    area = screen[y0:y1 + 1]
    if area.shape[0] < template.shape[0] or area.shape[1] < template.shape[1]:
        return False
    return float(cv2.matchTemplate(area, template, cv2.TM_CCOEFF_NORMED).max()) >= SHARED_THRESHOLD


def read(screen: np.ndarray, y0: int, y1: int) -> tuple[int, int, int] | None:
    """(K, X, Y) của tin "shared Coordinates:" trong bong bóng (y0, y1), hoặc None (không phải tin đó / không đọc được ký tự nào)."""
    found = _chars(screen, y0, y1)
    return found[0] if found else None


def link(screen: np.ndarray, y0: int, y1: int) -> tuple[int, int] | None:
    """Chỗ để bấm vào toạ độ (chữ xanh, giữa chữ X) của tin "shared Coordinates:" trong bong bóng: bấm vào là game nhảy tới boss."""
    found = _chars(screen, y0, y1)
    return found[1] if found else None


def _chars(screen: np.ndarray, y0: int, y1: int):
    """((K, X, Y), vị trí chữ X) của tin toạ độ, hoặc None."""
    if not is_shared(screen, y0, y1):
        return None
    text, x_at = "", None
    for mask, at in glyphs(screen, y0, y1):
        char = classify(mask)
        if char is None:
            return None
        if char == "X" and x_at is None:
            x_at = at
        text += char
    match = COORD.fullmatch(text)
    if not match or x_at is None:
        return None
    return tuple(int(g) for g in match.groups()), x_at


def list_name(screen: np.ndarray, y0: int, y1: int) -> str:
    """Tên người gửi của một dòng trong danh sách cuộc trò chuyện Whisper (chữ thường, "?" cho chữ chưa có mẫu)."""
    area = screen[y0 + NAME_LIST_BELOW[0]:y0 + NAME_LIST_BELOW[1], NAME_LIST_X[0]:NAME_LIST_X[1]]
    gray = cv2.cvtColor(area, cv2.COLOR_BGR2GRAY).astype(np.int16)
    mask = (gray < NAME_LIST_DARK).astype(np.uint8) * 255
    soft = np.clip((235 - gray) * 3, 0, 255).astype(np.uint8)
    pieces = _pieces.split(mask, soft, space_gap=NAME_LIST_GAP)
    return _pieces.read(pieces, NAME_FONT, NAME_LIST_MIN_SCORE) or ""


def same_name(read: str, wanted: str) -> bool:
    """Tên đọc được (có thể có "?") có phải tên `wanted` không: bỏ khoảng trắng / dấu, cùng độ dài thì "?" là chữ bất kỳ, rồi so độ giống."""
    a = re.sub(r"[^a-z0-9?]", "", read.lower())
    b = re.sub(r"[^a-z0-9]", "", wanted.lower())
    if not a or not b:
        return False
    if len(a) == len(b):
        a = "".join(y if x == "?" else x for x, y in zip(a, b))
    return difflib.SequenceMatcher(None, a, b).ratio() >= NAME_MATCH


def _orange(area: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Chữ cam (tên / cấp boss): mặt nạ 0/255 và ảnh "độ cam" mềm 0-255 (giữ viền khử răng cưa)."""
    b, g, r = (area[..., i].astype(np.int16) for i in range(3))
    mask = (((r - b) > 45) & (r < 215) & (g < 150)).astype(np.uint8) * 255
    return mask, np.clip((r - b - 20) * 2, 0, 255).astype(np.uint8)


def _digits(soft: np.ndarray) -> int | None:
    """Số trong vùng chữ số cấp (một hoặc hai chữ số), None nếu không đọc được."""
    mask = soft > 127
    cols = np.flatnonzero(mask.any(axis=0))
    rows = np.flatnonzero(mask.any(axis=1))
    if len(cols) == 0:
        return None
    mask = mask[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1]
    parts = [mask] if mask.shape[1] <= DIGIT_MAX_WIDTH else [mask[:, :mask.shape[1] // 2 + 1], mask[:, mask.shape[1] // 2:]]
    text = ""
    for part in parts:
        char = classify(part)
        if char is None or not char.isdigit():
            return None
        text += char
    return int(text)


def name_and_level(screen: np.ndarray, y0: int, y1: int) -> tuple[str | None, int | None]:
    """(tên, cấp) trong dòng "shared Coordinates: Lv7 (Boss) Yasha(K:...": tên là chữ thường, "?" cho chữ chưa có mẫu ("(boss) yasha"), cấp là số
    sau "Lv". Cái nào không đọc được là None."""
    template = read_image(TEMPLATE_DIR / SHARED)
    th, tw = template.shape[:2]
    area = screen[y0:y1 + 1]
    result = cv2.matchTemplate(area, template, cv2.TM_CCOEFF_NORMED)
    _, score, _, (tx, ty) = cv2.minMaxLoc(result)
    if score < SHARED_THRESHOLD:
        return None, None
    band = area[max(ty - BAND_ABOVE, 0):ty + th + BAND_BELOW, tx + tw:]
    mask, soft = _orange(band)
    cols = np.flatnonzero(mask.any(axis=0))
    if len(cols) == 0:
        return None, None
    # Từ đầu tiên là "Lv" + số cấp: cắt theo hình học vì chữ số hay dính vào chữ v.
    start = int(cols[0])
    end = start
    for c in cols:
        if c - end > NAME_SPACE_GAP and end > start:
            break
        end = int(c)
    level = _digits(soft[:, start + LV_WIDTH:end + 1]) if end + 1 - start > LV_WIDTH else None
    rest = mask.copy()
    rest[:, :end + 1] = 0
    pieces = _pieces.split(rest, soft, space_gap=NAME_SPACE_GAP)
    name = _pieces.read(pieces, NAME_FONT, NAME_MIN_SCORE)
    return (name.strip() or None) if name else None, level


def _time_line(screen: np.ndarray, y1: int):
    """Dòng giờ của bong bóng (đáy y1): (nét chữ 0/1, ảnh mềm 0-1, các từ [(cột đầu, cột cuối)]), hoặc None nếu không có chữ."""
    area = screen[y1 - TIME_BELOW[0]:y1 - TIME_BELOW[1] + 1, TIME_X:200]
    gray = cv2.cvtColor(area, cv2.COLOR_BGR2GRAY)
    dark = gray < TIME_DARK
    rows = np.flatnonzero(dark.any(axis=1))
    if len(rows) == 0:
        return None
    dark = dark[rows[0]:rows[-1] + 1]
    soft = np.clip((230.0 - gray[rows[0]:rows[-1] + 1]) * 3, 0, 255) / 255
    words, start, end = [], None, None
    for x, on in enumerate(list(dark.any(axis=0)) + [False]):
        if on:
            start = x if start is None else start
            end = x
        elif start is not None and x - end > TIME_WORD_GAP:
            words.append((start, end))
            start = None
    return (dark, soft, words) if words else None


def _time_number(dark: np.ndarray) -> int | None:
    """Số ở đầu dòng giờ (một hoặc hai chữ số; hai chữ số dính nhau thì cắt ở cột mỏng nhất)."""
    pieces, start = [], None
    for x, on in enumerate(list(dark.any(axis=0)) + [False]):
        if on and start is None:
            start = x
        elif not on and start is not None:
            pieces.append(dark[:, start:x])
            start = None
    parts = []
    for piece in pieces:
        if piece.shape[1] > TIME_DIGIT_WIDTH:
            inner = piece.sum(axis=0)[2:piece.shape[1] - 2]
            cut = 2 + int(inner.argmin())
            parts += [piece[:, :cut], piece[:, cut:]]
        else:
            parts.append(piece)
    text = ""
    for part in parts:
        rows = np.flatnonzero(part.any(axis=1))
        char = classify(part[rows[0]:rows[-1] + 1]) if len(rows) else None
        if char is None or not char.isdigit():
            return None
        text += char
    return int(text) if text else None


def _time_unit(soft: np.ndarray) -> str | None:
    """Đơn vị của cụm "<đơn vị> ago" (ảnh mềm) so với mẫu mins / secs / day; None nếu không giống mẫu nào (VD "hours", "1 min")."""
    best, name = TIME_UNIT_SCORE, None
    for unit in TIME_UNITS:
        sample = read_image(TEMPLATE_DIR / "Chat" / f"time_{unit}.png", cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255
        if abs(sample.shape[1] - soft.shape[1]) > 1 or sample.shape[0] != soft.shape[0]:
            continue
        width = min(sample.shape[1], soft.shape[1])
        a, b = sample[:, :width], soft[:, :width]
        score = float((a * b).sum() / (np.sqrt((a * a).sum() * (b * b).sum()) + 1e-6))
        if score > best:
            best, name = score, unit
    return name


def age_minutes(screen: np.ndarray, y0: int, y1: int) -> float | None:
    """Tin này gửi cách đây bao nhiêu phút (đọc dòng "22 mins ago" / "48 secs ago" / "1 day ago"); None nếu không đọc được (đơn vị lạ, số lạ)."""
    line = _time_line(screen, y1)
    if line is None:
        return None
    dark, soft, words = line
    if len(words) < 2:
        return None
    number = _time_number(dark[:, words[0][0]:words[0][1] + 1])
    unit = _time_unit(soft[:, words[1][0]:words[-1][1] + 1])
    if number is None or unit is None:
        return None
    return number * TIME_UNITS[unit]
