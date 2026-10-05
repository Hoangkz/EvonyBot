"""OCR and safety-state tests for the standalone Black Market activity.

Parity with C# ``Market.BlackMarket``:
* ``CheckGoldBlackMarket`` stops a refresh below 2,000,000 gold.
* unreadable gold is retried twice, then the check is skipped for that refresh.

Python additionally OCRs the gem wallet before a paid refresh.  OCR is anchored
to the two wallet icons so the top resource bar and item-price icons cannot be
read as the player's wallet.
"""
import unittest
from pathlib import Path
from unittest import mock

import cv2
import numpy as np

import bot.activities.black_market.market as market_module
from bot.activities.black_market.market import Market
from bot.ocr import MarketBalance, read_market_balance


SCREENS = Path(__file__).parents[1] / "event" / "kings_path" / "screens"


class MarketBalanceOcrTests(unittest.TestCase):
    def test_reads_gold_and_gems_from_real_market_screens(self):
        # Every real Black Market state currently captured must produce the
        # exact visible wallet, including buy/refresh confirmation overlays.
        # The later screens prove gem OCR follows the real paid-refresh
        # sequence instead of returning one hard-coded value.
        expected_gems = {
            "bm_screen.png": 105_947,
            "bm_screen_2.png": 105_947,
            "bm_screen_3.png": 105_947,
            "bm_screen_4.png": 105_847,
            "bm_screen_5.png": 105_797,
            "bm_screen_6.png": 105_747,
            "bm_screen_7.png": 105_697,
            "bm_refresh_gems.png": 105_947,
            "bm_bought.png": 105_947,
            "bm_confirm.png": 105_947,
        }
        for name, gems in expected_gems.items():
            with self.subTest(name=name, gems=gems):
                screen = cv2.imread(str(SCREENS / name))
                self.assertEqual(read_market_balance(screen), MarketBalance(2_199_030, gems))

    def test_non_market_screens_do_not_read_top_resource_counters(self):
        # Both screens contain the normal city resource bar.  Without wallet
        # icon anchoring a fixed crop can accidentally turn those values into
        # Black Market gold/gems.
        for name in ("bm_city.png", "bm_menu.png"):
            with self.subTest(name=name):
                screen = cv2.imread(str(SCREENS / name))
                self.assertEqual(read_market_balance(screen), MarketBalance(None, None))

    def test_wallet_can_shift_a_few_pixels_without_breaking_ocr(self):
        screen = cv2.imread(str(SCREENS / "bm_screen.png"))
        shifted = cv2.warpAffine(
            screen,
            np.float32([[1, 0, 7], [0, 1, 4]]),
            (screen.shape[1], screen.shape[0]),
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(0, 0, 0),
        )
        self.assertEqual(read_market_balance(shifted), MarketBalance(2_199_030, 105_947))

    def test_each_wallet_field_can_fail_independently(self):
        screen = cv2.imread(str(SCREENS / "bm_screen.png"))
        no_gold = screen.copy()
        no_gold[214:238, 95:225] = 0
        self.assertEqual(read_market_balance(no_gold), MarketBalance(None, 105_947))

        no_gems = screen.copy()
        no_gems[214:238, 262:382] = 0
        self.assertEqual(read_market_balance(no_gems), MarketBalance(2_199_030, None))

    def test_blank_screen_returns_none_per_field(self):
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        self.assertEqual(read_market_balance(screen), MarketBalance(None, None))


class MarketStateTests(unittest.TestCase):
    def test_purchase_confirmation_counts_once(self):
        bot = mock.Mock()
        market = Market(bot, {})
        market.pending = "buy"

        market.on_confirm(np.zeros((1, 1, 3), dtype=np.uint8), (190, 415))

        self.assertEqual(market.bought, 1)
        self.assertIsNone(market.pending)
        bot.tap.assert_called_once_with(190, 415)

    def test_refresh_confirmation_is_not_counted_as_purchase(self):
        bot = mock.Mock()
        market = Market(bot, {})
        market.pending = "refresh"

        market.on_confirm(np.zeros((1, 1, 3), dtype=np.uint8), (190, 415))

        self.assertEqual(market.bought, 0)
        self.assertIsNone(market.pending)
        bot.back.assert_called_once()

    def test_check_gold_stops_below_csharp_two_million_limit(self):
        bot = mock.Mock()
        market = Market(bot, {})
        with mock.patch.object(
            market_module, "read_market_balance", return_value=MarketBalance(1_999_999, 10)
        ):
            self.assertTrue(market._gold_too_low(np.zeros((1, 1, 3), dtype=np.uint8)))

    def test_unreadable_gold_retries_twice_then_matches_csharp_skip(self):
        bot = mock.Mock()
        market = Market(bot, {})
        with mock.patch.object(
            market_module, "read_market_balance", return_value=MarketBalance(None, 10)
        ):
            self.assertIsNone(market._gold_too_low(np.zeros((1, 1, 3), dtype=np.uint8)))
            self.assertIsNone(market._gold_too_low(np.zeros((1, 1, 3), dtype=np.uint8)))
            self.assertFalse(market._gold_too_low(np.zeros((1, 1, 3), dtype=np.uint8)))
        self.assertEqual(market.balance_misses, 0)


if __name__ == "__main__":
    unittest.main()
