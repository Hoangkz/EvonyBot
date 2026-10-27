"""Các lối vào thay thế của Super Value Return và lần bấm đã chọn."""
import unittest
from pathlib import Path
from unittest import mock

import cv2

from bot.activities.gift_claims.common import skipped_for_run
from bot.activities.gift_claims.screens import GiftScreen
from bot.activities.gift_claims.super_value_return import launcher, zone

ROOT = Path(__file__).parents[2]
SCREENS = Path(__file__).parent / "screens"
LOGIN_TOP_SCREEN = ROOT / "tests/event/gather_troops/cultivate_generals/screens/01_main_login_gift.png"
ARROW_UP_SCREEN = SCREENS / "super_value_return_arrow_up.png"
ARROW_DOWN_SCREEN = SCREENS / "super_value_return_arrow_down.png"
HALL_SCREEN = SCREENS / "super_value_return_hall_of_historic_generals.png"

# Vùng xoá đen để bỏ một trường hợp ưu tiên cao hơn: (x0, y0, x1, y1) px.
LOGIN_TOP = (325, 120, 396, 200)        # TH1: icon Login Gifts góc trên phải
SHOPPING_ICON = (0, 525, 70, 585)       # TH2: icon Shopping Spree dưới mũi tên
ARROW_UP = (10, 500, 60, 530)           # TH3: mũi tên lên


def screen(path, *blank):
    image = cv2.imread(str(path))
    for x0, y0, x1, y1 in blank:
        image[y0:y1, x0:x1] = 0
    return image


class FakeBot:
    def __init__(self, *screens):
        self.screens = list(screens)
        self.taps = []
        self.log = []

    def screenshot(self):
        return self.screens.pop(0) if len(self.screens) > 1 else self.screens[0]

    def _template(self, name):
        image = cv2.imread(str(ROOT / "Images" / name))
        if image is None:
            raise FileNotFoundError(name)
        return image

    @staticmethod
    def find(template, threshold=0.8, screen=None, center=True, region=None):
        height, width = screen.shape[:2]
        x0, y0, x1, y1 = region or (0, 0, 100, 100)
        left, top = int(width * x0 / 100), int(height * y0 / 100)
        area = screen[top:int(height * y1 / 100), left:int(width * x1 / 100)]
        _, score, _, (x, y) = cv2.minMaxLoc(cv2.matchTemplate(area, template, cv2.TM_CCOEFF_NORMED))
        if score < threshold:
            return None
        return left + x + template.shape[1] // 2, top + y + template.shape[0] // 2

    def tap(self, x, y):
        self.taps.append((x, y))

    def sleep(self, _seconds):
        pass

    def record(self, message):
        self.log.append(message)


class SuperValueLauncherTest(unittest.TestCase):
    def test_th2_loads_every_launcher_image_not_a_fixed_three(self):
        folder = ROOT / "Images" / "GiftClaims" / "SuperValueReturn" / "launcher_icons"
        expected = [f"SuperValueReturn/launcher_icons/{path.stem}"
                    for path in sorted(folder.glob("*.png"))]

        self.assertGreater(len(expected), 3)
        self.assertEqual(expected, launcher._launchers())

    def test_th1_login_gifts_top_right(self):
        bot = FakeBot(screen(LOGIN_TOP_SCREEN))
        self.assertEqual((362, 167), launcher.find_super_value_return(bot))
        self.assertIn("chọn lối vào Login Gifts", bot.log[-1])

    def test_th2_icon_in_bottom_left(self):
        bot = FakeBot(screen(LOGIN_TOP_SCREEN, LOGIN_TOP))
        self.assertEqual((35, 553), launcher.find_super_value_return(bot))
        self.assertIn("chọn lối vào icon", bot.log[-1])

    def test_th2_many_matches_takes_smallest_x(self):
        image = screen(LOGIN_TOP_SCREEN, LOGIN_TOP)
        image[541:562, 150:176] = image[541:562, 20:46]      # thêm một icon Login Gifts nữa ở bên phải
        bot = FakeBot(image)
        self.assertEqual((35, 553), launcher.find_super_value_return(bot))

    def test_th2_shopping_spree_icon(self):
        bot = FakeBot(screen(ARROW_UP_SCREEN))
        self.assertEqual((36, 557), launcher.find_super_value_return(bot))
        self.assertIn("chọn lối vào icon", bot.log[-1])

    def test_th2_hall_of_historic_generals_icon(self):
        bot = FakeBot(screen(HALL_SCREEN))
        self.assertEqual((37, 553), launcher.find_super_value_return(bot))
        self.assertIn("hall_of_historic_generals", bot.log[-1])

    def test_th2_each_launcher_icon_on_its_screen(self):
        # Ảnh màn thành có từng icon ở chỗ nút vào (dưới mũi tên lên); xoá đen góc trên phải để bỏ TH1 (vài màn có Login Gifts ở đó).
        expected = {
            "empire_depot": (34, 557), "lucky_raffle": (34, 557), "login_gifts": (35, 553),
            "city_growth_plan": (34, 557), "refining_weekly_card": (34, 557), "shopping_spree": (36, 557),
            "first_purchase": (34, 557),
        }
        for icon, pos in expected.items():
            with self.subTest(icon=icon):
                bot = FakeBot(screen(SCREENS / f"super_value_return_{icon}.png", LOGIN_TOP))
                self.assertEqual(pos, launcher.find_super_value_return(bot))
                self.assertIn(f"launcher_icons/{icon} ", bot.log[-1])

    def test_th1_wins_over_th2(self):
        bot = FakeBot(screen(SCREENS / "super_value_return_empire_depot.png"))
        self.assertEqual((362, 167), launcher.find_super_value_return(bot))
        self.assertIn("chọn lối vào Login Gifts", bot.log[-1])

    def test_th3_button_below_up_arrow(self):
        bot = FakeBot(screen(ARROW_UP_SCREEN, SHOPPING_ICON))
        self.assertEqual((34, 555), launcher.find_super_value_return(bot))
        self.assertIn("chọn lối vào dưới mũi tên lên", bot.log[-1])
        self.assertEqual([], bot.taps)

    def test_th4_taps_down_arrow_then_uses_up_arrow(self):
        bot = FakeBot(screen(ARROW_DOWN_SCREEN, SHOPPING_ICON), screen(ARROW_UP_SCREEN, SHOPPING_ICON))
        self.assertEqual((34, 555), launcher.find_super_value_return(bot))
        self.assertEqual([(33, 456)], bot.taps)
        self.assertIn("mở lối vào bằng mũi tên xuống", bot.log[-2])
        self.assertIn("chọn lối vào dưới mũi tên lên", bot.log[-1])

    def test_th5_same_row_as_valuable_event(self):
        bot = FakeBot(screen(ARROW_UP_SCREEN, SHOPPING_ICON, ARROW_UP))
        self.assertEqual((40, 560), launcher.find_super_value_return(bot))
        self.assertIn("chọn lối vào cùng hàng Valuable Event", bot.log[-1])

    def test_nothing_found(self):
        bot = FakeBot(screen(ARROW_UP_SCREEN, (0, 0, 396, 704)))
        self.assertIsNone(launcher.find_super_value_return(bot))


