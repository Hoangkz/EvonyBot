"""
Flow test activity Black Market (bot/activities/black_market/run.py): mở màn Black Market (từ màn thành: Chợ ở giữa ->
menu "Black Market"), quét 6 ô, mua món được tích (Resource / Chips không mua bằng kim cương), Instant Refresh, dừng
theo Quantity Buy / Refresh / số dư.

Ảnh dùng chung, không chép (ảnh chụp nguyên màn hình giả lập 396x704): bm_* ở tests/event/kings_path/screens/.
- bm_screen: ô 1 gói 50k gỗ (giá 40.000 lương thực), ô 4 Chips 100 x2 (giá 150.000 quặng), còn lại EXP / boost.
- bm_screen_3: ô 2 gói 100k quặng (giá 80.000 gỗ); ô 5, 6 gói 500k giá kim cương.
Mở Chợ từ màn thành (black_market/city_map.py), ảnh chụp 21943 trong screens/ của thư mục này:
- city_forge: Lò rèn ở giữa (197, 345); city_market: Chợ ở giữa (197, 337); city_market_edge: Chợ lệch (251, 317);
  market_menu: menu Chợ (icon "Black Market" (165, 226)).
"""
import sys
import unittest
from unittest import mock

import bot.activities  # noqa: F401 (nạp package activity)
from bot.activities.event.kings_path.black_market.constants import CONFIRM, INSTANT_REFRESH, MENU_BLACK_MARKET, SLOTS
from tests.daily_activities import KP, TESTS_DIR
from tests.flow import Step, back, end, run_flow, swipe, tap, tap_at, tap_pct

BM = "black_market/screens/"
# Bản đồ thành 21943 (toạ độ quét thật, black_market/city_map.py scan).
CITY_MAP = {"keep": [0, 0], "forge": [-412, -268], "market": [285, -715]}

SCREENS = TESTS_DIR
# Package black_market có hàm `run` trùng tên module -> lấy module qua sys.modules.
RUN = sys.modules["bot.activities.black_market.run"]
CM = sys.modules["bot.activities.black_market.city_map"]


def _settings(**kw):
    """Cấu hình tab mặc định (Resource + Chips 100) + `kw`."""
    return {"check_gold": False, "refresh": "ALL", "quantity_buy": "ALL", "resources": True,
            "items": {"chips_100": True}, **kw}


def _sold_out(bgr):
    """Mọi nút giá xám (đã mua hết) — tô đen 6 nút giá."""
    for x, y in SLOTS:
        bgr[y - 10:y + 10, x - 44:x + 44] = 40
    return bgr


VARIANTS = {"sold_out": _sold_out}


def _buy(screen, slot):
    """Bấm ô `slot` -> hộp "Are you sure ...?" -> Confirm."""
    return [Step(f"{KP}{screen}", tap_at(*SLOTS[slot])), Step(f"{KP}bm_confirm.png", tap(CONFIRM))]


def _run(testcase, flow, settings, **kw):
    return run_flow(testcase, RUN.run, SCREENS, flow, settings, variants=VARIANTS, **kw)


