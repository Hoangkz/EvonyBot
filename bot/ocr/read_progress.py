"""
read_progress.py — tiến độ nhiệm vụ event "300 / 500", "600 / 1,000" (góc phải trên
mỗi dòng nhiệm vụ ở màn Gather Troops / King's Path) -> số đã làm (300, 600).

Font này đơn cách: mỗi chữ số chiếm đúng CELL px và các chữ số sát nhau ở độ phân giải
gốc ("300" thành một khối), nên không tách theo cột trống mà chia mỗi nhóm chữ số thành
các ô CELL px tính từ mép trái. Dấu "/" (nét chéo) và "," (mảnh thấp) nhận theo hình
dạng, không cần mẫu.
"""
import re

import cv2
import numpy as np

from ._digits import read_chars

FONT = "Progress"
CELL = 7          # bề rộng một chữ số (6 px nét + 1 px khoảng)
_GROUP_GAP = 2    # khe <= 2 px vẫn cùng một số; trước "/" là khe ~3-4 px
# Tiến độ căn phải; khe > _TEXT_GAP px là chữ khác lấn vào vùng cắt (VD đuôi tiêu đề
# "...Ground Troop(s)." cách "0 / 500" ~53 px) -> chỉ giữ cụm bên phải nhất.
_TEXT_GAP = 10


def _runs(bw: np.ndarray) -> list[tuple[int, int]]:
    """Các đoạn cột có mực [x0, x1) trái -> phải."""
    lit = list(bw.any(axis=0)) + [False]
    runs, start = [], None
    for x, on in enumerate(lit):
        if on and start is None:
            start = x
        elif not on and start is not None:
            runs.append((start, x))
            start = None
    return runs


def _trim(piece: np.ndarray) -> np.ndarray:
    rows = np.flatnonzero(piece.any(axis=1))
    cols = np.flatnonzero(piece.any(axis=0))
    if rows.size == 0 or cols.size == 0:
        return piece[:0, :0]
    return piece[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1]


def _is_slash(piece: np.ndarray) -> bool:
    """Mảnh hẹp mà mực ở 1/3 trên nằm lệch phải so với 1/3 dưới (nét "/")."""
    h, w = piece.shape
    if w > h * 0.6 or w < 2:
        return False
    third = max(1, h // 3)
    top = np.flatnonzero(piece[:third].any(axis=0))
    bottom = np.flatnonzero(piece[-third:].any(axis=0))
    if top.size == 0 or bottom.size == 0:
        return False
    return top.mean() - bottom.mean() >= 1


def _groups(bw: np.ndarray) -> list:
    """Danh sách mảnh trái -> phải: "/" cho dấu gạch chéo, "," cho mảnh thấp, còn lại
    mỗi nhóm cột sát nhau là một list ảnh (mỗi ô CELL px một chữ số)."""
    pieces = []
    for x0, x1 in _runs(bw):
        piece = _trim(bw[:, x0:x1])
        pieces.append((x0, x1, piece))
    height = max((p.shape[0] for _, _, p in pieces), default=0)
    out, group, last_end = [], None, None
    for x0, x1, piece in pieces:
        if _is_slash(piece):
            out.append("/")
            group = None
        elif piece.shape[0] < height * 0.5:
            out.append(",")
            group = None
        else:
            if group is None or x0 - last_end > _GROUP_GAP:
                group = [x0, x1]
                out.append(group)
            else:
                group[1] = x1
        last_end = x1
    result = []
    for item in out:
        if isinstance(item, str):
            result.append(item)
            continue
        x0, x1 = item
        count = max(1, round((x1 - x0 + 1) / CELL))
        for i in range(count):
            cell = _trim(bw[:, x0 + i * CELL:min(x1, x0 + (i + 1) * CELL)])
            if cell.size:
                result.append(cell)
    return result


def split(image: np.ndarray) -> list:
    """Ảnh BGR -> mảnh trái -> phải: ảnh từng chữ số, "/" và ","."""
    if image.size == 0:
        return []
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return _groups(_last_text(bw))


def _last_text(bw: np.ndarray) -> np.ndarray:
    """Xoá mọi cột bên trái khe > _TEXT_GAP px cuối cùng (giữ cụm chữ bên phải nhất)."""
    runs = _runs(bw)
    for (_, prev_end), (start, _) in zip(reversed(runs[:-1]), reversed(runs[1:])):
        if start - prev_end > _TEXT_GAP:
            bw = bw.copy()
            bw[:, :start] = 0
            break
    return bw


def run(image: np.ndarray) -> int | None:
    """Số đã làm (bên trái "/") trong ảnh BGR "<số> / <số>", hoặc None nếu đọc lỗi.
    Chỉ lấy các mảnh sát ngay trước "/" (bỏ mảnh lạ phía xa bên trái)."""
    chars = split(image)
    slashes = [i for i, c in enumerate(chars) if isinstance(c, str) and c == "/"]
    if len(slashes) != 1:
        return None
    left = chars[:slashes[0]]
    while left and isinstance(left[0], str):   # "," lạc ở đầu
        left = left[1:]
    text = read_chars(left, FONT)
    digits = re.sub(r"\D", "", text or "")
    return int(digits) if digits else None
