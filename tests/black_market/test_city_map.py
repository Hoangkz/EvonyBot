"""
Unit test black_market/city_map.py bằng thành giả: các công trình ở toạ độ bản đồ cố định, camera dịch đúng bằng cú vuốt;
locate trả vị trí công trình trên màn theo camera. Kiểm: chia cú thẳng hàng (split), quét thành ghi đúng toạ độ (scan),
đi tới công trình từ một công trình đã biết (goto), toạ độ ô trong city_tour.json.
"""
import unittest
from unittest import mock

import sys

import bot.activities  # noqa: F401

city_map = sys.modules["bot.activities.black_market.city_map"]

W, H = 396, 704


class FakeCity:
    """Thành giả: công trình b ở toạ độ bản đồ WORLD[b]; camera (toạ độ bản đồ của giữa màn) = `cam`. Công trình hiện
    trên màn tại CENTER + cam - V_b nếu trong khung màn."""

    def __init__(self, world, cam=(0, 0)):
        self.world = dict(world)
        self.cam = list(cam)
        self.swipes = []

    def pos(self, building):
        if building not in self.world:
            return None
        vx, vy = self.world[building]
        x, y = city_map.CENTER[0] + self.cam[0] - vx, city_map.CENTER[1] + self.cam[1] - vy
        return (x, y) if 0 <= x < W and 0 <= y < H else None

    def locate(self, bot, screen, building):
        pos = self.pos(building)
        return (0.95, pos) if pos is not None else (0.0, None)

    def swipe(self, x1, y1, x2, y2, duration=0, delay=0):
        self.swipes.append((x2 - x1, y2 - y1))
        self.cam[0] += x2 - x1
        self.cam[1] += y2 - y1


class CityMapTest(unittest.TestCase):
    def _patch(self, city):
        bot = mock.Mock()
        bot.swipe.side_effect = city.swipe
        patches = [mock.patch.object(city_map, "locate", city.locate),
                   mock.patch.object(city_map, "city_screen", lambda b: None)]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        return bot

    def test_split_straight_line(self):
        moves = city_map.split((712, -478))
        self.assertTrue(all(m == moves[0] for m in moves))              # thẳng hàng
        self.assertTrue(all(abs(dx) <= city_map.MAX_SWIPE[0] and abs(dy) <= city_map.MAX_SWIPE[1] for dx, dy in moves))
        self.assertLessEqual(abs(sum(m[0] for m in moves) - 712), len(moves))
        self.assertEqual(city_map.split((0, 0)), [])

    def test_goto_from_known_building(self):
        """Đang thấy Lò rèn (đã có trong bản đồ, không ở giữa) -> vuốt thẳng tới Chợ, Chợ vào giữa màn."""
        world = {"forge": (-404, -238), "market": (297, -689), "keep": (0, 0)}
        city = FakeCity(world, cam=(-404 + 40, -238 - 30))
        bot = self._patch(city)
        pos = city_map.goto(bot, "BM", "market", world)
        self.assertIsNotNone(pos)
        self.assertLessEqual(abs(pos[0] - city_map.CENTER[0]), city_map.TOLERANCE)
        self.assertLessEqual(abs(pos[1] - city_map.CENTER[1]), city_map.TOLERANCE)
        straight = [s for s in city.swipes]
        self.assertGreaterEqual(len(straight), 1)

    def test_goto_without_known_building_on_screen(self):
        world = {"forge": (-404, -238), "market": (297, -689)}
        city = FakeCity(world, cam=(5000, 5000))
        bot = self._patch(city)
        self.assertIsNone(city_map.goto(bot, "BM", "market", world))
        self.assertEqual(city.swipes, [])

    def test_scan_records_every_plot(self):
        """Thành giả có công trình đúng ở toạ độ các ô của city_tour.json: quét từ Thành chính ghi đủ, đúng toạ độ."""
        names = ["academy", "defense_force", "barracks", "archer_camp", "workshop", "stables", "hospital", "market",
                 "war_hall", "embassy", "warehouse", "prison", "forge"]
        world = {"keep": (0, 0)}
        for name, plot in zip(names, city_map.TOUR):
            world[name] = tuple(plot["view"])
        city = FakeCity(world)
        bot = self._patch(city)
        with mock.patch.object(city_map, "BUILDINGS", tuple(world)):
            found = city_map.scan(bot, "BM")
        self.assertEqual(set(found), set(world))
        for name, view in world.items():
            self.assertLessEqual(abs(found[name][0] - view[0]) + abs(found[name][1] - view[1]), 4, name)

    def test_tour_swipes_safe(self):
        """Mỗi cú trong city_tour.json có điểm đầu / cuối trong màn 396x704."""
        for plot in city_map.TOUR:
            for start, end in plot["swipes"]:
                for x, y in (start, end):
                    self.assertTrue(0 <= x < W and 0 <= y < H, plot["plot"])


if __name__ == "__main__":
    unittest.main()
