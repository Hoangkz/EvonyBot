import unittest
from pathlib import Path

import cv2

from bot.ocr.find_valuable_event import captions, find_valuable_event

SCREENS = Path(__file__).parent / "screens"


class FindValuableEventTest(unittest.TestCase):
    def test_reads_caption_on_real_lobby(self):
        # Cùng dòng chữ trên hai icon khác nhau (đã nhận / còn quà).
        for state in ("done", "pending"):
            with self.subTest(state=state):
                screen = cv2.imread(str(SCREENS / f"lobby_valuable_event_{state}.png"))
                x, y = find_valuable_event(screen)
                self.assertAlmostEqual(260, x, delta=4)
                self.assertAlmostEqual(584, y, delta=4)

    def test_reads_other_captions_as_themselves(self):
        screen = cv2.imread(str(SCREENS / "lobby_valuable_event_done.png"))
        words = {text for text, _ in captions(screen)}
        self.assertTrue({"Adventure", "Depot", "Event"} <= words)

    def test_scales_with_screen_width(self):
        screen = cv2.imread(str(SCREENS / "lobby_valuable_event_done.png"))
        big = cv2.resize(screen, (540, 960), interpolation=cv2.INTER_CUBIC)
        x, y = find_valuable_event(big)
        self.assertAlmostEqual(260 * 540 / 396, x, delta=6)
        self.assertAlmostEqual(584 * 540 / 396, y, delta=6)

    def test_no_caption_no_result(self):
        screen = cv2.imread(str(SCREENS / "lobby_valuable_event_done.png"))
        screen[565:600, 225:300] = 0     # xoá riêng chữ Valuable Event
        self.assertIsNone(find_valuable_event(screen))


if __name__ == "__main__":
    unittest.main()
