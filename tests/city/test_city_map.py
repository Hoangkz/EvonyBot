"""
Unit test bot/city/city_map.py bằng thành giả: các công trình ở toạ độ bản đồ cố định, camera dịch đúng bằng cú vuốt;
locate trả vị trí công trình trên màn theo camera. Kiểm: chia cú thẳng hàng (split), quét thành ghi đúng toạ độ (scan),
đi tới công trình từ một công trình đã biết (goto), toạ độ ô trong bot/city/civ1/city_tour.py.
"""
import unittest
from unittest import mock

import numpy as np

import sys

import bot.city.city_map  # noqa: F401
from bot.city import tours

city_map = sys.modules["bot.city.city_map"]   # package city có module city_map; lấy qua sys.modules cho đồng bộ với các test khác

civ1 = tours.civ1      # bảng route civ1 (bot/city/civ1/city_tour.py)
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
        bot.swipe_watch = None
        bot.swipe_count = 0
        bot.civilization = 1      # route data hiện chỉ có civ1
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
        """Thành giả có công trình đúng ở toạ độ các ô của bot/city/civ1/city_tour.py: quét từ Thành chính ghi đủ, đúng toạ độ."""
        names = ["academy", "trap_factory", "barracks", "archer_camp", "workshop", "stables", "hospital", "market",
                 "war_hall", "embassy", "tavern", "prison", "forge"]
        world = {"keep": (0, 0)}
        for name, plot in zip(names, civ1.DATA):
            world[name] = tuple(plot["view"])
        city = FakeCity(world)
        bot = self._patch(city)
        with mock.patch.object(city_map, "BUILDINGS", tuple(world)):
            found = city_map.scan(bot, "BM", civ1)
        self.assertEqual(set(found), set(world) | set(civ1.FIXED))
        for name, view in civ1.FIXED.items():
            if name not in names:    # công trình cố định không có ô riêng: toạ độ có sẵn; tavern thì là một ô, lấy toạ độ quét
                self.assertEqual(found[name], view)
        for name, view in world.items():
            self.assertLessEqual(abs(found[name][0] - view[0]) + abs(found[name][1] - view[1]), 4, name)

    def test_scan_city_from_a_fixed_building_saves_the_map(self):
        """Rảnh, chưa có bản đồ: camera đứng ở Tường thành (không thấy Thành chính) -> về Thành chính, quét 13 ô, lưu bản đồ."""
        names = ["academy", "trap_factory", "barracks", "archer_camp", "workshop", "stables", "hospital", "market",
                 "war_hall", "embassy", "tavern", "prison", "forge"]
        world = {"keep": (0, 0), **{b: tuple(v) for b, v in civ1.FIXED.items()}}
        for name, plot in zip(names, civ1.DATA):
            world[name] = tuple(plot["view"])
        city = FakeCity(world, cam=tuple(civ1.FIXED["walls"]))
        bot = self._patch(city)
        bot.find.return_value = (1, 1)           # đang ở màn thành (nút •••)
        bot.city_map = {}
        with mock.patch.object(city_map, "BUILDINGS", tuple(world)):
            self.assertTrue(city_map.scan_city(bot, "BM"))
        bot.set_city_map.assert_called_once()
        saved = bot.set_city_map.call_args[0][0]
        self.assertEqual(set(saved), set(world))
        self.assertIsNone(bot.swipe_watch)

    def test_find_keep_sweeps_when_no_anchor_on_screen(self):
        """Không thấy Thành chính / Tường thành / Research Factory trên màn: dò (vuốt xoắn ốc) tới khi thấy rồi kéo Thành chính vào giữa."""
        world = {"keep": (0, 0), **{b: tuple(v) for b, v in civ1.FIXED.items()}}
        city = FakeCity(world, cam=(-520, 0))     # Thành chính lệch ra ngoài mép trái màn
        bot = self._patch(city)
        self.assertIs(city_map.find_keep(bot, "BM"), civ1)
        self.assertLessEqual(abs(city.cam[0]), city_map.TOLERANCE)
        self.assertLessEqual(abs(city.cam[1]), city_map.TOLERANCE)

    def test_find_keep_from_a_fixed_building_uses_the_fixed_route(self):
        """Thấy Tavern / Research Factory / Walls trên màn: vuốt đúng đường cố định (ROUTES) về Thành chính, không dò."""
        for anchor in civ1.FIXED:
            world = {"keep": (0, 0), **{b: tuple(v) for b, v in civ1.FIXED.items()}}
            city = FakeCity(world, cam=tuple(civ1.FIXED[anchor]))
            bot = self._patch(city)
            self.assertTrue(city_map.find_keep(bot, "BM"), anchor)
            self.assertLessEqual(abs(city.cam[0]), city_map.TOLERANCE, anchor)
            self.assertLessEqual(abs(city.cam[1]), city_map.TOLERANCE, anchor)
            self.assertEqual(sum(1 for s in city.swipes if s in civ1.ROUTES[(anchor, "keep")]),
                             len(civ1.ROUTES[(anchor, "keep")]), anchor)

    def test_routes_match_fixed_positions(self):
        """Tổng cú vuốt của mỗi đường cố định khớp hiệu toạ độ hai công trình (lệch tối đa 20 px mỗi trục)."""
        pos = {"keep": (0, 0), **{b: tuple(v) for b, v in civ1.FIXED.items()}}
        for (src, dst), moves in civ1.ROUTES.items():
            total = (sum(m[0] for m in moves), sum(m[1] for m in moves))
            shift = lambda b: civ1.ANCHOR_SHIFT.get(b, (0, 0))
            want = (pos[dst][0] - pos[src][0] + shift(dst)[0] - shift(src)[0],
                    pos[dst][1] - pos[src][1] + shift(dst)[1] - shift(src)[1])
            self.assertLessEqual(abs(total[0] - want[0]), 20, (src, dst))
            self.assertLessEqual(abs(total[1] - want[1]), 20, (src, dst))

    def test_find_keep_from_anywhere_in_the_city(self):
        """Mọi chỗ đứng trong thành (lưới 200 px): vòng xoáy thấy một mốc và đưa Thành chính vào giữa màn."""
        world = {"keep": (0, 0), **{b: tuple(v) for b, v in civ1.FIXED.items()}}
        for x in range(-450, 1251, 200):
            for y in range(-900, 251, 200):
                city = FakeCity(world, cam=(x, y))
                bot = self._patch(city)
                self.assertTrue(city_map.find_keep(bot, "BM"), (x, y))
                self.assertLessEqual(abs(city.cam[0]), city_map.TOLERANCE, (x, y))
                self.assertLessEqual(abs(city.cam[1]), city_map.TOLERANCE, (x, y))
                self.addCleanup(lambda: None)

    def test_find_keep_gives_up_after_the_whole_search(self):
        world = {"keep": (0, 0)}
        city = FakeCity(world, cam=(-5000, 5000))
        bot = self._patch(city)
        self.assertIsNone(city_map.find_keep(bot, "BM"))
        self.assertEqual(len(city.swipes), len(city_map.spiral_swipes()))

    def test_scan_city_checks_bosses_every_three_swipes(self):
        """scan_city gọi watch lúc bắt đầu rồi cứ BOSS_CHECK_EVERY cú vuốt một lần (cả lúc tìm Thành chính lẫn lúc quét ô)."""
        names = ["academy", "trap_factory", "barracks", "archer_camp", "workshop", "stables", "hospital", "market",
                 "war_hall", "embassy", "tavern", "prison", "forge"]
        world = {"keep": (0, 0), **{b: tuple(v) for b, v in civ1.FIXED.items()}}
        for name, plot in zip(names, civ1.DATA):
            world[name] = tuple(plot["view"])
        city = FakeCity(world, cam=tuple(civ1.FIXED["walls"]))
        bot = self._patch(city)
        bot.find.return_value = (1, 1)
        bot.city_map = {}
        calls = []
        with mock.patch.object(city_map, "BUILDINGS", tuple(world)):
            city_map.scan_city(bot, "BM", watch=lambda b: calls.append(len(city.swipes)))
        self.assertEqual(calls[0], 0)                                                      # số boss ban đầu
        self.assertEqual(calls[1:], list(range(3, len(city.swipes) + 1, 3)))              # mỗi 3 cú vuốt
        self.assertIsNone(bot.swipe_watch)

    def test_ensure_city_taps_the_city_button_on_the_world_map(self):
        bot = mock.Mock()
        bot.find.side_effect = [(360, 670), None]      # lần 1 thấy nút toà thành (bản đồ thế giới), lần 2 hết
        city_map.ensure_city(bot, "BM")
        bot.tap.assert_called_once_with(360, 670, delay=city_map.TO_CITY_WAIT)
        bot = mock.Mock()
        bot.find.return_value = None                   # đã ở thành: không bấm gì
        city_map.ensure_city(bot, "BM")
        bot.tap.assert_not_called()

    def test_swipe_retries_from_another_start_when_the_screen_does_not_move(self):
        """Cú vuốt trúng icon (game coi là bấm) làm màn hình không đổi -> vuốt lại bằng điểm đầu khác tới khi màn hình đổi."""
        still = np.zeros((704, 396, 3), np.uint8)
        moved = still.copy()
        moved[200:400] = 200
        bot = mock.Mock()
        bot.swipe_watch = None
        bot.screenshot.side_effect = [still, still, moved]          # sau cú 1, 2: không đổi; sau cú 3: đổi
        with mock.patch.object(city_map, "city_screen", lambda b: still):
            city_map.swipe_from_to(bot, (100, 300), (250, 300))
        starts = [call.args[:2] for call in bot.swipe.call_args_list]
        self.assertEqual(len(starts), 3)
        self.assertEqual(starts[0], (100, 300))
        self.assertEqual(starts[1], (100, 190))                    # RETRY_SHIFTS[1]
        self.assertEqual(len(set(starts)), 3)

    def test_find_keep_skips_a_civilization_without_route_data(self):
        """Thấy công trình của civ 4 (chưa đo đủ route) -> không vuốt theo bảng civ1, trả None."""
        world = {"keep": (0, 0), **{b: tuple(v) for b, v in civ1.FIXED.items()}}
        city = FakeCity(world, cam=tuple(civ1.FIXED["walls"]))
        bot = self._patch(city)
        bot.civilization = 4
        self.assertIsNone(city_map.find_keep(bot, "BM"))
        self.assertEqual(city.swipes, [])
        bot.record.assert_called()

    def test_tour_swipes_safe(self):
        """Mỗi cú trong city_tour.py của mọi civ có điểm đầu / cuối trong màn 396x704."""
        for civ, tour in tours.ALL.items():
            for plot in tour.DATA:
                for start, end in plot["swipes"]:
                    for x, y in (start, end):
                        self.assertTrue(0 <= x < W and 0 <= y < H, (civ, plot["plot"]))

    def test_only_complete_civs_are_enabled(self):
        self.assertEqual(set(tours.TOURS), {1, 2, 3, 5, 7})      # civ4 đang đo dở (COMPLETE = False)


if __name__ == "__main__":
    unittest.main()
