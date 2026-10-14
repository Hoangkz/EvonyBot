"""
test_boss_count.py — OCR số boss chờ ở huy hiệu đỏ của icon listboss (bot/ocr/read_boss_count.py): đọc đúng trên các ảnh màn thành thật.
"""
import unittest
from pathlib import Path

import cv2

from bot.context.templates import TEMPLATE_DIR
from bot.ocr.read_boss_count import crop, run

TESTS = Path(__file__).resolve().parents[1]
LISTBOSS = cv2.imread(str(TEMPLATE_DIR / "JoinBoss/listboss.png"))

# ảnh (dưới tests/) -> số boss thấy bằng mắt
CASES = {
    "join_monster_war/screens/01_home_listboss.png": 1,
    "join_monster_war/screens/new_join_boss_flow/01_home_listboss.png": 4,
    "black_market/screens/city_forge.png": 2,
    "event/city_building/screens/civ1/art_hall/01.png": 3,
    "event/city_building/screens/civ1/forge/01.png": 5,
    "event/city_building/screens/civ1/battlefield/01.png": 4,
    "event/kings_path/screens/heal_menu.png": 3,
    **{f"join_monster_war/screens/boss_count_{n}.png": n for n in range(5, 13)},   # 5..9 một chữ số, 10..12 hai chữ số
}


class BossCountTests(unittest.TestCase):
    def test_reads_the_badge_on_real_screens(self):
        for name, want in CASES.items():
            screen = cv2.imread(str(TESTS / name))
            result = cv2.matchTemplate(screen, LISTBOSS, cv2.TM_CCOEFF_NORMED)
            _, score, _, icon = cv2.minMaxLoc(result)
            self.assertGreater(score, 0.95, name)   # ảnh mẫu bỏ viền vàng nên khớp cả lúc có viền (boss mới)
            self.assertEqual(run(crop(screen, icon)), want, name)


if __name__ == "__main__":
    unittest.main()
