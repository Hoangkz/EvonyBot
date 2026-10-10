"""Kiểm tra catalog boss được dựng đúng thành các nút trên tab Join Boss."""

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication

from ui.tabs.join_monster_war_tab import JoinMonsterWarTab


class BossSelectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_boss_with_one_level_has_only_a_level_box_active_by_default(self):
        tab = JoinMonsterWarTab()
        self.addCleanup(tab.deleteLater)

        category, name, enabled, levels = next(
            choice for choice in tab.boss_choices if choice[1] == "Aglaope"
        )

        self.assertEqual(category, "mythical_and_elite_bosses")
        self.assertIsNone(enabled)                  # chỉ có ô cấp, không có ô Join riêng
        self.assertEqual(list(levels), [1])
        self.assertTrue(levels[1].isChecked())

        saved = next(
            boss for boss in tab.get_settings()["selected_bosses"] if boss["name"] == "Aglaope"
        )
        self.assertEqual(saved, {"category_key": "mythical_and_elite_bosses",
                                 "name": "Aglaope", "levels": [1]})

    def test_saved_settings_can_untick_the_level(self):
        tab = JoinMonsterWarTab()
        self.addCleanup(tab.deleteLater)

        tab.set_settings({"selected_bosses": []})

        levels = next(choice[3] for choice in tab.boss_choices if choice[1] == "Aglaope")
        self.assertFalse(levels[1].isChecked())


if __name__ == "__main__":
    unittest.main()
