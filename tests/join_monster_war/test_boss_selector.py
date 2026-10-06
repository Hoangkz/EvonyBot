"""Kiểm tra catalog boss được dựng đúng thành các nút trên tab Join Boss."""

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication

from ui.tabs.join_monster_war_tab import BOSS_CATALOG_VERSION, JoinMonsterWarTab


class BossSelectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_elite_temple_guard_has_its_own_join_button_active_by_default(self):
        tab = JoinMonsterWarTab()
        self.addCleanup(tab.deleteLater)

        category, name, enabled, levels = next(
            choice for choice in tab.boss_choices if choice[1] == "Elite Temple Guard"
        )

        self.assertEqual(category, "mythical_and_elite_bosses")
        self.assertEqual(name, "Elite Temple Guard")
        self.assertIsNotNone(enabled)
        self.assertEqual(enabled.text(), "Join")
        self.assertTrue(enabled.isChecked())
        self.assertEqual(levels, {})

        saved = next(
            boss for boss in tab.get_settings()["selected_bosses"]
            if boss["name"] == "Elite Temple Guard"
        )
        self.assertEqual(saved, {
            "category_key": "mythical_and_elite_bosses",
            "name": "Elite Temple Guard",
            "levels": [],
        })
        self.assertEqual(tab.get_settings()["boss_catalog_version"], BOSS_CATALOG_VERSION)

    def test_old_saved_settings_enable_new_default_boss_once(self):
        tab = JoinMonsterWarTab()
        self.addCleanup(tab.deleteLater)

        tab.set_settings({"selected_bosses": [
            {"category_key": "standard_bosses", "name": "Peryton", "levels": []},
        ]})

        elite = next(choice[2] for choice in tab.boss_choices
                     if choice[1] == "Elite Temple Guard")
        self.assertTrue(elite.isChecked())

    def test_current_settings_can_keep_elite_temple_guard_disabled(self):
        tab = JoinMonsterWarTab()
        self.addCleanup(tab.deleteLater)

        tab.set_settings({
            "boss_catalog_version": BOSS_CATALOG_VERSION,
            "selected_bosses": [],
        })

        elite = next(choice[2] for choice in tab.boss_choices
                     if choice[1] == "Elite Temple Guard")
        self.assertFalse(elite.isChecked())


if __name__ == "__main__":
    unittest.main()
