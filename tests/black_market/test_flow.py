"""Screenshot flows for the standalone Black Market activity.

The screens are full 396x704 ADB captures.  Together these flows cover the
C# state-machine order (open -> scan -> buy -> confirm -> refresh) and the
Python safety checks added around gold/gem OCR.
"""
import unittest
from pathlib import Path
from unittest import mock

import bot.activities.black_market.market as market_module
from bot.activities.black_market.constants import (
    GEM_ICONS,
    GEM_ICON_THRESHOLD,
    GOLD_ICONS,
    GOLD_ICON_THRESHOLD,
)
from bot.activities.black_market.market import Market, _currency_slots
from bot.ocr import MarketBalance
from tests.flow import Step, back, end, run_flow, tap, tap_at


SCREENS = Path(__file__).parents[1] / "event" / "kings_path" / "screens"


class BlackMarketFlowTests(unittest.TestCase):
    def test_real_screen_classifies_gold_and_gem_price_slots_only(self):
        """Wallet/refresh icons must not be mistaken for one of the six prices."""
        found = {}

        def classify(bot, _):
            screen = bot.screenshot()
            found["gems"] = _currency_slots(bot, screen, GEM_ICONS, GEM_ICON_THRESHOLD)
            found["gold"] = _currency_slots(bot, screen, GOLD_ICONS, GOLD_ICON_THRESHOLD)

        run_flow(self, classify, SCREENS, [Step("bm_refresh_gems.png", end())], {})

        self.assertEqual(found["gems"], [(80, 365), (200, 365), (80, 522), (200, 522)])
        self.assertEqual(found["gold"], [(320, 365)])

    def test_scans_buys_confirms_and_honors_quantity_limit(self):
        holder = []

        def buy(bot, data):
            market = Market(bot, data)
            holder.append(market)
            market.run()

        flow = [
            Step("bm_screen.png", tap_at(80, 365)),
            Step("bm_confirm.png", tap("Black Market/xacnhan.png")),
            Step("bm_bought.png", end()),
        ]
        settings = {
            "black_market_items": {"Resources": True},
            "refresh": "ALL",
            "quantity_buy": "1",
        }

        run_flow(self, buy, SCREENS, flow, settings)

        self.assertEqual(holder[0].bought, 1)
        self.assertIsNone(holder[0].pending)

    def test_new_currency_icons_skip_gold_and_gems_for_resource_only_mode(self):
        holder = []

        def scan(bot, data):
            market = Market(bot, data)
            holder.append(market)
            market._scan(bot.screenshot())

        settings = {
            "black_market_items": {"Resources": True},
            "refresh": "ALL",
            "quantity_buy": "ALL",
        }
        run_flow(self, scan, SCREENS, [Step("bm_refresh_gems.png", end())], settings)

        # This screen has two resource items priced in gems and one priced in
        # gold.  Resource-only mode must buy none of them.
        self.assertEqual(holder[0].points, [])

    def test_zero_gems_skips_gem_slots_even_when_gem_buying_is_enabled(self):
        """A definitive OCR zero must never open a purchase that cannot succeed."""
        holder = []

        def scan(bot, data):
            market = Market(bot, data)
            holder.append(market)
            market._scan(bot.screenshot())

        settings = {
            "black_market_items": {"Resources": True, "Resources Gem": True},
            "refresh": "ALL",
            "quantity_buy": "ALL",
        }
        with mock.patch.object(
            market_module, "read_market_balance", return_value=MarketBalance(2_199_030, 0)
        ):
            run_flow(self, scan, SCREENS, [Step("bm_refresh_gems.png", end())], settings)

        self.assertEqual(holder[0].points, [])

    def test_opens_market_reads_wallet_and_stops_at_zero_refresh_limit(self):
        flow = [
            Step("bm_menu.png", tap("Black Market/BlackMarketCheck.png")),
            Step("bm_screen.png", end()),
        ]
        settings = {
            "black_market_items": {},
            "refresh": "0",
            "quantity_buy": "ALL",
        }

        device = run_flow(self, lambda bot, data: Market(bot, data).run(), SCREENS, flow, settings)

        self.assertIn("Black Market: wallet gold=2199030, gems=105947", device.logs)

    def test_paid_refresh_confirms_without_counting_a_purchase(self):
        holder = []

        def refresh(bot, _):
            market = Market(bot, {"refresh": "1", "quantity_buy": "ALL"})
            holder.append(market)
            screen = bot.screenshot()
            pos = bot.find("Black Market/Refresh.png", screen=screen)
            market._refresh(screen, pos)

        flow = [
            Step("bm_refresh_gems.png", tap("Black Market/Refresh.png")),
            Step("bm_confirm.png", tap("Black Market/xacnhan.png")),
            Step("bm_screen_2.png", end()),
        ]

        device = run_flow(self, refresh, SCREENS, flow, {})

        self.assertEqual(holder[0].bought, 0)
        self.assertEqual(holder[0].refreshes, 1)
        self.assertIn("Black Market: confirmed paid refresh (105947 gems available)", device.logs)

    def test_paid_refresh_stops_when_gem_wallet_cannot_be_verified(self):
        """Never confirm a gem charge when OCR cannot prove a positive balance."""
        holder = []

        def refresh(bot, _):
            market = Market(bot, {"refresh": "1", "quantity_buy": "ALL"})
            holder.append(market)
            screen = bot.screenshot()
            pos = bot.find("Black Market/Refresh.png", screen=screen)
            market._refresh(screen, pos)

        flow = [
            Step("bm_refresh_gems.png", tap("Black Market/Refresh.png")),
            Step("bm_confirm.png", *back(), end()),
        ]
        with mock.patch.object(
            market_module, "read_market_balance", return_value=MarketBalance(2_199_030, None)
        ):
            device = run_flow(self, refresh, SCREENS, flow, {})

        self.assertTrue(holder[0].done)
        self.assertEqual(holder[0].bought, 0)
        self.assertIn("cannot verify gems for paid refresh", device.logs[-1])

    def test_check_gold_stops_before_refresh_when_wallet_is_below_limit(self):
        """C# parity: CheckGold ends the activity below 2,000,000 gold."""
        holder = []

        def refresh(bot, _):
            market = Market(bot, {
                "black_market_items": {"CheckGold": True},
                "refresh": "1",
                "quantity_buy": "ALL",
            })
            holder.append(market)
            screen = bot.screenshot()
            pos = bot.find("Black Market/Refresh.png", screen=screen)
            market._refresh(screen, pos)

        with mock.patch.object(
            market_module, "read_market_balance", return_value=MarketBalance(1_999_999, 105_947)
        ):
            device = run_flow(
                self, refresh, SCREENS, [Step("bm_screen.png", end())], {}
            )

        self.assertTrue(holder[0].done)
        self.assertEqual(device.events, [])


if __name__ == "__main__":
    unittest.main()
