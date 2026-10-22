"""
read_boss_popup.py — tên boss ở đầu cửa sổ thông tin boss (hiện sau khi bấm vào boss rồi bấm Attack), VD "Medium Hydra" / "(Boss) Manticore", chữ be kem cỡ lớn bên phải huy hiệu "Lv".

Cùng cách đọc với nhãn trên bản đồ (read_map_label: so mẫu từng chữ với danh sách tên), chỉ khác bộ mẫu chữ lớn Images/OCR/PopupName/ (make_map_samples.py PopupName). Cửa sổ cao thấp
tuỳ số vật phẩm nên vị trí tên không cố định: tìm huy hiệu "Lv" đỏ làm điểm tựa (tên nằm bên phải, ngay dưới mép trên huy hiệu). Tên dài xuống hai dòng ("Legendary Bayar" / "Knight"): mỗi
dòng đọc riêng với danh sách "nửa đầu" / "nửa sau" các tên rồi ghép. Cấp độ và sức mạnh trong cửa sổ không đọc (cấp suy ra từ tầng trong tên).
"""
import cv2
import numpy as np

from . import read_map_label

FONT = "PopupName"
FONT2 = "PopupName2"                 # chữ nhỏ hơn của tên xuống hai dòng
BADGE_AREA = (0, 60, 80, 420)        # (x1, y1, x2, y2): huy hiệu "Lv" đỏ nằm ở góc trái đầu cửa sổ (y đầu cửa sổ từ khoảng 80 tới 140 tuỳ độ cao cửa sổ)
NAME_X = (6, 181)                    # tên nằm trong khoảng này bên phải mép phải huy hiệu (px)
NAME_Y = (6, 66)                     # ... và trong khoảng này dưới mép trên huy hiệu (đủ hai dòng)
LINE_H = 40                          # chiều cao một dòng khi đọc (đủ khung chữ + đuôi g, y, p)
INK_FROM, INK_RANGE, CREAM = 110, 110, 70
SCALES = (1.0, 1.15, 1.3, 1.48, 1.65)   # cỡ chữ tên tự co theo độ dài (tên dài chữ nhỏ hơn: cỡ 23 -> 14 khi xuống hai dòng): thử phóng dòng chữ lên từng tỉ lệ rồi đọc bằng mẫu cỡ 23


def badge(screen: np.ndarray) -> tuple[int, int, int, int] | None:
    """Hộp (x, y, w, h) huy hiệu "Lv" đỏ của cửa sổ thông tin trên `screen` (BGR), hoặc None nếu không thấy (không phải cửa sổ thông tin)."""
    x1, y1, x2, y2 = BADGE_AREA
    hsv = cv2.cvtColor(screen[y1:y2, x1:x2], cv2.COLOR_BGR2HSV)
    red = (((hsv[..., 0] < 8) | (hsv[..., 0] > 172)) & (hsv[..., 1] > 150) & (hsv[..., 2] > 70)).astype(np.uint8)
    count, _, stats, _ = cv2.connectedComponentsWithStats(red, 8)
    best = max(range(1, count), key=lambda i: stats[i][4], default=None)
    if best is None or stats[best][4] < 1500:
        return None
    x, y, w, h = (int(v) for v in stats[best][:4])
    return x + x1, y + y1, w, h


def name_lines(screen: np.ndarray) -> list[np.ndarray]:
    """Ảnh nét chữ (0-1) từng dòng của tên boss (1 hoặc 2 dòng), mỗi dòng LINE_H hàng, chỉ giữ nét của dòng đó."""
    box = badge(screen)
    if box is None:
        return []
    x, y, w, _ = box
    crop = screen[y + NAME_Y[0]:y + NAME_Y[1], x + w + NAME_X[0]:x + w + NAME_X[1]]
    r, g = crop[..., 2].astype(np.float32), crop[..., 1].astype(np.float32)
    ink = np.clip((r - INK_FROM) / INK_RANGE, 0, 1) * (g * 100 > r * CREAM)
    rows = ink.max(axis=1) >= 0.3
    lines, start = [], None
    for i, on in enumerate(list(rows) + [False]):
        if on and start is None:
            start = i
        elif not on and start is not None:
            if i - start >= 6:                       # dòng chữ cao hơn 6 hàng, thấp hơn là nét rời
                lines.append((start, i))
            start = None
    merged = []
    for top, bottom in lines:                        # đuôi g, y, p cách rời phần trên: gộp các dải cách nhau dưới 3 hàng
        if merged and top - merged[-1][1] < 3:
            merged[-1] = (merged[-1][0], bottom)
        else:
            merged.append((top, bottom))
    out = []
    for top, bottom in merged[:2]:
        frame = np.zeros((LINE_H, ink.shape[1]), np.float32)
        lo = max(0, top - 2)
        hi = min(ink.shape[0], bottom + 5)
        offset = 8 + (lo - top)                      # đỉnh chữ nằm cách đầu khung 8 hàng
        frame[max(0, offset):max(0, offset) + (hi - lo)] = ink[lo:hi][:LINE_H - max(0, offset)]
        out.append(frame)
    return out


def read_name(screen: np.ndarray, lexicon: read_map_label.Lexicon, halves=None) -> dict | None:
    """Tên boss trong cửa sổ thông tin: {"text", "mean", "min", "weak"} (text là một chuỗi trong `lexicon`) hoặc None. Dòng đầu đọc thẳng với `lexicon`; không ra thì thử tên hai dòng, cần `halves` =
    (Lexicon các nửa đầu, Lexicon các nửa sau, {(nửa đầu, nửa sau): tên đầy đủ})."""
    lines = name_lines(screen)
    if not lines:
        return None
    for scale in SCALES:                                      # tên một dòng: thử từng tỉ lệ phóng, cái nào đọc ra tên trong danh sách trước thì lấy
        line = lines[0] if scale == 1.0 else np.clip(cv2.resize(lines[0], None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC), 0, 1)
        single = read_map_label.read(line, lexicon, font=FONT)
        if single:
            return single
    if len(lines) < 2 or halves is None:
        return None
    first_lexicon, second_lexicon, table = halves             # tên hai dòng: dòng đầu không phải một tên đầy đủ (dòng thứ hai nếu là dòng sức mạnh thì ghép không ra tên nào)
    a = read_map_label.read(lines[0], first_lexicon, font=FONT2)
    b = read_map_label.read(lines[1], second_lexicon, font=FONT2)
    text = table.get((a["text"], b["text"])) if a and b else None
    if text:
        return {"text": text, "mean": min(a["mean"], b["mean"]), "min": min(a["min"], b["min"]), "weak": a["weak"] + b["weak"]}
    return None
