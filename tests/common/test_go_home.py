"""go_home: ở bản đồ thế giới thì bấm nút toà thành thay vì Back."""
import unittest
from pathlib import Path
from unittest import mock

import cv2

from bot.common import go_home
from bot.common.go_home import RADIAL_CLOSE_TAPS, TO_CITY, TO_CITY_REGION, TO_CITY_WAIT
from bot.context.templates import TEMPLATE_DIR

SCREENS = Path(__file__).parent / "screens"


class _RealBot:
    """Bot giả khớp ảnh mẫu thật trên ảnh chụp: ghi lại tap / Back."""
    def __init__(self):
        self.taps, self.backs = [], 0

    def find(self, path, threshold=0.9, screen=None, region=None):
        template = cv2.imread(str(TEMPLATE_DIR / path))
        if template is None:
            return None
        _, score, _, loc = cv2.minMaxLoc(cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED))
        return (loc[0] + template.shape[1] // 2, loc[1] + template.shape[0] // 2) if score >= threshold else None

    def tap(self, x, y, delay=0):
        self.taps.append((x, y))

    def tap_percent(self, x, y, delay=0, count=1):
        self.taps.append(("pct", x, y))

    def back(self, delay=0):
        self.backs += 1

    log = record = lambda self, message: None


class GoHomeTests(unittest.TestCase):
    def bot(self, world: bool):
        bot = mock.Mock()
        bot.find.side_effect = lambda path, **kw: (360, 670) if world and path == TO_CITY else None
        return bot

    @mock.patch("bot.common.go_home.current_focus", return_value="com.topgamesinc.evony")
    def test_world_map_taps_city_button_not_back(self, _focus):
        bot = self.bot(world=True)
        go_home(bot, "screen")
        bot.tap.assert_called_once_with(360, 670, delay=TO_CITY_WAIT)
        bot.back.assert_not_called()
        self.assertIn(mock.call(TO_CITY, screen="screen", region=TO_CITY_REGION), bot.find.call_args_list)

    @mock.patch("bot.common.go_home.current_focus", return_value="com.topgamesinc.evony")
    def test_other_screen_still_presses_back(self, _focus):
        bot = self.bot(world=False)
        go_home(bot, "screen")
        bot.back.assert_called_once()
        bot.tap.assert_not_called()

    @mock.patch("bot.common.go_home.current_focus", return_value="com.topgamesinc.evony")
    def test_building_menu_open_taps_empty_ground_not_back(self, _focus):
        """Menu tròn của Barracks: Back chỉ mở hộp thoát game, nên bấm đất trống."""
        bot = _RealBot()
        go_home(bot, cv2.imread(str(SCREENS / "city_building_menu.png")))
        self.assertEqual((bot.taps, bot.backs), ([("pct", *RADIAL_CLOSE_TAPS[0])], 0))

    @mock.patch("bot.common.go_home.current_focus", return_value="com.topgamesinc.evony")
    def test_exit_dialog_taps_cancel_not_back(self, _focus):
        """Hộp "exit the game?": bấm Cancel (Back sẽ tắt rồi mở lại hộp, lặp mãi)."""
        bot = _RealBot()
        go_home(bot, cv2.imread(str(SCREENS / "city_exit_dialog.png")))
        self.assertEqual(bot.backs, 0)
        self.assertEqual(len(bot.taps), 1)
        x, y = bot.taps[0]
        self.assertTrue(80 <= x <= 190 and 395 <= y <= 435)   # nút Cancel


if __name__ == "__main__":
    unittest.main()
