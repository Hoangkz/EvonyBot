"""Bộ đọc dòng của màn Refine Equipment (bot/ocr/read_refine_lines.py) trên ảnh thật chụp ở 21913 (396x704) và luật đếm `meets`."""
import unittest
from pathlib import Path

import cv2

import bot.activities  # noqa: F401  (nạp gói activity trước: tránh vòng import)
from bot.activities.refine_equipment.constants import SLOTS
from bot.ocr.read_refine_lines import meets, read_new, read_original, satisfies

SCREENS = Path(__file__).parent / "screens"
CATALOG = {slot_id: catalog for slot_id, _label, _pos, catalog in SLOTS}


def load(name):
    return cv2.imread(str(SCREENS / name))


def row(name, color, kind="percent"):
    return {"name": name, "color": color, "kind": kind}


class ReadLines(unittest.TestCase):
    def test_all_four_locked_colours_ignore_the_gold_padlock(self):
        """Ảnh 17 (giày, cả 4 dòng khoá): ổ khoá đóng màu vàng nằm cạnh chữ, màu dòng vẫn phải là trắng / tím / trắng / tím (trước đây dòng 1 và 3 bị đọc thành vàng)."""
        rows = read_original(load("17_all_locked.png"), CATALOG["boots"])
        self.assertEqual([r["color"] for r in rows], ["normal", "purple", "normal", "purple"])
        self.assertEqual([r["locked"] for r in rows], [True] * 4)
        self.assertEqual([r["name"] for r in rows], ["Ranged Troop Defense", "Ground Troop Defense", "Mounted Troop Defense", "Mounted Troop Load"])
        self.assertEqual([r["kind"] for r in rows], ["flat", "flat", "flat", "percent"])

    def test_unlocked_original_rows(self):
        rows = read_original(load("12_ring_refine.png"), CATALOG["ring"])
        self.assertEqual([r["name"] for r in rows], ["Mounted Troop Load", "Mounted Troop Attack", "Ground Troop Load", "Ground Troop Load"])
        self.assertEqual([r["kind"] for r in rows], ["percent", "flat", "percent", "percent"])
        self.assertEqual([r["locked"] for r in rows], [False] * 4)

    def test_unrefined_equipment_has_no_original_frame(self):
        self.assertIsNone(read_original(load("16_unrefined.png"), CATALOG["armor"]))

    def test_new_frame_has_no_lock_icons(self):
        rows = read_new(load("14_result_match.png"), CATALOG["ring"])
        self.assertEqual([(r["name"], r["color"]) for r in rows][1], ("Siege Machine Load", "orange"))
        self.assertEqual([r["locked"] for r in rows], [None] * 4)

    def test_long_name_in_both_layouts(self):
        """Tên dài xuống 2 dòng: khung chưa cuộn (chữ nhỏ, ảnh 08) và đã cuộn (ảnh 09)."""
        for name in ("08_refine_equipment.png", "09_new_lines.png"):
            rows = read_original(load(name), CATALOG["weapon"])
            self.assertEqual(rows[1]["name"], "Increases Troop Capacity in Subordinate City", name)


class MarchSpeedToMonsters(unittest.TestCase):
    """"March Speed to Monsters" (cam) không được lẫn với "March Speed" (mẫu ngắn khớp phần đầu dòng dài): ảnh thật của giày ở 21913."""

    def test_original_frame_unscrolled_two_line_small_font(self):
        rows = read_original(load("18_boots_original_march_monsters.png"), CATALOG["boots"])
        self.assertEqual([r["name"] for r in rows], ["March Speed", "Siege Machine Defense", "March Speed to Monsters", "Ranged Troop Defense"])
        self.assertEqual(rows[2]["color"], "orange")
        self.assertEqual(rows[2]["kind"], "percent")

    def test_new_frame_one_line(self):
        rows = read_new(load("19_boots_result_march_monsters.png"), CATALOG["boots"])
        self.assertEqual([r["name"] for r in rows], ["March Speed", "Siege Machine Defense", "March Speed to Monsters", "Ranged Troop Defense"])
        self.assertEqual([r["color"] for r in rows], ["normal", "normal", "orange", "normal"])


class IncreasesConstructionSpeed(unittest.TestCase):
    """"Increases Construction Speed in Subordinate City" của giáp (Armor) ở cả hai kiểu màn hình, và tên "... Troop Defense" xuống 2 dòng ở khung chưa cuộn."""

    def test_result_frame(self):
        rows = read_new(load("20_armor_result_construction.png"), CATALOG["armor"])
        self.assertEqual([r["name"] for r in rows], ["Mounted Troop Defense", "Ranged Troop Defense", "Increases Construction Speed in Subordinate City", "Siege Machine Defense"])
        self.assertEqual([r["kind"] for r in rows], ["flat", "percent", "percent", "flat"])

    def test_original_frame_unscrolled_small_font(self):
        """Ảnh 21: khung Original chưa cuộn, "Mounted Troop / Defense" và "Siege Machine / Defense" xuống 2 dòng; "Mounted Troop Defense" từng bị "?" vì dòng 2 "Defense" giống hệt
        "Ranged / Ground Troop Defense" làm điểm trung bình hai dòng sát nhau."""
        rows = read_original(load("21_armor_original_construction.png"), CATALOG["armor"])
        self.assertEqual([r["name"] for r in rows], ["Mounted Troop Defense", "Ranged Troop Defense", "Increases Construction Speed in Subordinate City", "Siege Machine Defense"])

    def test_original_frame_of_the_result_screen(self):
        rows = read_original(load("20_armor_result_construction.png"), CATALOG["armor"])
        self.assertEqual([r["name"] for r in rows], ["Ground Troop Load", "Increases Gold Production Speed in Subordinate City", "Subordinate City Training Speed", "Subordinate City Training Speed"])


