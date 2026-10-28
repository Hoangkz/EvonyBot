"""
lanes.py — số đường hành quân (march slot) đang dùng / tối đa, đọc ở bảng hành quân ở góc trên trái bản đồ.

- Đã dùng: số dòng của bảng. Dòng "+ Add March Slot" nằm ngay dưới dòng cuối nên vị trí y của nó cho biết số dòng (mỗi dòng cao ROW_PITCH px; 0 dòng thì ở ADD_Y0).
- Tối đa: chữ số sau dấu "/" ở bộ đếm vàng "2/5" ngay đầu bảng, đọc bằng mẫu Images/OCR/Lanes (hiện có 1, 2, 5; chữ số khác đọc ra None, khi gặp cần thêm mẫu).

Mỗi tài khoản có số đường tối đa riêng (tối đa 6, tài khoản yếu hơn ít hơn). Số đường bot dùng được còn bị chặn bởi số đội quân đã chọn ở group Troop (mỗi lần hành quân dùng một đội,
hai hành quân cùng lúc không dùng chung một đội): `capacity`.
"""
import cv2
import numpy as np

from ...context.templates import TEMPLATE_DIR, read_image
from .constants import (NO_LANES, NO_LANES_THRESHOLD, LANE_PANEL_REGION, LANE_ROWS, LANE_ADD_SLOT, LANE_ADD_Y0, LANE_DIGIT_DIST, LANE_ROW_PITCH, LANES_BOX, MAX_LANES, SPEED_PANEL)

_bank: list | None = None


def _vector(mask: np.ndarray) -> np.ndarray:
    return cv2.resize(mask.astype(np.float32), (8, 12), interpolation=cv2.INTER_AREA)


def _samples() -> list[tuple[str, np.ndarray]]:
    global _bank
    if _bank is None:
        _bank = [(path.stem.split("_")[0], _vector(read_image(path, cv2.IMREAD_GRAYSCALE) > 127))
                 for path in sorted((TEMPLATE_DIR / "OCR" / "Lanes").glob("*.png"))]
    return _bank


def used_lanes(bot, screen=None) -> int | None:
    """Số dòng của bảng hành quân (= đường đang dùng) từ vị trí dòng "+ Add March Slot"; None nếu không thấy dòng đó (bảng đang thu gọn, đang ở màn khác...)."""
    pos = bot.find(LANE_ADD_SLOT, threshold=0.8, screen=screen)
    if pos is None:
        return None
    return max(0, round((pos[1] - LANE_ADD_Y0) / LANE_ROW_PITCH))


def breakdown(bot, screen=None) -> dict[str, int]:
    """Số dòng từng loại trong bảng hành quân: Rallying (đang chờ rally), Marching (đang đi), Returning (đang về). Cả ba loại đều chiếm một đường; Rallying không xử lý gì
    (không tăng tốc), chỉ tính vào số đường đang dùng."""
    return {kind: len(bot.find_all(path, threshold=0.85, screen=screen, region=LANE_PANEL_REGION)) for kind, path in LANE_ROWS.items()}


def max_lanes(screen: np.ndarray) -> int | None:
    """Số đường tối đa của tài khoản: chữ số sau dấu "/" của bộ đếm "2/5" (chữ vàng); None nếu không đọc được."""
    x0, y0, x1, y1 = LANES_BOX
    area = screen[y0:y1, x0:x1].astype(int)
    mask = ((area[..., 2] > 100) & (area[..., 1] > 80) & (area[..., 0] < 100)).astype(np.uint8)
    pieces, start = [], None
    for x, on in enumerate(list(mask.any(axis=0)) + [False]):
        if on and start is None:
            start = x
        elif not on and start is not None:
            part = mask[:, start:x]
            rows = np.flatnonzero(part.any(axis=1))
            pieces.append(part[rows[0]:rows[-1] + 1])
            start = None
    if len(pieces) != 3:                      # chữ số, dấu "/", chữ số
        return None
    vector = _vector(pieces[2])
    best, label = LANE_DIGIT_DIST, None
    for name, sample in _samples():
        dist = float(np.abs(vector - sample).mean())
        if dist < best:
            best, label = dist, name
    return int(label) if label is not None else None


LEARNED_ATTR = "attack_lanes_cap"      # trên bot: số đường tối đa học được khi game báo hết đường (trong lượt chạy này)
USED_ATTR = "attack_lanes_used"        # trên bot: số đường đang dùng ở lần đọc bảng gần nhất
HIT_ATTR = "attack_lanes_hit"          # trên bot: vừa gặp thông báo hết đường mà chưa xử lý


def no_lanes(bot, screen=None) -> bool:
    """Đang hiện thông báo "You cannot send more troops." (hết đường hành quân)."""
    return bot.find(NO_LANES, threshold=NO_LANES_THRESHOLD, screen=screen) is not None


def learn(bot) -> int | None:
    """Game vừa báo hết đường: lưu số đường đang dùng (số dòng của bảng hành quân; bảng bị hộp thoại làm tối không đếm được thì lấy lần đọc gần nhất) làm số đường tối đa
    của tài khoản, và đặt cờ cho `consume_full`. Trả số đường học được; None nếu không biết."""
    used = used_lanes(bot) or getattr(bot, USED_ATTR, None)
    setattr(bot, HIT_ATTR, True)
    if used:
        setattr(bot, LEARNED_ATTR, used)
        bot.record(f"Attack Boss: hết đường hành quân, tối đa {used} đường")
    return used or None


def consume_full(bot) -> bool:
    """Vừa gặp thông báo hết đường (cờ do `learn` đặt) thì xoá cờ và trả True: nơi gọi chuyển sang tăng tốc / chờ đường trống."""
    hit = bool(getattr(bot, HIT_ATTR, False))
    setattr(bot, HIT_ATTR, False)
    return hit


def capacity(maximum: int | None, troops: int, learned: int | None = None) -> int:
    """Số đường bot dùng được: nhỏ nhất của MAX_LANES, số đường tối đa của tài khoản (đọc ở bộ đếm, nếu đọc được), số đường đã học khi game báo hết đường (nếu có) và
    số đội quân đã chọn; ít nhất 1."""
    return max(1, min(MAX_LANES, maximum or MAX_LANES, learned or MAX_LANES, troops))


def lanes_full(bot, troops: int) -> bool:
    """Đã dùng hết số đường chưa. Bảng hành quân đang thu gọn ("▶ March") thì bấm mở ra rồi đọc lại. Không có bảng March nào (không thấy cả dạng mở lẫn thu gọn) nghĩa là
    không có hành quân nào: chưa tấn công boss nào, còn đường (False)."""
    screen = bot.screenshot()
    used = used_lanes(bot, screen)
    if used is None:
        panel = bot.find(SPEED_PANEL, threshold=0.85, screen=screen)
        if panel is None:
            return False
        bot.tap(*panel, delay=1)
        screen = bot.screenshot()
        used = used_lanes(bot, screen)
        if used is None:
            return False
    setattr(bot, USED_ATTR, used)             # nhớ để `learn` dùng khi bảng bị hộp thoại làm tối
    return used >= capacity(max_lanes(screen), troops, getattr(bot, LEARNED_ATTR, None))
