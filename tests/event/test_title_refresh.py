"""
Tự cập nhật ảnh tiêu đề (bot/activities/event/common.py refresh_template): cắt ô tiêu đề trên màn
thật, khác ảnh mẫu thì ghi đè. Ghi vào thư mục tạm (patch TEMPLATE_DIR), không đụng Images/.
"""
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import cv2
import numpy as np

from bot.activities.event import common
from bot.activities.event.constants import EVENT_LIST_TITLE, EVENT_LIST_TITLE_BOX, KINGS_PATH_TITLE
from bot.context import TEMPLATE_DIR
from bot.context.screen import ScreenMixin

SCREENS = Path(__file__).parent / "kings_path" / "screens"


def _bot():
    logs = []
    return SimpleNamespace(crop=ScreenMixin.crop, log=logs.append, record=logs.append,
                           _templates={EVENT_LIST_TITLE: "cached"}, logs=logs)


class RefreshTemplateTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir)
        patcher = mock.patch.object(common, "TEMPLATE_DIR", self.dir)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _copy(self, template):
        (self.dir / template).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(TEMPLATE_DIR / template, self.dir / template)

    def test_same_title_not_written(self):
        """Ảnh mẫu hiện tại khớp ô cắt: không ghi."""
        self._copy(EVENT_LIST_TITLE)
        bot = _bot()
        screen = cv2.imread(str(SCREENS / "04_event_list.png"))
        self.assertFalse(common.refresh_template(bot, screen, EVENT_LIST_TITLE, EVENT_LIST_TITLE_BOX))
        self.assertEqual(bot._templates, {EVENT_LIST_TITLE: "cached"})

    def test_different_title_overwritten(self):
        """Ảnh mẫu cũ khác (lấy tiêu đề King's Path làm ảnh "cũ", như đổi đợt lễ hội): ghi đè bằng ô
        cắt, bỏ bản đã nạp."""
        (self.dir / EVENT_LIST_TITLE).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(TEMPLATE_DIR / KINGS_PATH_TITLE, self.dir / EVENT_LIST_TITLE)
        bot = _bot()
        screen = cv2.imread(str(SCREENS / "04_event_list.png"))
        self.assertTrue(common.refresh_template(bot, screen, EVENT_LIST_TITLE, EVENT_LIST_TITLE_BOX))
        written = cv2.imread(str(self.dir / EVENT_LIST_TITLE))
        x, y, w, h = EVENT_LIST_TITLE_BOX
        self.assertTrue(np.array_equal(written, screen[y:y + h, x:x + w]))
        self.assertNotIn(EVENT_LIST_TITLE, bot._templates)


    def test_blank_area_not_written(self):
        """Vùng trơn (VD màn đen lúc đang tải): không ghi."""
        bot = _bot()
        screen = np.zeros((704, 396, 3), np.uint8)
        self.assertFalse(common.refresh_template(bot, screen, EVENT_LIST_TITLE, EVENT_LIST_TITLE_BOX))
        self.assertFalse((self.dir / EVENT_LIST_TITLE).exists())


if __name__ == "__main__":
    unittest.main()
