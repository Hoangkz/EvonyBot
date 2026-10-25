"""find_super_value_return: TH1 -> TH5 trên ảnh màn thành thật (396x704)."""
import unittest
from pathlib import Path

import cv2

from bot.activities.gift_claims.super_value_return import launcher

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
    def test_th1_login_gifts_top_right(self):
        bot = FakeBot(screen(LOGIN_TOP_SCREEN))
        self.assertEqual((362, 167), launcher.find_super_value_return(bot))
        self.assertIn("TH1", bot.log[-1])

    def test_th2_icon_in_bottom_left(self):
        bot = FakeBot(screen(LOGIN_TOP_SCREEN, LOGIN_TOP))
        self.assertEqual((35, 553), launcher.find_super_value_return(bot))
        self.assertIn("TH2", bot.log[-1])

    def test_th2_many_matches_takes_smallest_x(self):
        image = screen(LOGIN_TOP_SCREEN, LOGIN_TOP)
        image[541:562, 150:176] = image[541:562, 20:46]      # thêm một icon Login Gifts nữa ở bên phải
        bot = FakeBot(image)
        self.assertEqual((35, 553), launcher.find_super_value_return(bot))

    def test_th2_shopping_spree_icon(self):
        bot = FakeBot(screen(ARROW_UP_SCREEN))
        self.assertEqual((36, 557), launcher.find_super_value_return(bot))
        self.assertIn("TH2", bot.log[-1])

    def test_th2_hall_of_historic_generals_icon(self):
        bot = FakeBot(screen(HALL_SCREEN))
        self.assertEqual((37, 553), launcher.find_super_value_return(bot))
        self.assertIn("hall_of_historic_generals", bot.log[-1])

    def test_th3_button_below_up_arrow(self):
        bot = FakeBot(screen(ARROW_UP_SCREEN, SHOPPING_ICON))
        self.assertEqual((34, 555), launcher.find_super_value_return(bot))
        self.assertIn("TH3", bot.log[-1])
        self.assertEqual([], bot.taps)

    def test_th4_taps_down_arrow_then_uses_up_arrow(self):
        bot = FakeBot(screen(ARROW_DOWN_SCREEN, SHOPPING_ICON), screen(ARROW_UP_SCREEN, SHOPPING_ICON))
        self.assertEqual((34, 555), launcher.find_super_value_return(bot))
        self.assertEqual([(33, 456)], bot.taps)
        self.assertIn("TH4", bot.log[-2])
        self.assertIn("TH3", bot.log[-1])

    def test_th5_same_row_as_valuable_event(self):
        bot = FakeBot(screen(ARROW_UP_SCREEN, SHOPPING_ICON, ARROW_UP))
        self.assertEqual((40, 560), launcher.find_super_value_return(bot))
        self.assertIn("TH5", bot.log[-1])

    def test_nothing_found(self):
        bot = FakeBot(screen(ARROW_UP_SCREEN, (0, 0, 396, 704)))
        self.assertIsNone(launcher.find_super_value_return(bot))


if __name__ == "__main__":
    unittest.main()
