import unittest

import cv2

from bot.activities.join_monster_war.boss_names import catalog, level, parse, selection, wanted
from bot.activities.join_monster_war.run import (NAME_DH, NAME_DX, NAME_DY, NAME_W, POWER_DH,
                                                 POWER_DX, POWER_DY, POWER_W)
from bot.ocr import read_boss_name, read_power
from tests.join_monster_war.test_flow import SCREENS

# (ảnh, y góc trên nút Join, tên boss, tier, lực trên thẻ); thẻ trên và thẻ dưới lệch nửa pixel.
CARDS = [("02_war_list_join.png", 331, "Peryton", None, 6_500_000),
         ("war_pan_ranged.png", 331, "Pan", None, 122_900_000),   # "Pan (Ranged Troop)"
         ("war_list_join_red.png", 331, "Manticore", None, 2_200_000),
         ("war_list_attacking_join.png", 562, "Yasha", None, 3_400_000),
         ("war_list_two_join.png", 331, "Minotaur", None, 9_900_000),
         ("war_list_two_join.png", 562, "Minotaur", None, 9_900_000),
         ("war_list_more_below.png", 331, "Minotaur", None, 9_900_000),
         ("war_list_more_below.png", 562, "Minotaur", None, 9_900_000),
         # Tên dài nhất: "Junior Knight Bayard" (tier đứng trước, không có "(Boss)").
         ("war_list_long_name.png", 331, "Knight Bayard", "junior", 65_500_000),
         # Game đảo thứ tự từ ở tier Senior: "Senior Bayar Knight".
         ("war_senior_junior_bayard.png", 331, "Knight Bayard", "senior", 147_500_000),
         ("war_senior_junior_bayard.png", 562, "Knight Bayard", "junior", 65_500_000),
         ("war_joined_and_join.png", 562, "Knight Bayard", "junior", 65_500_000),
         # Danh sách đã cuộn: thẻ ở y = 596/597; Golem không có tier -> cấp từ lực.
         ("war_scrolled_golem.png", 596, "Golem", None, 12_400_000),
         ("war_scrolled_golem_2.png", 596, "Golem", None, 12_400_000),
         ("war_scrolled_join_cut_top.png", 597, "Golem", None, 12_400_000),
         # Hai thẻ đã "Joined" (vị trí nút như Join): tier Epic + lực đơn vị B; tên dài
         # xuống 2 dòng "(Boss) Skeleton" / "Dragon" + lực đơn vị K.
         ("war_epic_cerberus_skeleton.png", 331, "Cerberus", "epic", 1_500_000_000),
         ("war_epic_cerberus_skeleton.png", 562, "Skeleton Dragon", None, 787_200)]
X = 319   # x góc trên nút Join trên mọi ảnh


def boss(name):
    return catalog()["bosses"][name.lower()]


class CardOcrTests(unittest.TestCase):
    def _cards(self):
        for screen, y, name, tier, power in CARDS:
            image = cv2.imread(str(SCREENS / screen))
            if image is None:
                self.skipTest(f"thiếu ảnh {screen}")
            yield screen, y, name, tier, power, image

    def test_reads_name_on_every_card(self):
        for screen, y, name, tier, _, image in self._cards():
            crop = image[y + NAME_DY:y + NAME_DY + NAME_DH, X + NAME_DX:X + NAME_DX + NAME_W]
            with self.subTest(screen=screen, y=y):
                found, found_tier = parse(read_boss_name(crop))
                self.assertEqual((found and found.name, found_tier), (name, tier))

    def test_reads_power_on_every_card(self):
        # Lực đọc được khớp "power" của boss thường trong boss.json.
        for screen, y, _, _, power, image in self._cards():
            crop = image[y + POWER_DY:y + POWER_DY + POWER_DH, X + POWER_DX:X + POWER_DX + POWER_W]
            with self.subTest(screen=screen, y=y):
                self.assertEqual(read_power(crop), power)


