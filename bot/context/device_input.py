"""
device_input.py — taps, swipes, keys and shell commands sent to the device.
"""


class InputMixin:
    def tap(self, x: int, y: int, delay: float = 0):
        self.check()
        self.device.click(x, y)
        self.sleep(delay)

    def tap_percent(self, x: float, y: float, count: int = 1, delay: float = 0):
        """tap() with coordinates given as 0-100 % of the screen size, `count` times."""
        w, h = self.window_size()
        for _ in range(count):
            self.tap(int(w * x / 100), int(h * y / 100))
        self.sleep(delay)

    def shell(self, command: str) -> str:
        self.check()
        return self.device.shell(command)

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: float = 0.3, delay: float = 0):
        self.check()
        self.device.swipe(x1, y1, x2, y2, duration)
        self.sleep(delay)

    def swipe_percent(self, x1: float, y1: float, x2: float, y2: float,
                      duration: float = 0.3, delay: float = 0):
        """swipe() with coordinates given as 0-100 % of the screen size."""
        w, h = self.window_size()
        self.swipe(int(w * x1 / 100), int(h * y1 / 100), int(w * x2 / 100), int(h * y2 / 100),
                   duration, delay)

    def back(self, delay: float = 0):
        self.check()
        self.device.keyevent("KEYCODE_BACK")
        self.sleep(delay)

    def window_size(self) -> tuple[int, int]:
        if self._window_size is None:
            w, h = self.device.window_size()
            self._window_size = (w, h)
        return self._window_size
