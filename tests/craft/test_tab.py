"""Tab Craft: trừ số lượng sau khi bot chế tạo xong (CraftTab.craft_done / DeviceView.apply_craft_done), cấu hình lưu / nạp lại."""
import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication

from ui.tabs import CraftTab

BOW = "bow/01_Fighter's_Bow"
RING = "ring/01_Fighter's_Ring"


class CraftTabDone(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_craft_done_decrements_then_unticks(self):
        tab = CraftTab()
        tab.set_settings({"items": {BOW: 2, RING: 1}})
        tab.craft_done(BOW)
        self.assertEqual(tab.get_settings()["items"], {BOW: 1, RING: 1})
        tab.craft_done(BOW)                              # về 0: bỏ tích
        self.assertEqual(tab.get_settings()["items"], {RING: 1})
        self.assertFalse(tab.boxes[BOW][0].isChecked())
        self.assertEqual(tab.boxes[BOW][1].value(), 1)   # số lượng về mặc định để lần tích sau là 1
        tab.craft_done("bow/not_a_real_item")            # id lạ: bỏ qua
        self.assertEqual(tab.get_settings()["items"], {RING: 1})

    def test_ticked_items_are_not_touched_when_another_item_is_done(self):
        tab = CraftTab()
        tab.set_settings({"items": {RING: 3}})
        tab.craft_done(BOW)                              # BOW không được tích: không ảnh hưởng RING
        self.assertEqual(tab.get_settings()["items"], {RING: 3})


if __name__ == "__main__":
    unittest.main()