class BossLevelTests(unittest.TestCase):
    def test_parse_name(self):
        self.assertEqual(parse("(boss) peryton"), (boss("Peryton"), None))
        self.assertEqual(parse("(boss) m?n?aur"), (boss("Minotaur"), None))   # chữ chưa có mẫu
        self.assertEqual(parse("(boss) knight bayard"), (boss("Knight Bayard"), None))
        self.assertEqual(parse("(boss) ?????"), (None, None))
        # Pan có 3 loại, tên không có "(Boss)" mà có loại quân trong ngoặc ở cuối.
        self.assertEqual(parse("pan (panged ?roop)"), (boss("Pan"), None))
        self.assertEqual(parse("pan (ground troop)"), (boss("Pan"), None))
        self.assertEqual(parse("pan (mounted tr"), (boss("Pan"), None))   # ngoặc bị cắt
        self.assertEqual(parse(None), (None, None))

    def test_tier_gives_level_of_that_boss(self):
        no_power = lambda: self.fail("có tier thì không đọc lực")
        hydra, tier = parse("(boss) junior hydra")
        self.assertEqual((hydra.name, tier), ("Hydra", "junior"))
        self.assertEqual(level(hydra, tier, no_power), (1, None))
        # "Senior" là cấp 2 ở Knight Bayard nhưng cấp 3 ở Cerberus.
        self.assertEqual(level(*parse("(boss) senior knight bayard"), no_power), (2, None))
        self.assertEqual(level(*parse("(boss) senior cerberus"), no_power), (3, None))
        self.assertEqual(level(*parse("(boss) myth?cal hydra"), no_power), (6, None))

    def test_power_gives_level_without_tier(self):
        ymir, tier = parse("(boss) ymir")
        self.assertIsNone(tier)
        self.assertEqual(level(ymir, tier, lambda: 120_200_000), (3, 120_200_000))
        self.assertEqual(level(ymir, tier, lambda: 125_000_000), (3, 125_000_000))  # lệch ít
        self.assertEqual(level(ymir, tier, lambda: 9_000_000_000), (None, 9_000_000_000))
        self.assertEqual(level(ymir, tier, lambda: None), (None, None))  # không đọc được lực

    def test_standard_boss_has_no_level(self):
        self.assertEqual(level(boss("Peryton"), None, lambda: self.fail("không cần lực")),
                         (None, None))

    def test_wanted(self):
        selected = selection({"selected_bosses": [
            {"category_key": "standard_bosses", "name": "Peryton", "levels": []},
            {"category_key": "special_and_recurring_event_bosses", "name": "Ymir", "levels": [2, 3]},
            {"category_key": "mythical_and_elite_bosses", "name": "Aglaope", "levels": [1]},
        ]})
        self.assertTrue(wanted(selected, boss("Peryton"), None))
        self.assertFalse(wanted(selected, boss("Yasha"), None))      # không tích
        self.assertFalse(wanted(selected, None, None))               # không nhận ra tên
        self.assertTrue(wanted(selected, boss("Ymir"), 3))
        self.assertFalse(wanted(selected, boss("Ymir"), 1))          # cấp không tích
        self.assertFalse(wanted(selected, boss("Ymir"), None))       # không xác định được cấp
        self.assertTrue(wanted(selection({}), boss("Yasha"), None))  # cấu hình cũ không có selected_bosses

    def test_boss_without_tier_and_power_is_checked_by_name(self):
        aglaope = boss("Aglaope")
        self.assertFalse(aglaope.has_level_data)
        self.assertEqual(level(aglaope, None, lambda: self.fail("không cần lực")), (None, None))
        selected = selection({"selected_bosses": [
            {"category_key": "mythical_and_elite_bosses", "name": "Aglaope", "levels": [1]}]})
        self.assertTrue(wanted(selected, aglaope, None))
        self.assertFalse(wanted(selection({"selected_bosses": []}), aglaope, None))  # không tích

    def test_nian_standard_and_event(self):
        # Nian có ở cả Boss Standard (không cấp) và Boss Event (có tier).
        nian = boss("Nian")
        only_event = selection({"selected_bosses": [
            {"category_key": "special_and_recurring_event_bosses", "name": "Nian", "levels": [3]}]})
        self.assertTrue(wanted(only_event, nian, 3))
        self.assertFalse(wanted(only_event, nian, None))   # Nian thường không được tích
        both = selection({"selected_bosses": [
            {"category_key": "standard_bosses", "name": "Nian", "levels": []},
            {"category_key": "special_and_recurring_event_bosses", "name": "Nian", "levels": [3]}]})
        self.assertTrue(wanted(both, nian, None))          # Nian thường (không tier)
        self.assertFalse(wanted(both, nian, 1))            # Nian event cấp 1 không tích


if __name__ == "__main__":
    unittest.main()
