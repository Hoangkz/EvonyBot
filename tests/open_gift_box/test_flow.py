"""Flow tests for the Open Gift Box activity.

Flow: "..." -> Items -> tap the Common tab (list back to the top) -> tap the first wanted box
-> Open / Use button -> quantity popup (Use) -> success popup (Back; only after Open) -> ... ->
"done" image: tap Common and scan again; the second "done" marks the task done for today.

The project does not yet have ADB captures of the Items/box screens, so these flows use the
flow-test harness's documented template variants on a real 396x704 base screenshot.  Replace
them with captures under ``screens/`` when that UI is available; no production template is
mocked.
"""
import unittest
from pathlib import Path

import cv2

from bot.activities.open_gift_box.constants import BOX_FOLDERS, KEY, LIST_SWIPE
from bot.activities.open_gift_box.run import _seen_done, run
from bot.context.screen import ScreenMixin
from bot.common import images_in
from bot.context import TEMPLATE_DIR
from tests.flow import Step, back, end, run_flow, swipe, tap


SCREENS = Path(__file__).parents[1] / "event" / "kings_path" / "screens"
TESTS_DIR = Path(__file__).parents[1]
MAIN = "daily_activities/screens/01_main.png"                # city: "..." button
MORE_MENU = "daily_activities/screens/12_old_more_menu.png"  # "..." menu: Items
# Own captures of the Items list: items_01 (top of the list) .. items_12 (end of the list).
LIST = "open_gift_box/screens/items_{:02d}.png"
SETTINGS = {"selection_gift_box": {"Resource": True}}

COMMON = "Items/CommonTab.png"
COMMON_AT = (28, 150)
BOX = "Items/resource/45.png"
OTHER_BOX = "Items/resource/46.png"
DONE = "Items/done/10.png"
OPEN = "OpenBox/Setup/Open.png"
USE = "OpenBox/Setup/Use.png"
USE_POPUP = "OpenBox/Setup/Use2.png"
SUCCESS = "OpenBox/Setup/success.png"


def _screen(*templates: tuple[str, tuple[int, int]]):
    """Put templates on a black 396x704 fixture for state-machine QA."""
    def variant(screen):
        screen[:] = 0
        for name, (x, y) in templates:
            image = cv2.imread(str(TEMPLATE_DIR / name))
            h, w = image.shape[:2]
            screen[y:y + h, x:x + w] = image
        return screen
    return variant


VARIANTS = {
    "menu": _screen(("OpenBox/Setup/chucnang.png", (330, 620))),
    "items": _screen(("OpenBox/Setup/Items.png", (120, 300))),
    "list": _screen((COMMON, COMMON_AT), (BOX, (80, 250))),
    "list_two": _screen((COMMON, COMMON_AT), (OTHER_BOX, (250, 252)), (BOX, (80, 250))),
    "hidden": _screen((COMMON, COMMON_AT), (BOX, (80, 620))),
    "open": _screen((COMMON, COMMON_AT), (OPEN, (140, 560))),
    "use": _screen((COMMON, COMMON_AT), (USE, (140, 560))),
    "popup": _screen((COMMON, COMMON_AT), (USE_POPUP, (220, 450))),
    "success": _screen((COMMON, COMMON_AT), (SUCCESS, (120, 250))),
    "done": _screen((COMMON, COMMON_AT), (DONE, (60, 400))),
}


def _step(variant: str, *actions) -> Step:
    return Step(f"alliance_main.png?{variant}", *actions)


