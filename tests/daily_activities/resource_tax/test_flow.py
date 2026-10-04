"""
Flow test Daily Activities / Resource Tax (bot/activities/daily_activities/resource_tax/), phiên bản
giao diện mới: màn chính -> Quests -> tab Activity -> Claim All -> cuộn -> dòng "Tax on resources for
N time(s)" -> Go -> về thành, Chợ ở giữa -> menu Chợ, icon "Tax" -> màn Tax -> thu từng dòng (after_go).

Ảnh trong screens/ là ảnh chụp nguyên màn hình giả lập 396x704 (01..04 chép từ
tests/daily_activities/screens/; 07..11 chép từ tests/event/kings_path/screens/ tax_city, tax_menu,
tax_popup, tax_confirm_gems, tax_congrats_gems — màn Tax dùng chung với King's Path City Tax).
"""
import unittest
from pathlib import Path

from bot.activities.daily_activities import resource_tax
from bot.activities.daily_activities.common import open_task, task_cards, task_titles
from bot.activities.daily_activities.constants import GO_BUTTON, TASK_OPENED
from bot.activities.daily_activities.resource_tax.run import after_go
from bot.activities.event.kings_path.city_tax.constants import OKAY, POPUP_TAX, TAX_MENU
from tests.daily_activities import CLAIM_ALL_ONCE, SCROLL, TO_ACTIVITY, open_task_of
from tests.flow import Step, back, end, run_flow, tap, tap_at, tap_pct

SCREENS = Path(__file__).parent / "screens"
TAX_GO_Y = 568   # Go dưới tiêu đề Tax (y 526) trên 04_activity_scrolled — dòng thứ 2, không phải Go của Offer
ROW_X = 309      # nút Tax của 4 dòng (Food / Wood / Stone / Iron) trên 05_tax_screen
ROW_Y = {"Food": 284, "Wood": 383, "Stone": 482, "Iron": 581}
TO_GO = [
    *TO_ACTIVITY, *CLAIM_ALL_ONCE,
    Step("03_activity_top.png", SCROLL),
    Step("04_activity_scrolled.png", tap(GO_BUTTON)),
]
# Sau Go: thành không khớp ảnh mẫu Chợ -> bấm giữa -> menu Chợ -> icon Tax -> màn Tax.
TO_TAX = [
    Step("07_after_go_city.png", tap_pct(50, 50)),
    Step("08_market_menu.png", tap(TAX_MENU)),
]


def _open_and_after_go(bot, _settings):
    """open_task (bấm Go) rồi phần sau Go của Resource Tax."""
    if open_task(bot, task_titles(resource_tax.TASK), task_cards(resource_tax.TASK)) != TASK_OPENED:
        return False
    return after_go(bot)


def _tax_settings(**counts):
    """Cấu hình group "City Tax" của tab Daily Activities (mặc định mọi loại 0, không loại nào Free)."""
    data = {"Food": 0, "Wood": 0, "Stone": 0, "Iron": 0, "free": None}
    data.update(counts)
    return {"Daily Activities": {"Tax on resource": data}}


class ResourceTaxFlow(unittest.TestCase):
    def test_open_task(self):
        flow = [*TO_GO, Step("01_main.png", end(result=TASK_OPENED))]
        device = run_flow(self, open_task_of(resource_tax.TASK), SCREENS, flow, {})
        go = [e for _, e in device.events if e[0] == "tap"][-1]
        self.assertEqual(go[2], TAX_GO_Y)

    def test_after_go_taxes_free_then_count(self):
        """Stone tích Free (+0): popup giữ số free mặc định (11) -> Tax -> hộp xác nhận kim cương ->
        Okay -> băng Taxing Gift -> bấm cho mất. Food 7: popup ô số đọc 7 = đúng số chọn -> Tax.
        Wood / Iron 0: bỏ qua. Xong -> Back về thành, đánh dấu xong hôm nay."""
        flow = [
            *TO_GO, *TO_TAX,
            Step("05_tax_screen.png", tap_at(ROW_X, ROW_Y["Stone"])),
            Step("09_tax_popup_free_11.png", tap(POPUP_TAX)),
            Step("10_tax_confirm_gems.png", tap(OKAY)),
            Step("11_tax_congrats_gems.png", tap_pct(50, 95)),
            Step("05_tax_screen.png", tap_at(ROW_X, ROW_Y["Food"])),
            Step("06_tax_popup_7.png", tap(POPUP_TAX)),
            Step("05_tax_screen.png", back()),
            Step("01_main.png", end(result=True)),
        ]
        device = run_flow(self, _open_and_after_go, SCREENS, flow, {},
                          ctx_settings=_tax_settings(Food=7, free="Stone"))
        self.assertIn("Resource Tax", device.daily_done)

    def test_after_go_nothing_selected(self):
        """Không chọn loại nào (mọi loại 0, không Free): tới màn Tax rồi Back, không bấm dòng nào;
        vẫn đánh dấu xong hôm nay."""
        flow = [
            *TO_GO, *TO_TAX,
            Step("05_tax_screen.png", back()),
            Step("01_main.png", end(result=True)),
        ]
        device = run_flow(self, _open_and_after_go, SCREENS, flow, {}, ctx_settings=_tax_settings())
        self.assertIn("Resource Tax", device.daily_done)


if __name__ == "__main__":
    unittest.main()
