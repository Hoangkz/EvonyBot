"""
Tự thêm ảnh tiêu đề danh sách event (bot/activities/event/common.py add_title / event_list_titles):
cắt ô tiêu đề trên màn thật, khác MỌI ảnh tiêu đề đã có thì lưu thành ảnh mới <n>.png trong thư
mục tự học (không ghi đè title.png). Thư mục tự học là thư mục tạm (patch LEARNED_TITLES_DIR),
không đụng Images/ lẫn %LOCALAPPDATA%.
"""
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import cv2
import numpy as np

from bot.activities.event import common, constants
from bot.activities.event.constants import EVENT_LIST_TITLE, EVENT_LIST_TITLE_BOX, KINGS_PATH_TITLE
from bot.context import TEMPLATE_DIR
from bot.context.screen import ScreenMixin

SCREENS = Path(__file__).parent / "kings_path" / "screens"


def _bot():
    logs = []
    return SimpleNamespace(crop=ScreenMixin.crop, log=logs.append, record=logs.append, logs=logs)


def _screen(name):
    return cv2.imread(str(SCREENS / name))


class AddTitleTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir)
        patcher = mock.patch.object(constants, "LEARNED_TITLES_DIR", self.dir)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_same_title_not_saved(self):
        """Ô cắt giống title.png ("Wine Festival Event"): không lưu."""
        self.assertFalse(common.add_title(_bot(), _screen("04_event_list.png"),
                                          common.event_list_titles(), self.dir, EVENT_LIST_TITLE_BOX))
        self.assertEqual(list(self.dir.glob("*.png")), [])

    def test_new_title_saved_as_new_file(self):
        """Tiêu đề khác (lấy màn King's Path, như đổi đợt lễ hội): lưu 1.png, title.png giữ nguyên,
        event_list_titles có thêm ảnh mới; gặp lại thì không lưu thêm."""
        original = (TEMPLATE_DIR / EVENT_LIST_TITLE).read_bytes()
        screen = _screen("day1_city_tax.png")
        self.assertTrue(common.add_title(_bot(), screen, common.event_list_titles(), self.dir,
                                         EVENT_LIST_TITLE_BOX))
        saved = self.dir / "1.png"
        x, y, w, h = EVENT_LIST_TITLE_BOX
        self.assertTrue(np.array_equal(cv2.imread(str(saved)), screen[y:y + h, x:x + w]))
        self.assertEqual((TEMPLATE_DIR / EVENT_LIST_TITLE).read_bytes(), original)
        self.assertIn(str(saved), common.event_list_titles())
        self.assertFalse(common.add_title(_bot(), screen, common.event_list_titles(), self.dir,
                                          EVENT_LIST_TITLE_BOX))

    def test_next_number(self):
        """Đã có 1.png (tiêu đề khác): ảnh mới là 2.png."""
        shutil.copy(TEMPLATE_DIR / KINGS_PATH_TITLE, self.dir / "1.png")
        self.assertTrue(common.add_title(_bot(), _screen("day1_city_tax.png"),
                                         common.event_list_titles(), self.dir, EVENT_LIST_TITLE_BOX))
        self.assertTrue((self.dir / "2.png").exists())

    def test_blank_area_not_saved(self):
        """Vùng trơn (VD màn đen lúc đang tải): không lưu."""
        screen = np.zeros((704, 396, 3), np.uint8)
        self.assertFalse(common.add_title(_bot(), screen, common.event_list_titles(), self.dir,
                                          EVENT_LIST_TITLE_BOX))
        self.assertEqual(list(self.dir.glob("*.png")), [])


if __name__ == "__main__":
    unittest.main()
