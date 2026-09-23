"""
screen.py — screenshots and template matching.
"""
import time

import cv2
import numpy as np

from .templates import DEFAULT_THRESHOLD, TEMPLATE_DIR


class ScreenMixin:
    def screenshot(self) -> np.ndarray:
        """Current screen as a BGR image (OpenCV format)."""
        self.check()
        image = self.device.screenshot().convert("RGB")
        return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    def _template(self, name: "str | np.ndarray") -> np.ndarray:
        """A template by path under Images/, or an image passed through as-is
        (e.g. a region cropped from an earlier screenshot)."""
        if isinstance(name, np.ndarray):
            return name
        if name not in self._templates:
            path = TEMPLATE_DIR / name
            image = cv2.imread(str(path))
            if image is None:
                raise FileNotFoundError(f"Template not found: {path}")
            self._templates[name] = image
        return self._templates[name]

    @staticmethod
    def crop(image: np.ndarray, x: int, y: int, w: int, h: int) -> np.ndarray:
        """Region of `image` (clipped to its bounds)."""
        x, y = max(x, 0), max(y, 0)
        return image[y:y + max(h, 0), x:x + max(w, 0)].copy()

    @staticmethod
    def _match(screen: np.ndarray, tpl: np.ndarray):
        """matchTemplate scores, or None if the template can't fit on screen."""
        if (tpl.size == 0 or tpl.shape[0] > screen.shape[0] or tpl.shape[1] > screen.shape[1]):
            return None
        return cv2.matchTemplate(screen, tpl, cv2.TM_CCOEFF_NORMED)

    def template_size(self, template: "str | np.ndarray") -> tuple[int, int]:
        """(width, height) of a template image."""
        h, w = self._template(template).shape[:2]
        return w, h

    def find(self, template: "str | np.ndarray", threshold: float = DEFAULT_THRESHOLD,
             screen: np.ndarray | None = None, center: bool = True):
        """Position of `template` (path under Images/, or an image) on screen,
        or None. Returns its center, or its top-left corner with center=False."""
        screen = self.screenshot() if screen is None else screen
        tpl = self._template(template)
        result = self._match(screen, tpl)
        if result is None:
            return None
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val < threshold:
            return None
        if not center:
            return max_loc
        h, w = tpl.shape[:2]
        return max_loc[0] + w // 2, max_loc[1] + h // 2

    def find_all(self, template: "str | np.ndarray", threshold: float = DEFAULT_THRESHOLD,
                 screen: np.ndarray | None = None, center: bool = True) -> list[tuple[int, int]]:
        """Every match of `template` on screen (overlapping hits merged): their
        centers, or their top-left corners with center=False."""
        screen = self.screenshot() if screen is None else screen
        tpl = self._template(template)
        h, w = tpl.shape[:2]
        result = self._match(screen, tpl)
        if result is None:
            return []
        ys, xs = np.where(result >= threshold)
        # Best scores first, then drop hits that overlap one already kept.
        hits = sorted(zip(xs, ys), key=lambda p: result[p[1], p[0]], reverse=True)
        kept: list[tuple[int, int]] = []
        for x, y in hits:
            if all(abs(x - kx) >= w // 2 or abs(y - ky) >= h // 2 for kx, ky in kept):
                kept.append((int(x), int(y)))
        if not center:
            return kept
        return [(x + w // 2, y + h // 2) for x, y in kept]

    def wait_for(self, template: str, timeout: float = 10, threshold: float = DEFAULT_THRESHOLD,
                 interval: float = 0.5):
        """Poll until `template` shows up; returns its center or None on timeout."""
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            pos = self.find(template, threshold)
            if pos is not None:
                return pos
            self.sleep(interval)
        return None

    def tap_image(self, template: str, timeout: float = 10, threshold: float = DEFAULT_THRESHOLD,
                  delay: float = 0.5) -> bool:
        """Wait for `template` and tap it. Returns False if it never appeared."""
        pos = self.wait_for(template, timeout, threshold)
        if pos is None:
            return False
        self.tap(*pos, delay=delay)
        return True