class OreGatheringSpeed(unittest.TestCase):
    """"Ore Gathering Speed" của vũ khí (chỉ khác "Food / Lumber / Stone Gathering Speed" ở từ đầu), ảnh thật ở 21913."""

    def test_result_frame(self):
        rows = read_new(load("22_weapon_result_ore.png"), CATALOG["weapon"])
        self.assertEqual([r["name"] for r in rows], ["Mounted Troop Attack", "Ore Gathering Speed", "Ground Troop Attack", "March Speed to Monsters"])
        self.assertEqual([r["color"] for r in rows], ["normal", "normal", "purple", "normal"])
        self.assertEqual([r["kind"] for r in rows], ["flat", "percent", "percent", "percent"])

    def test_original_frame_unscrolled(self):
        rows = read_original(load("23_weapon_original_ore.png"), CATALOG["weapon"])
        self.assertEqual([r["name"] for r in rows], ["Mounted Troop Attack", "Ore Gathering Speed", "Ground Troop Attack", "March Speed to Monsters"])
        self.assertEqual([r["locked"] for r in rows], [False] * 4)

    def test_original_frame_of_the_result_screen(self):
        rows = read_original(load("22_weapon_result_ore.png"), CATALOG["weapon"])
        self.assertEqual([r["name"] for r in rows], ["March Speed", "Ranged Troop Attack", "Mounted Troop Attack", "Ground Troop Attack"])
        self.assertEqual([r["kind"] for r in rows], ["percent", "percent", "flat", "flat"])


class GoldLines(unittest.TestCase):
    """7 ảnh thật của nhẫn (ring) ở 21913 có dòng vàng ở khung New: mọi dòng đều phải nhận ra tên (không None) và dòng vàng phải đọc đúng màu."""

    def test_every_line_is_recognised_and_gold_is_gold(self):
        names = sorted(p.name for p in SCREENS.glob("*_ring_gold_*.png"))
        self.assertEqual(len(names), 7)
        gold = 0
        for name in names:
            for read in (read_original, read_new):
                rows = read(load(name), CATALOG["ring"])
                self.assertTrue(all(r["name"] is not None for r in rows), name)
                gold += sum(r["color"] == "gold" for r in rows)
        self.assertGreaterEqual(gold, 10)


class StopRule(unittest.TestCase):
    def test_only_wanted_attribute_counts(self):
        """3 Orange mà chỉ tích Ground Troop Load: cả 3 dòng phải là Ground Troop Load cam trở lên (2 cam + 1 vàng vẫn đạt)."""
        wanted = {"Ground Troop Load": ("orange", "all")}
        ok = [row("Ground Troop Load", "orange"), row("Ground Troop Load", "orange"), row("Ground Troop Load", "gold"), row("Mounted Troop Load", "gold")]
        bad = [row("Ground Troop Load", "orange"), row("Ground Troop Load", "orange"), row("Mounted Troop Load", "gold"), row("Mounted Troop Load", "gold")]
        self.assertTrue(meets(ok, wanted, 0, 3))
        self.assertFalse(meets(bad, wanted, 0, 3))

    def test_gold_and_orange_mix(self):
        wanted = {"A": ("orange", "all"), "B": ("orange", "all")}
        self.assertTrue(meets([row("A", "gold"), row("B", "orange"), row("C", "normal"), row("C", "normal")], wanted, 1, 1))
        self.assertFalse(meets([row("A", "orange"), row("B", "orange"), row("C", "normal"), row("C", "normal")], wanted, 1, 1))

    def test_minimum_colour_per_attribute(self):
        self.assertFalse(satisfies(row("A", "orange"), {"A": ("gold", "all")}))
        self.assertTrue(satisfies(row("A", "gold"), {"A": ("orange", "all")}))

    def test_percent_or_flat_kind(self):
        self.assertFalse(satisfies(row("A", "gold", "flat"), {"A": ("gold", "percent")}))
        self.assertTrue(satisfies(row("A", "gold", "flat"), {"A": ("gold", "all")}))
        self.assertTrue(satisfies(row("A", "gold", "flat"), {"A": ("gold", "flat")}))

    def test_unreadable_rows_do_not_count(self):
        self.assertFalse(meets([row(None, "gold")] * 4, {"A": ("orange", "all")}, 0, 1))
        self.assertFalse(meets(None, {"A": ("orange", "all")}, 0, 1))


if __name__ == "__main__":
    unittest.main()
