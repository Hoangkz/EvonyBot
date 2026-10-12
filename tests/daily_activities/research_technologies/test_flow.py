"""
Test Daily Activities / Research technologies (bot/activities/daily_activities/research_technologies/):
nhận nhãn "Lv N / M" xanh trên màn Academy và nút Research xanh / xám ở màn Technology.

Ảnh trong screens/ là ảnh chụp nguyên màn giả lập 396x704 (2026-10-13): 07 màn Academy tab Advancement,
08 màn Technology (Research xanh), 13 màn Technology thiếu điều kiện (Research xám), 10 popup Researching,
11 màn Research Speedup, 12 popup Finish All.
"""
import unittest
from pathlib import Path

import cv2
from bot.activities.daily_activities.research_technologies.run import green_levels

SCREENS = Path(__file__).parent / "screens"


def _shot(name):
    return cv2.imread(str(SCREENS / name))


class ResearchTechnologies(unittest.TestCase):
    def test_green_levels_on_academy(self):
        """4 nhãn xanh (Graziery, Felling Axe, Scythe, Bucksaw); Lv1/1 trắng của Builder không tính."""
        self.assertEqual(green_levels(_shot("07_academy.png")), [(73, 429), (321, 429), (73, 583), (321, 583)])

    def test_no_green_level_on_technology_popup(self):
        self.assertEqual(green_levels(_shot("13_technology_locked.png")), [])

    def test_no_green_level_at_bottom_of_tree(self):
        """Cuối cây tab Advancement: chỉ nhãn trắng Lv0 / 20 (chưa mở khoá) -> không chọn, cuộn / sang tab khác."""
        self.assertEqual(green_levels(_shot("22_academy_bottom_locked.png")), [])

    def test_maxed_levels_are_not_green(self):
        """Lv10 / 10, Lv1 / 1 (chữ vàng) bỏ qua; còn Felling Axe, Scythe, Bucksaw (xanh)."""
        self.assertEqual(green_levels(_shot("21_academy_some_maxed.png")), [(321, 429), (73, 583), (321, 583)])


if __name__ == "__main__":
    unittest.main()
