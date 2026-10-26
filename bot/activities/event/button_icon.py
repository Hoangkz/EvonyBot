"""
button_icon.py — nhận nút event (dưới Event Center) bằng icon, ưu tiên hơn ruy băng.

Icon có ánh sáng chạy liên tục nên so ảnh màu thẳng chỉ khớp 0,7-0,9 giữa các khung; khớp qua
`laplacian()` (xám -> mờ 5x5 -> Laplacian) thì ổn định >= 0,85. Ảnh mẫu là ảnh màu thường trong
Images/Event/ButtonIcon/ (mỗi event một file, tạo bằng .claude/skills/template-images/scripts/
find_icon.py); biến đổi áp lên cả ảnh mẫu và vùng tìm. Điểm của một ảnh mẫu = điểm cao hơn của
2 cách khớp (màu thẳng, Laplacian): ảnh to phẳng như bọt cốc bia chỉ khớp tốt khi so màu thẳng
(Laplacian tự khớp chính khung cắt chỉ 0,4-0,65 vì viền), ảnh nhỏ nhiều nét thì Laplacian tốt hơn.
"""
import cv2
import numpy as np

from ...common import images_in
from .constants import BUTTON_ICON_DIR, BUTTON_ICON_REGIONS, BUTTON_ICON_THRESHOLD

_BLUR = 5
_cache: dict[str, tuple[np.ndarray, np.ndarray]] = {}   # đường dẫn ảnh mẫu -> (ảnh mẫu, ảnh mẫu đã biến đổi)


def laplacian(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32)
    return cv2.Laplacian(cv2.GaussianBlur(gray, (_BLUR, _BLUR), 0), cv2.CV_32F, ksize=3)


def icon_regions(screen: np.ndarray) -> list[tuple[int, int, int, int]]:
    """BUTTON_ICON_REGIONS (% màn hình) đổi sang pixel (x, y, w, h)."""
    h, w = screen.shape[:2]
    boxes = []
    for x0, y0, x1, y1 in BUTTON_ICON_REGIONS:
        left, top = int(w * x0 / 100), int(h * y0 / 100)
        boxes.append((left, top, int(w * x1 / 100) - left, int(h * y1 / 100) - top))
    return boxes


def find_button_icon(bot, screen: np.ndarray):
    """Điểm bấm nút event (tâm ảnh mẫu khớp tốt nhất) nếu thấy một icon trong BUTTON_ICON_DIR với
    điểm >= BUTTON_ICON_THRESHOLD trong một trong 2 vùng BUTTON_ICON_REGIONS (icon_regions); None nếu
    không có thư mục/ảnh mẫu hoặc không icon nào khớp (người gọi quay về cách tìm ruy băng)."""
    paths = images_in(BUTTON_ICON_DIR)
    for path in paths:
        if path not in _cache:
            tpl = bot._template(path)
            _cache[path] = (tpl, laplacian(tpl))
    best = None
    for ox, oy, w, h in icon_regions(screen):
        area = bot.crop(screen, ox, oy, w, h)
        area_lap = laplacian(area)
        for path in paths:
            tpl, tpl_lap = _cache[path]
            th, tw = tpl.shape[:2]
            if th > area.shape[0] or tw > area.shape[1]:
                continue
            for image, template in ((area, tpl), (area_lap, tpl_lap)):
                if template.std() < 1e-6:
                    continue
                _, score, _, (x, y) = cv2.minMaxLoc(cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED))
                if best is None or score > best[0]:
                    best = (float(score), path, (x + ox + tw // 2, y + oy + th // 2))
    if best is None or best[0] < BUTTON_ICON_THRESHOLD:
        return None
    bot.log(f"Event: button icon {best[1]} at {best[2]} score {best[0]:.3f}")
    return best[2]
