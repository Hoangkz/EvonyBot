"""
speedup.py — tăng tốc hành quân / trở về bằng vật phẩm (Adv Troop March Speedup -50%, Troop March Speedup -30%).

Bảng hành quân ở góc trên trái của bản đồ liệt kê từng đội: nhãn "Marching..." / "Returning..." / "Rallying...", thanh thời gian và icon tăng tốc (mũi tên vàng). Bấm
icon mở popup tăng tốc: thanh thời gian còn lại và các vật phẩm (nút Use). Mức chọn ở tab (`SPEEDUP_CHOICES`):
- "No": không tăng tốc;
- "All": tăng tốc tới khi tới nơi / về xong (popup đóng);
- "5s" ... "30s": đọc thời gian còn lại một lần, tính số cái cần dùng (mỗi cái -50% thời gian còn lại) để còn không quá chừng đó rồi dùng đúng số đó;
- "1" ... "10": dùng đúng chừng đó cái vật phẩm (dừng sớm nếu đội đã tới nơi / về xong).
"""
import math

import cv2
import numpy as np

from ...common import boss_scan
from ...context.templates import TEMPLATE_DIR, read_image
from .constants import (MARCH_SPEED_KEY, RETURN_SPEED_KEY, SPEED_CELL_OFFSETS, SPEED_CELL_W, SPEED_DIGIT_DIST, SPEED_FACTOR, SPEED_ICON, SPEED_ICON_OFFSET, SPEED_ICON_SAME_ROW, SPEED_ICON_THRESHOLD, SPEED_MAX_COUNT, SPEED_MAX_USES, SPEED_OPEN_WAIT, SPEED_PANEL,
                        SPEED_ROW, SPEED_ROW_THRESHOLD, SPEED_TIME_BOX, SPEED_TIME_MIN, SPEED_TITLE, SPEED_USE_DY, SPEED_USE_WAIT, SPEED_USE_X_PERCENT)

MARCHING, RETURNING = "Marching", "Returning"
NONE, UNTIL, COUNT = "none", "until", "count"
_bank: list | None = None


def plan(setting: str | None) -> tuple[str, int]:
    """Mức chọn -> (cách dừng, số): (NONE, 0) "No" / thiếu; (UNTIL, 0) "All" (tới khi popup đóng); (UNTIL, giây) "10s"; (COUNT, số cái) "3"."""
    setting = str(setting or "No").strip()
    if setting == "No":
        return NONE, 0
    if setting == "All":
        return UNTIL, 0
    try:
        if setting.endswith("s"):
            return UNTIL, int(setting[:-1])
        return COUNT, max(1, int(setting))
    except ValueError:
        return NONE, 0


def uses_needed(remaining: int, target: int) -> int:
    """Số cái vật phẩm -50% cần dùng để thời gian còn lại `remaining` giây xuống không quá `target` giây (mỗi cái giảm một nửa thời gian còn lại): ⌈log2(remaining /
    target)⌉, 0 nếu đã đủ. `target` tối thiểu 1 giây ("All" = gần như tới nơi); tối đa SPEED_MAX_COUNT."""
    target = max(target, 1)
    if remaining <= target:
        return 0
    return min(math.ceil(math.log(remaining / target) / math.log(1 / SPEED_FACTOR)), SPEED_MAX_COUNT)


def enabled(settings: dict) -> bool:
    """Có dùng tăng tốc không: ô hành quân hoặc ô trở về khác "No"."""
    return plan(settings.get(MARCH_SPEED_KEY))[0] != NONE or plan(settings.get(RETURN_SPEED_KEY))[0] != NONE


def speed_up_all(bot, kind: str, setting: str | None) -> int:
    """Tăng tốc MỌI đội `kind` trong bảng hành quân (lần lượt từ trên xuống; mỗi lần tìm lại bảng vì dòng đã tăng tốc xong có thể biến mất). Trả tổng số cái đã dùng."""
    if plan(setting)[0] == NONE:
        return 0
    total = 0
    for index in range(len(_rows(bot, kind))):
        rows = sorted(_rows(bot, kind), key=lambda pos: pos[1])
        if index >= len(rows):
            break
        total += speed_up(bot, kind, setting, rows[index])
    return total


