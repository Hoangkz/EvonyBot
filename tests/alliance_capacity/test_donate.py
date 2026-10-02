"""
Test Alliance Capacity (bot/activities/alliance_capacity/): ở màn Alliance Science phải bấm giữ
nút Donate của thẻ khoa học TRÊN CÙNG. Ảnh cũ Science/donate.png chỉ khớp 0,84 ở thẻ đầu nên bot
donate nhầm thẻ 2 — nay dùng chung ảnh nút Donate với King's Path (1,00 ở cả hai thẻ).
Ảnh: tests/event/kings_path/screens/alliance_science.png (thẻ 1 Alliance Capacity, thẻ 2
Construction Speed).
"""
import unittest
from pathlib import Path

from bot.activities.alliance_capacity.run import _donate
from tests.flow import Step, end, run_flow, swipe

SCREENS = Path(__file__).parents[1] / "event" / "kings_path" / "screens"


class DonateTopCard(unittest.TestCase):
    def test_holds_top_donate_button(self):
        """Hai thẻ có nút Donate (y 361 và 530): bấm giữ nút thẻ đầu (317, 361) = (80,1 %, 51,3 %)."""
        flow = [Step("alliance_science.png", swipe(80.1, 51.3, 80.1, 51.3, tol=1), end())]
        run_flow(self, lambda bot, _: _donate(bot, bot.screenshot()), SCREENS, flow, {})


if __name__ == "__main__":
    unittest.main()
