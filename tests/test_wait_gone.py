import threading
import time
import unittest
from pathlib import Path
from unittest import mock

import cv2
import numpy as np
from PIL import Image

from bot.activities.join_monster_war.constants import JOIN, LISTBOSS
from bot.common import wait_gone
from tests.flow import FlowContext, _Clock

SCREENS = Path(__file__).parent / "join_monster_war" / "screens"
TARGETS = [(LISTBOSS, "tap"), (JOIN, "join_list")]


class _Device:
    """Trả lần lượt các ảnh trong `names` (ảnh cuối lặp lại mãi)."""
    serial = "t"

    def __init__(self, names):
        self.images = [Image.open(SCREENS / n).convert("RGB") for n in names]
        self.shots = 0

    def screenshot(self):
        self.shots += 1
        return self.images[min(self.shots, len(self.images)) - 1]


class WaitGoneTests(unittest.TestCase):
    def _run(self, names, action, pos):
        if not all((SCREENS / n).exists() for n in names):
            self.skipTest("thiếu ảnh")
        clock, stop = _Clock(), threading.Event()
        device = _Device(names)
        ctx = FlowContext(device, stop, clock, lambda _: None)
        with mock.patch.object(time, "monotonic", clock):
            screen = wait_gone(ctx, TARGETS, action, pos)
        return screen, device, clock

    def test_returns_screen_once_changed(self):
        # listboss (364, 411) trên màn hình chính; ảnh thứ 2 là danh sách War.
        screen, device, _ = self._run(["01_home_listboss.png", "01_home_listboss.png",
                                       "02_war_list_join.png"], "tap", (364, 411))
        self.assertEqual(device.shots, 3)
        expected = cv2.cvtColor(np.array(device.images[2]), cv2.COLOR_RGB2BGR)
        self.assertTrue(np.array_equal(screen, expected))   # đúng ảnh màn hình mới

    def test_returns_none_on_timeout(self):
        # Màn hình không đổi -> hết 10 giây -> None (nơi gọi phải chụp lại).
        screen, _, clock = self._run(["01_home_listboss.png"], "tap", (364, 411))
        self.assertIsNone(screen)
        self.assertGreaterEqual(clock.now - 1000, 10)


if __name__ == "__main__":
    unittest.main()