def speed_up(bot, kind: str, setting: str | None, row: tuple[int, int] | None = None) -> int:
    """Tăng tốc một đội `kind` (MARCHING / RETURNING) trong bảng hành quân theo mức `setting`; trả số lần đã dùng vật phẩm. `row` = tâm nhãn dòng cần tăng tốc, không có
    thì lấy dòng cuối (đội mới nhất). Không có dòng / không mở được popup thì thôi. Chỉ gọi khi đang ở bản đồ thế giới sạch.
    COUNT: dùng đúng số cái đã chọn. UNTIL: đọc thời gian còn lại MỘT lần, tính số cái cần dùng (`uses_needed`) rồi bấm dùng đúng số đó (không đọc được thì dùng tới
    khi hết SPEED_MAX_USES lần hoặc popup đóng)."""
    mode, number = plan(setting)
    if mode == NONE:
        return 0
    if row is None:
        rows = _rows(bot, kind)
        if not rows:
            return 0
        row = max(rows, key=lambda pos: pos[1])
    x, y = row
    bot.tap(*_icon(bot, x, y), delay=0)
    for _ in range(round(SPEED_OPEN_WAIT / 0.5)):
        bot.sleep(0.5)
        if bot.find(SPEED_TITLE, threshold=0.8) is not None:
            break
    else:
        bot.log(f"Attack Boss: không thấy popup tăng tốc ({kind}), bỏ qua")
        boss_scan.ensure_map(bot)       # có gì che màn hình thì Back (không bấm Back ở bản đồ sạch: game sẽ hỏi thoát)
        return 0
    if mode == COUNT:
        count, reading = number, None
    else:
        reading = remaining_seconds(bot.screenshot())
        count = uses_needed(reading, number) if reading is not None else SPEED_MAX_USES
    uses = 0
    for _ in range(count):
        use = _use_button(bot)
        if use is None:                             # không thấy tên vật phẩm: bỏ qua tăng tốc, đóng popup bằng Back
            bot.log(f"Attack Boss: không thấy tên vật phẩm tăng tốc ({kind}), bỏ qua")
            boss_scan.ensure_map(bot)
            break
        bot.tap(*use, delay=0)                      # vật phẩm đầu tiên của popup: Adv Troop March Speedup (-50%)
        uses += 1
        bot.sleep(SPEED_USE_WAIT)
        if bot.find(SPEED_TITLE, threshold=0.8) is None:     # popup đóng: đội đã tới nơi / về xong
            break
    else:
        if bot.find(SPEED_TITLE, threshold=0.8) is not None:
            bot.back(delay=1)
    bot.record(f"Attack Boss: tăng tốc {kind} ({setting}): còn {reading if reading is not None else '?'} giây, dùng {uses} cái")
    return uses


def _use_button(bot) -> tuple[int, int] | None:
    """Chỗ bấm nút Use của vật phẩm đầu tiên (Adv Troop March Speedup, -50%): x cố định (SPEED_USE_X_PERCENT % chiều rộng màn hình), y tính từ vị trí tên vật phẩm
    (ảnh `speedTitle.png`). Không tìm chữ Use / số lượng vì số lượng dài có thể tràn ra ngoài viền nút. None nếu không thấy tên vật phẩm."""
    title = bot.find(SPEED_TITLE, threshold=0.8)
    if title is None:
        return None
    width, _ = bot.window_size()
    return round(width * SPEED_USE_X_PERCENT / 100), title[1] + SPEED_USE_DY


def _icon(bot, x: int, y: int) -> tuple[int, int]:
    """Tâm icon mũi tên sang của dòng có nhãn tâm (x, y): tìm đúng icon bằng ảnh mẫu, lấy cái cùng dòng; không thấy thì tính lệch từ nhãn."""
    icons = [pos for pos in bot.find_all(SPEED_ICON, threshold=SPEED_ICON_THRESHOLD)
             if abs(pos[1] - (y + SPEED_ICON_OFFSET[1])) <= SPEED_ICON_SAME_ROW]
    if icons:
        return min(icons, key=lambda pos: abs(pos[1] - (y + SPEED_ICON_OFFSET[1])))
    return x + SPEED_ICON_OFFSET[0], y + SPEED_ICON_OFFSET[1]


