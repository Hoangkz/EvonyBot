import threading
import unittest
from pathlib import Path
from types import SimpleNamespace

import cv2

from bot.activities.join_monster_war.constants import JOIN, REGIONS
from bot.context import BotContext

SCREENS = Path(__file__).parent / "join_monster_war" / "screens"


class FindAllTests(unittest.TestCase):
    def setUp(self):
        self.ctx = BotContext(SimpleNamespace(serial="t"), threading.Event(), None, lambda _: None)

    def _screen(self, name):
        image = cv2.imread(str(SCREENS / name))
        if image is None:
            self.skipTest(f"thiếu ảnh {name}")
        return image

    def test_region_does_not_duplicate_hits(self):
        # Một nút Join -> đúng một điểm, dù tìm trong REGIONS[JOIN].
        screen = self._screen("war_list_join_red.png")
        hits = self.ctx.find_all(JOIN, threshold=0.8, screen=screen, center=False, region=REGIONS[JOIN])
        self.assertEqual(hits, [(319, 331)])

    def test_region_and_full_screen_agree(self):
        screen = self._screen("war_list_two_join.png")
        in_region = self.ctx.find_all(JOIN, threshold=0.8, screen=screen, region=REGIONS[JOIN])
        full = self.ctx.find_all(JOIN, threshold=0.8, screen=screen)
        self.assertEqual(sorted(in_region), sorted(full))
        self.assertEqual(len(full), 2)


if __name__ == "__main__":
    unittest.main()
