"""
OCR tiến độ "300 / 500" trên dòng có nút Go (bot.ocr.read_progress) và số lần còn
thiếu của Cultivate Generals, đọc đúng vùng bot cắt trên ảnh chụp thật.
"""
import importlib
import unittest
from pathlib import Path
from types import SimpleNamespace

import cv2

from bot.activities.event.constants import PROGRESS_FROM_GO
from bot.activities.event.gather_troops.cultivate_generals.constants import TOTAL
from bot.context import BotContext
from bot.ocr import read_progress

SCREENS = Path(__file__).parent / "screens"
# Module run.py (package export `run` là hàm cùng tên nên import theo đường dẫn module).
task = importlib.import_module("bot.activities.event.gather_troops.cultivate_generals.run")


def _progress_crop(screen, go):
    dx, dy, w, h = PROGRESS_FROM_GO
    return BotContext.crop(screen, go[0] + dx, go[1] + dy, w, h)


class ProgressOcr(unittest.TestCase):
    # (ảnh, tâm nút Go, số đã làm): "300 / 500", "300 / 1,000", "600 / 1,000".
    CASES = [
        ("06_gather_recruit_more.png", (335, 344), 300),
        ("06_gather_recruit_more.png", (335, 456), 300),
        ("08_gather_claim_all.png", (335, 456), 600),
    ]

    def test_reads_done_count(self):
        for name, go, done in self.CASES:
            with self.subTest(screen=name, go=go):
                screen = cv2.imread(str(SCREENS / name))
                self.assertEqual(read_progress(_progress_crop(screen, go)), done)

    def test_reads_cropped_samples(self):
        """Ảnh cắt sẵn vùng tiến độ trong progress/, tên file = số đã làm (có đủ 0-9)."""
        for path in sorted((Path(__file__).parent / "progress").glob("*.png")):
            with self.subTest(image=path.name):
                self.assertEqual(read_progress(cv2.imread(str(path))), int(path.stem))

    def test_read_done_at_go(self):
        """Dòng có nút Go (335, 344) ghi "300 / 500" -> đã làm 300, tổng 1000 còn thiếu 700."""
        screen = cv2.imread(str(SCREENS / "06_gather_recruit_more.png"))
        bot = SimpleNamespace(crop=BotContext.crop, log=lambda message: None)
        self.assertEqual(task._read_done(bot, screen, (335, 344)), 300)
        self.assertEqual(TOTAL - 300, 700)

    def test_no_slash_is_unreadable(self):
        """Vùng không có "a / b" (VD tiêu đề 2 dòng) -> None, không đoán bừa."""
        screen = cv2.imread(str(SCREENS / "07_generals.png"))
        self.assertIsNone(read_progress(_progress_crop(screen, (335, 344))))


if __name__ == "__main__":
    unittest.main()