def _rows(bot, kind: str) -> list:
    """Các dòng `kind` trong bảng hành quân; bảng đang thu gọn ("▶ March") thì bấm mở ra rồi tìm lại."""
    rows = bot.find_all(SPEED_ROW[kind], threshold=SPEED_ROW_THRESHOLD)
    if rows:
        return rows
    panel = bot.find(SPEED_PANEL, threshold=0.85)
    if panel is None:
        return []
    bot.tap(*panel, delay=1)
    return bot.find_all(SPEED_ROW[kind], threshold=SPEED_ROW_THRESHOLD)


def time_cells(screen: np.ndarray, shift: int = 0) -> list[np.ndarray]:
    """Sáu chữ số (hh mm ss) của thanh thời gian "00:09:16" trong popup: chữ sáng (xám trắng) trên thanh tối / xanh, cắt theo ô cố định tính từ mép trái của dãy số
    (các chữ số hay dính nhau nên không tách theo khoảng trống). `shift`: lệch thêm các ô chừng này điểm ảnh. Mỗi ô là mặt nạ 0/1 cắt sát; [] nếu không thấy chữ."""
    x0, y0, x1, y1 = SPEED_TIME_BOX
    mask = (screen[y0:y1, x0:x1].astype(int).min(axis=2) > SPEED_TIME_MIN).astype(np.uint8)
    cols = np.flatnonzero(mask.any(axis=0))
    if len(cols) == 0:
        return []
    left = int(cols[0])
    cells = []
    for offset in SPEED_CELL_OFFSETS:
        start = max(left + offset + shift, 0)
        cell = mask[:, start:start + SPEED_CELL_W]
        rows, columns = np.flatnonzero(cell.any(axis=1)), np.flatnonzero(cell.any(axis=0))
        if len(rows) == 0:
            return []
        cells.append(cell[rows[0]:rows[-1] + 1, columns[0]:columns[-1] + 1])
    return cells


def _vector(mask: np.ndarray) -> np.ndarray:
    return cv2.resize(mask.astype(np.float32), (8, 12), interpolation=cv2.INTER_AREA)


def _samples() -> list[tuple[str, np.ndarray]]:
    global _bank
    if _bank is None:
        _bank = [(path.stem.split("_")[0], _vector(read_image(path, cv2.IMREAD_GRAYSCALE) > 127))
                 for path in sorted((TEMPLATE_DIR / "OCR" / "SpeedTime").glob("*.png"))]
    return _bank


def read_digit(mask: np.ndarray) -> tuple[str | None, float]:
    """(chữ số, khác biệt với mẫu): None nếu không mẫu nào khác biệt dưới SPEED_DIGIT_DIST."""
    vector = _vector(mask)
    best, label = SPEED_DIGIT_DIST, None
    for name, sample in _samples():
        dist = float(np.abs(vector - sample).mean())
        if dist < best:
            best, label = dist, name
    return label, best


def remaining_seconds(screen: np.ndarray) -> int | None:
    """Thời gian còn lại (giây) ở thanh thời gian của popup tăng tốc ("00:01:16"); None nếu không đọc được đủ sáu chữ số. Mỗi ô thử lệch -1 / 0 / +1 điểm ảnh
    (chữ số "1" hẹp làm các ô sau lệch), lấy cách giống mẫu nhất."""
    per_shift = [time_cells(screen, shift) for shift in (-1, 0, 1)]
    digits = []
    for index in range(6):
        reads = [read_digit(cells[index]) for cells in per_shift if len(cells) == 6]
        reads = [r for r in reads if r[0] is not None]
        if not reads:
            return None
        digits.append(min(reads, key=lambda r: r[1])[0])
    text = "".join(digits)
    return int(text[:2]) * 3600 + int(text[2:4]) * 60 + int(text[4:])
