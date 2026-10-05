"""Unit tests for the C# ListGiftBox-to-folder mapping."""
import unittest

from bot.activities.open_gift_box.run import _box_images


class GiftBoxSelectionTests(unittest.TestCase):
    def test_no_selection_does_nothing(self):
        self.assertEqual(_box_images({}), [])

    def test_one_selection_uses_only_its_folder(self):
        selected = _box_images({"Gift Box Alliance": True})
        self.assertTrue(selected)
        self.assertTrue(all("/Alliance/" in path for path in selected))

    def test_all_boxes_expands_all_six_csharp_folders(self):
        selected = _box_images({"All Gift Box": True})
        self.assertTrue(any("/Alliance/" in path for path in selected))
        self.assertTrue(any("/Boss/" in path for path in selected))
        self.assertTrue(any("/BoxResource/" in path for path in selected))
        self.assertTrue(any("/Gems/" in path for path in selected))
        self.assertTrue(any("/Gold/" in path for path in selected))
        self.assertTrue(any("/etc/" in path for path in selected))

    def test_selected_images_follow_csharp_numeric_file_order(self):
        selected = _box_images({"Gift Box Alliance": True, "Gift Box Boss": True})
        numbers = [int(path.rsplit("/", 1)[-1].removesuffix(".png")) for path in selected]
        self.assertEqual(numbers, sorted(numbers))
        self.assertEqual(len(selected), len(set(selected)))


if __name__ == "__main__":
    unittest.main()