class OpenSuperValueReturnTest(unittest.TestCase):
    """Màn sau mỗi lần chụp: "main" (màn thành), "svr" (Super Value Return), "other" (màn khác)."""

    def _open(self, after_tap):
        bot = mock.Mock(spec=["check", "screenshot", "tap", "sleep", "record"])
        frames = iter(["main", "main"] + after_tap)      # 2 lần chụp đầu: kiểm tra đang ở màn thành
        bot.screenshot.side_effect = lambda: next(frames)
        with (mock.patch.object(zone, "on_main", side_effect=lambda _b, s: s == "main"),
              mock.patch.object(zone, "to_city", return_value=False),
              mock.patch.object(zone, "return_home") as home,
              mock.patch.object(zone, "find_super_value_return", return_value=(34, 557)),
              mock.patch.object(zone, "identify",
                                side_effect=lambda _b, s: GiftScreen.SUPER_VALUE_RETURN if s == "svr" else None)):
            opened = zone.open_super_value_return(bot)
        return opened, bot, home

    def test_opens_when_title_shows(self):
        opened, bot, _ = self._open(["main", "main", "svr"])
        self.assertTrue(opened)
        bot.tap.assert_called_once_with(34, 557)
        self.assertEqual(3, bot.sleep.call_count)
        self.assertFalse(skipped_for_run(bot, zone.KEY))

    def test_retry_reuses_one_selected_entrance(self):
        bot = mock.Mock(spec=["check", "screenshot", "tap", "sleep", "record"])
        frames = iter(["main", "main"] + ["main"] * 8 + ["svr"])
        bot.screenshot.side_effect = lambda: next(frames)
        with (mock.patch.object(zone, "on_main", side_effect=lambda _b, s: s == "main"),
              mock.patch.object(zone, "to_city", return_value=False),
              mock.patch.object(zone, "return_home"),
              mock.patch.object(zone, "find_super_value_return",
                                return_value=(34, 557)) as find_entrance,
              mock.patch.object(zone, "identify",
                                side_effect=lambda _b, s: GiftScreen.SUPER_VALUE_RETURN if s == "svr" else None)):
            self.assertTrue(zone.open_super_value_return(bot))

        find_entrance.assert_called_once_with(bot)
        self.assertEqual([mock.call(34, 557), mock.call(34, 557)],
                         bot.tap.call_args_list)

    def test_still_in_city_taps_again_once(self):
        opened, bot, _ = self._open(["main"] * 8 + ["svr"])
        self.assertTrue(opened)
        self.assertEqual(2, bot.tap.call_count)

    def test_still_in_city_after_two_taps_skips_until_start(self):
        opened, bot, _ = self._open(["main"] * 16)
        self.assertFalse(opened)
        self.assertEqual(2, bot.tap.call_count)
        self.assertEqual(2 * 8, bot.sleep.call_count)
        self.assertTrue(skipped_for_run(bot, zone.KEY))

    def test_other_screen_goes_home_and_skips_until_start(self):
        opened, bot, home = self._open(["other"] * 8)
        self.assertFalse(opened)
        bot.tap.assert_called_once_with(34, 557)
        home.assert_called_once_with(bot)
        self.assertTrue(skipped_for_run(bot, zone.KEY))

    def test_real_title_screen_is_super_value_return(self):
        from bot.activities.gift_claims.screens import identify
        self.assertEqual(GiftScreen.SUPER_VALUE_RETURN,
                         identify(FakeBot(), screen(SCREENS / "super_value_return_title.png")))


if __name__ == "__main__":
    unittest.main()
