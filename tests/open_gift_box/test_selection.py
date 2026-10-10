"""Unit tests for the C# ListGiftBox-to-folder mapping."""
import unittest

from bot.activities.open_gift_box.run import _box_images


class GiftBoxSelectionTests(unittest.TestCase):
    def test_no_selection_does_nothing(self):
        self.assertEqual(_box_images({}), [])

    def test_one_selection_uses_only_its_folder(self):
        selected = _box_images({"Resource": True})
        self.assertTrue(selected)
        self.assertTrue(all("/BoxResource/" in path for path in selected))

    def test_all_boxes_expands_all_four_folders(self):
        selected = _box_images({"All": True})
        self.assertTrue(any("/BoxResource/" in path for path in selected))
        self.assertTrue(any("/Gems/" in path for path in selected))
        self.assertTrue(any("/Gold/" in path for path in selected))
        self.assertTrue(any("/etc/" in path for path in selected))

    def test_selected_images_have_no_duplicates(self):
        selected = _box_images({"Resource": True, "Gems": True})
        self.assertEqual(len(selected), len(set(selected)))


if __name__ == "__main__":
    unittest.main()
