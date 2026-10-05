"""Flow tests for the C# ``OpenAllGiftBox`` port.

The state order mirrors C#: open Functions -> Items -> selected box -> Open
or Use -> Max -> Use2 -> keep scanning until a CheckOpen end marker appears.
The C# ``checkUsed`` distinction is covered explicitly: ``Open`` waits for and
closes the success popup, while ``Use`` returns directly to the list.

The project does not yet have ADB captures of the Items/box popups, so these
flows use the flow-test harness's documented template variants on a real
396x704 base screenshot.  Replace them with captures under ``screens/`` when
that UI is available; no production template is mocked.
"""
import unittest
from pathlib import Path

import cv2

from bot.activities.open_gift_box.run import run
from bot.context import TEMPLATE_DIR
from tests.flow import Step, back, end, run_flow, swipe, tap


SCREENS = Path(__file__).parents[1] / "event" / "kings_path" / "screens"


def _screen(*templates: tuple[str, tuple[int, int]]):
    """Put the original C# templates on a 396x704 fixture for state-machine QA."""
    def variant(screen):
        screen[:] = 0
        for name, (x, y) in templates:
            image = cv2.imread(str(TEMPLATE_DIR / name))
            h, w = image.shape[:2]
            screen[y:y + h, x:x + w] = image
        return screen
    return variant


class OpenGiftBoxFlowTests(unittest.TestCase):
    def test_opens_selected_box_uses_max_and_stops_at_end(self):
        common = "OpenBox/Setup/Common.png"
        box = "OpenBox/Alliance/58.png"
        flow = [
            Step("alliance_main.png?menu", tap("OpenBox/Setup/chucnang.png")),
            Step("alliance_main.png?items", tap("OpenBox/Setup/Items.png")),
            Step("alliance_main.png?list", tap(box)),
            Step("alliance_main.png?open", tap("OpenBox/Setup/Open.png")),
            Step("alliance_main.png?max", tap("OpenBox/Setup/Max.png"),
                 tap("OpenBox/Setup/Use2.png")),
            Step("alliance_main.png?success", *back()),
            Step("alliance_main.png?end", end()),
        ]
        variants = {
            "menu": _screen(("OpenBox/Setup/chucnang.png", (330, 620))),
            "items": _screen(("OpenBox/Setup/Items.png", (120, 300))),
            "list": _screen((common, (20, 100)), (box, (80, 250))),
            "open": _screen(("OpenBox/Setup/Open.png", (140, 500))),
            "max": _screen(("OpenBox/Setup/Max.png", (80, 350)),
                           ("OpenBox/Setup/Use2.png", (220, 350))),
            "success": _screen(("OpenBox/Setup/success.png", (120, 250))),
            "end": _screen((common, (20, 100)), ("OpenBox/CheckOpen/1.png", (60, 500))),
        }
        settings = {"selection_gift_box": {"Gift Box Alliance": True}}

        run_flow(self, run, SCREENS, flow, settings, variants=variants)

    def test_use_path_skips_success_popup_like_csharp_check_used(self):
        common = "OpenBox/Setup/Common.png"
        box = "OpenBox/Alliance/58.png"
        flow = [
            Step("alliance_main.png?list", tap(box)),
            Step("alliance_main.png?use", tap("OpenBox/Setup/Use.png")),
            Step("alliance_main.png?max", tap("OpenBox/Setup/Max.png"),
                 tap("OpenBox/Setup/Use2.png")),
            Step("alliance_main.png?end", end()),
        ]
        variants = {
            "list": _screen((common, (20, 100)), (box, (80, 250))),
            "use": _screen(("OpenBox/Setup/Use.png", (140, 500))),
            "max": _screen(("OpenBox/Setup/Max.png", (80, 350)),
                           ("OpenBox/Setup/Use2.png", (220, 350))),
            "end": _screen((common, (20, 100)), ("OpenBox/CheckOpen/1.png", (60, 500))),
        }
        settings = {"selection_gift_box": {"Gift Box Alliance": True}}

        device = run_flow(self, run, SCREENS, flow, settings, variants=variants)
        self.assertFalse(any(event[0] == "back" for _, event in device.events))

    def test_box_below_bottom_bar_scrolls_instead_of_tapping(self):
        common = "OpenBox/Setup/Common.png"
        box = "OpenBox/Alliance/58.png"
        flow = [
            Step("alliance_main.png?hidden", swipe(50, 50, 50, 36)),
            Step("alliance_main.png?end", end()),
        ]
        variants = {
            "hidden": _screen((common, (20, 100)), (box, (80, 660))),
            "end": _screen((common, (20, 100)), ("OpenBox/CheckOpen/1.png", (60, 500))),
        }
        settings = {"selection_gift_box": {"Gift Box Alliance": True}}

        run_flow(self, run, SCREENS, flow, settings, variants=variants)

if __name__ == "__main__":
    unittest.main()