class OpenGiftBoxFlowTests(unittest.TestCase):
    def test_open_box_then_two_done_scans_mark_the_task_done(self):
        flow = [
            _step("menu", tap("OpenBox/Setup/chucnang.png")),
            _step("items", tap("OpenBox/Setup/Items.png")),
            _step("list", tap(COMMON)),             # first time on the list: back to the top
            _step("list", tap(BOX)),
            _step("open", tap(OPEN)),               # Open button showed up within 1s: no second tap
            _step("popup", tap(USE_POPUP)),
            _step("success", *back()),
            _step("done", tap(COMMON)),             # 1st time at the end: back to the top, scan again
            _step("done", end()),                   # 2nd time at the end: finished
        ]

        device = run_flow(self, run, SCREENS, flow, SETTINGS, variants=VARIANTS)

        self.assertIn(KEY, device.daily_done)

    def test_use_button_has_no_success_popup(self):
        flow = [
            _step("list", tap(COMMON)),
            _step("list", tap(BOX)),
            _step("use", tap(USE)),
            _step("popup", tap(USE_POPUP)),
            _step("done", tap(COMMON)),
            _step("done", end()),
        ]

        device = run_flow(self, run, SCREENS, flow, SETTINGS, variants=VARIANTS)

        self.assertFalse(any(event[0] == "back" for _, event in device.events))
        self.assertIn(KEY, device.daily_done)

    def test_box_is_tapped_again_when_no_button_shows_up(self):
        flow = [
            _step("list", tap(COMMON)),
            _step("list", tap(BOX), tap(BOX)),      # no Open / Use after 1s: tap the box again
            _step("open", tap(OPEN)),
        ]

        run_flow(self, run, SCREENS, flow, SETTINGS, variants=VARIANTS)

    def test_first_box_in_reading_order_is_tapped(self):
        flow = [
            _step("list_two", tap(COMMON)),
            _step("list_two", tap(BOX)),            # same row: the left one first
            _step("open", tap(OPEN)),
        ]

        run_flow(self, run, SCREENS, flow, SETTINGS, variants=VARIANTS)

    def test_box_below_the_scan_area_scrolls_instead_of_tapping(self):
        flow = [
            _step("hidden", tap(COMMON)),
            _step("hidden", swipe(*LIST_SWIPE)),
            _step("done", tap(COMMON)),
            _step("done", end()),
        ]

        device = run_flow(self, run, SCREENS, flow, SETTINGS, variants=VARIANTS)

        self.assertIn(KEY, device.daily_done)

    def test_nothing_selected_does_nothing(self):
        flow = [_step("list", end())]

        device = run_flow(self, run, SCREENS, flow, {"selection_gift_box": {}}, variants=VARIANTS)

        self.assertEqual(device.events, [])


class OpenGiftBoxRealScreensTests(unittest.TestCase):
    """Real captures of the Items list, scrolled from the top (items_01) to the end (items_12)."""

    def test_scrolls_down_until_the_wanted_box_is_in_the_scan_area(self):
        flow = [
            Step(MAIN, tap("OpenBox/Setup/chucnang.png")),
            Step(MORE_MENU, tap("OpenBox/Setup/Items.png")),
            Step(LIST.format(1), tap(COMMON)),
            *[Step(LIST.format(i), swipe(*LIST_SWIPE)) for i in range(1, 10)],
            Step(LIST.format(10), tap("Items/gem/125.png")),    # first Gems box, row 1
        ]

        run_flow(self, run, TESTS_DIR, flow, {"selection_gift_box": {"Gems": True}})

    def test_end_of_list_is_scanned_twice_then_marked_done(self):
        flow = [
            Step(LIST.format(12), tap(COMMON)),     # on the list: back to the top first
            Step(LIST.format(12), tap(COMMON)),     # 1st time at the end: back to the top, scan again
            Step(LIST.format(12), end()),           # 2nd time at the end: finished
        ]

        device = run_flow(self, run, TESTS_DIR, flow, {"selection_gift_box": {"Gems": True}})

        self.assertIn(KEY, device.daily_done)


class _Matcher(ScreenMixin):
    _templates: dict = {}


class DoneImageTests(unittest.TestCase):
    """The quill "done" images also match a scroll item on the first screen: they need the
    hero fragment's puzzle piece beside them."""

    def _seen(self, number: int) -> bool:
        screen = cv2.imread(str(TESTS_DIR / LIST.format(number)))
        return _seen_done(_Matcher(), screen, ["Items/done/fragment_purple.png", "Items/done/fragment_orange.png"])

    def test_quill_without_puzzle_piece_is_not_done(self):
        self.assertFalse(self._seen(1))

    def test_quill_next_to_puzzle_piece_is_done(self):
        self.assertTrue(self._seen(11))
        self.assertTrue(self._seen(12))


class GemImagesTests(unittest.TestCase):
    def test_gem_images_match_all_nine_gem_icons(self):
        """gems.png shows the 9 gem items (10 / 20 / 50 / 100 / 200 / 500 / 1000 / 2000 / 5000)."""
        screen = cv2.imread(str(TESTS_DIR / "open_gift_box/screens/gems.png"))
        matcher = _Matcher()
        hits = [pos for path in images_in(BOX_FOLDERS["Gems"])
                for pos in matcher.find_all(path, threshold=0.8, screen=screen)]
        icons = []      # one entry per icon: hits closer than half an icon are the same icon
        for x, y in hits:
            if all(abs(x - ix) > 30 or abs(y - iy) > 30 for ix, iy in icons):
                icons.append((x, y))

        self.assertEqual(len(icons), 9)


if __name__ == "__main__":
    unittest.main()
