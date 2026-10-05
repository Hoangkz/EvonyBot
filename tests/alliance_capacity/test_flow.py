"""Screenshot flow parity tests for C# ``ScienceNew`` / Alliance Capacity.

Covered C# branches:
* Alliance -> scroll -> Alliance Science -> hold the top Donate button.
* ``Times=No`` stops before a gem donation.
* a numeric Times value allows exactly that many gem donations.
* ``ALL`` maps to the C# unlimited value ``-1``.

Navigation and donation use real full-screen ADB captures. The isolated gem
button state is a synthetic variant because no stable full-screen capture of
that transient state exists yet.
"""
import unittest
from pathlib import Path

import cv2
import numpy as np

from bot.activities.alliance_capacity.run import _gems_limit, run
from bot.context import TEMPLATE_DIR
from tests.flow import Step, end, run_flow, swipe, tap


SCREENS = Path(__file__).parents[1] / "event" / "kings_path" / "screens"


def _only(template: str):
    """Synthetic terminal state; navigation and donation use real screenshots."""
    def variant(screen):
        screen[:] = 0
        image = cv2.imread(str(TEMPLATE_DIR / template))
        h, w = image.shape[:2]
        screen[100:100 + h, 100:100 + w] = image
        return screen
    return variant


class AllianceCapacityFlowTests(unittest.TestCase):
    def test_csharp_science_new_navigation_and_top_card_donation(self):
        flow = [
            Step("alliance_main.png", tap("JoinBoss/lienminh.png")),
            Step("alliance_screen.png", swipe(50, 87, 50, 54), swipe(50, 87, 50, 54)),
            Step("alliance_scrolled.png", tap("Science/scienceclick.png")),
            Step("alliance_science.png", swipe(80.1, 51.3, 80.1, 51.3, tol=1)),
        ]

        run_flow(self, run, SCREENS, flow, {"times": "No"})

    def test_no_means_no_gem_donation(self):
        flow = [Step("alliance_science.png?gems", end())]
        run_flow(self, run, SCREENS, flow, {"times": "No"},
                 variants={"gems": _only("Science/sciencekc.png")})

    def test_numeric_limit_allows_exactly_two_gem_donations(self):
        flow = [
            Step("alliance_science.png?gems", tap("Science/sciencekc.png")),
            Step("alliance_science.png?gems", tap("Science/sciencekc.png")),
            Step("alliance_science.png?gems", end()),
        ]
        run_flow(self, run, SCREENS, flow, {"times": "2"},
                 variants={"gems": _only("Science/sciencekc.png")})

    def test_gem_limit_conversion_matches_csharp(self):
        self.assertEqual(_gems_limit("No"), 0)
        self.assertEqual(_gems_limit("10"), 10)
        self.assertEqual(_gems_limit("ALL"), -1)


if __name__ == "__main__":
    unittest.main()