class BlackMarketFlow(unittest.TestCase):
    def test_buy_resource_and_chips(self):
        """Đang ở màn Black Market: mua ô 1 (gói 50k gỗ) rồi ô 4 (Chips 100) -> đủ Quantity Buy 2 -> Back."""
        flow = [
            *_buy("bm_screen.png", 0),
            *_buy("bm_screen.png", 3),
            Step(f"{KP}bm_screen.png", back()),
            Step(f"{KP}bm_city.png", end()),
        ]
        device = _run(self, flow, _settings(quantity_buy="2"))
        self.assertIn("Black Market: buy resource (slot 1)", device.logs)
        self.assertIn("Black Market: buy chips_100 (slot 4)", device.logs)
        self.assertIn("Black Market: Quantity Buy reached (2), stop", device.logs)

    def test_open_from_city(self):
        """Từ màn thành (nút "•••"): Chợ ở giữa -> menu "Black Market" -> mua 1 -> Back."""
        flow = [
            Step(f"{KP}bm_city.png", tap_pct(50, 50)),
            Step(f"{KP}bm_menu.png", tap(MENU_BLACK_MARKET)),
            *_buy("bm_screen.png", 0),
            Step(f"{KP}bm_screen.png", back()),
            Step(f"{KP}bm_city.png", end()),
        ]
        _run(self, flow, _settings(quantity_buy="1"))

    def test_gem_priced_resource_skipped(self):
        """Resource không mua bằng kim cương: bm_screen_3 chỉ mua ô 2 (gói 100k quặng giá gỗ), bỏ ô 5, 6 (500k giá
        kim cương) -> hết ô, Refresh "0" -> Back."""
        flow = [
            *_buy("bm_screen_3.png", 1),
            Step(f"{KP}bm_screen_3.png", back()),
            Step(f"{KP}bm_city.png", end()),
        ]
        device = _run(self, flow, _settings(refresh="0", items={}))
        self.assertIn("Black Market: Refresh limit reached (0), bought 1, stop", device.logs)

    def test_refresh_then_buy(self):
        """Mua hết bộ hàng (nút giá xám) -> Instant Refresh -> bộ mới -> mua ô 1 -> đủ Quantity Buy 1."""
        flow = [
            Step(f"{KP}bm_screen.png?sold_out", tap(INSTANT_REFRESH)),
            *_buy("bm_screen.png", 0),
            Step(f"{KP}bm_screen.png", back()),
            Step(f"{KP}bm_city.png", end()),
        ]
        device = _run(self, flow, _settings(quantity_buy="1"))
        self.assertIn("Black Market: Instant Refresh 1", device.logs)

    def test_refresh_limit(self):
        """Hết ô để mua và đã đủ số lần Refresh (2) -> Back, không refresh thêm."""
        flow = [
            Step(f"{KP}bm_screen.png?sold_out", tap(INSTANT_REFRESH)),
            Step(f"{KP}bm_screen_2.png", tap(INSTANT_REFRESH)),
            Step(f"{KP}bm_screen_6.png", back()),
            Step(f"{KP}bm_city.png", end()),
        ]
        device = _run(self, flow, _settings(refresh="2"))
        self.assertIn("Black Market: Refresh limit reached (2), bought 0, stop", device.logs)

    def test_low_gems_stops(self):
        """Kim cương < 50 -> Back ngay, không mua (luôn kiểm tra, kể cả không tích CheckGold)."""
        flow = [Step(f"{KP}bm_screen.png", back()), Step(f"{KP}bm_city.png", end())]
        with mock.patch.object(RUN, "read_gems", return_value=49):
            device = _run(self, flow, _settings())
        self.assertIn("Black Market: gems 49 < 50, bought 0, stop", device.logs)

    def test_check_gold(self):
        """Vàng < 2.000.000: tích CheckGold -> dừng; không tích -> vẫn mua."""
        stop = [Step(f"{KP}bm_screen.png", back()), Step(f"{KP}bm_city.png", end())]
        with mock.patch.object(RUN, "read_gold", return_value=1_999_999):
            device = _run(self, stop, _settings(check_gold=True))
            self.assertIn("Black Market: gold 1,999,999 < 2,000,000, bought 0, stop", device.logs)
            buy = [*_buy("bm_screen.png", 0), Step(f"{KP}bm_screen.png", back()), Step(f"{KP}bm_city.png", end())]
            _run(self, buy, _settings(quantity_buy="1"))

    def test_nothing_selected(self):
        """Không tích món nào -> không làm gì."""
        flow = [Step(f"{KP}bm_screen.png", end())]
        device = _run(self, flow, _settings(resources=False, items={}))
        self.assertIn("Black Market: no item selected", device.logs)


class OpenMarketFlow(unittest.TestCase):
    """Mở Black Market từ màn thành (_market): Chợ trên màn / bản đồ thành của máy."""

    @staticmethod
    def _swipe_pct(finger):
        """Cú vuốt city_map.swipe (đối xứng quanh SWIPE_CENTER) theo % màn 396x704."""
        cx, cy = CM.SWIPE_CENTER
        fx, fy = finger
        x1, y1, x2, y2 = int(cx - fx / 2), int(cy - fy / 2), int(cx + fx / 2), int(cy + fy / 2)
        return swipe(x1 * 100 / 396, y1 * 100 / 704, x2 * 100 / 396, y2 * 100 / 704, tol=1)

    def _to_black_market(self):
        """Chợ ở giữa -> bấm -> menu -> icon "Black Market" -> màn Black Market (Quantity Buy 0: dừng ngay)."""
        return [
            Step(f"{BM}city_market.png", tap_at(197, 337)),
            Step(f"{BM}market_menu.png", tap(MENU_BLACK_MARKET)),
            Step(f"{KP}bm_screen.png", back()),
            Step(f"{BM}city_market.png", end()),
        ]

    def test_goto_market_with_city_map(self):
        """Đang thấy Lò rèn (có trong bản đồ của máy) -> vuốt thẳng (697, -447) chia 3 cú (232, -149) -> Chợ ở giữa."""
        moves = CM.split((CITY_MAP["market"][0] - CITY_MAP["forge"][0], CITY_MAP["market"][1] - CITY_MAP["forge"][1]))
        self.assertEqual(moves, [(232, -149)] * 3)
        flow = [Step(f"{BM}city_forge.png", self._swipe_pct(m)) for m in moves] + self._to_black_market()
        device = _run(self, flow, _settings(quantity_buy="0"), setup=lambda ctx: setattr(ctx, "city_map", dict(CITY_MAP)))
        self.assertIn("Black Market: go to market from forge: 3 swipe(s) [(232, -149)]", device.logs)

    def test_market_on_screen_centred(self):
        """Chợ có trên màn nhưng lệch (251, 317) -> kéo bù một cú (-54, 28) vào giữa -> bấm (không cần bản đồ)."""
        flow = [Step(f"{BM}city_market_edge.png", self._swipe_pct((-54, 28)))] + self._to_black_market()
        _run(self, flow, _settings(quantity_buy="0"))


if __name__ == "__main__":
    unittest.main()
