import unittest
from unittest import mock

import cv2
import numpy as np

from bot.activities.daily_activities.alliance_vip import run
from bot.activities.daily_activities.alliance_vip.catalog import (
    ITEMS,
    SETTINGS_KEY,
    normalized,
)


class CatalogTests(unittest.TestCase):
    def test_all_requested_limits(self):
        expected = {
            "tribute": 5, "vip_points": 5,
            "food_100k": 200, "lumber_100k": 200, "stone_100k": 200,
            "ore_100k": 200, "food_500k": 50, "lumber_500k": 50,
            "stone_500k": 50, "ore_500k": 50,
            "chip_100": 5, "chip_1000": 1,
            "truce_agreement_8h": 3, "truce_agreement_24h": 1,
            "truce_agreement_3d": 1,
        }
        self.assertEqual(expected, {item.key: item.maximum for item in ITEMS})

    def test_checked_values_always_mean_buy_max(self):
        values = normalized({"food_100k": True, "tribute": 1,
                             "truce_agreement_8h": False})
        self.assertEqual(200, values["food_100k"])
        self.assertEqual(5, values["tribute"])
        self.assertEqual(0, values["truce_agreement_8h"])

    def test_new_profile_checks_tribute_and_vip_only(self):
        values = normalized(None)
        self.assertEqual(5, values["tribute"])
        self.assertEqual(5, values["vip_points"])
        self.assertTrue(all(value == 0 for key, value in values.items()
                            if key not in {"tribute", "vip_points"}))

    def test_preliminary_quantity_keys_are_migrated(self):
        values = normalized({"vip_points_100": 5, "chips_1k": 1,
                             "truce_24h": 1})
        self.assertEqual(5, values["vip_points"])
        self.assertEqual(1, values["chip_1000"])
        self.assertEqual(1, values["truce_agreement_24h"])


class SaturationTests(unittest.TestCase):
    class Bot:
        def __init__(self):
            self.logs = []

        @staticmethod
        def crop(image, x, y, w, h):
            return image[y:y + h, x:x + w].copy()

        def record(self, message):
            self.logs.append(message)

    def test_popup_buy_button_must_be_saturated(self):
        bot = self.Bot()
        screen = np.full((200, 300, 3), 120, dtype=np.uint8)
        center = (150, 100)
        w, h = run.BUY_BUTTON_BOX
        screen[center[1] - h // 2:center[1] + h // 2,
               center[0] - w // 2:center[0] + w // 2] = (20, 180, 20)
        self.assertTrue(run._buy_button_active(bot, screen, center))

        screen[:] = 120
        self.assertFalse(run._buy_button_active(bot, screen, center))


class TruceColorTests(unittest.TestCase):
    class Bot:
        def __init__(self):
            self.logs = []

        @staticmethod
        def _template(path):
            image = cv2.imread(str(run.TEMPLATE_DIR / path), cv2.IMREAD_COLOR)
            if image is None:
                raise AssertionError(f"Missing fixture: {path}")
            return image

        @staticmethod
        def crop(image, x, y, w, h):
            return image[y:y + h, x:x + w].copy()

        def record(self, message):
            self.logs.append(message)

    def test_each_truce_colour_only_matches_its_own_duration(self):
        bot = self.Bot()
        items = [item for item in ITEMS
                 if item.key.startswith("truce_agreement_")]
        for visible in items:
            image = bot._template(visible.template)
            screen = np.zeros((120, 160, 3), dtype=np.uint8)
            top, left = 40, 50
            screen[top:top + image.shape[0],
                   left:left + image.shape[1]] = image
            center = (left + image.shape[1] // 2,
                      top + image.shape[0] // 2)
            for expected in items:
                self.assertEqual(
                    visible.key == expected.key,
                    run._truce_color_matches(
                        bot, screen, center, expected.template),
                    f"visible={visible.key}, expected={expected.key}",
                )

    def test_truce_reference_colours_have_safe_separation(self):
        bot = self.Bot()
        histograms = {
            item.key: run._hue_histogram(bot._template(item.template))
            for item in run._TRUCE_ITEMS
        }
        for left_index, left in enumerate(run._TRUCE_ITEMS):
            for right in run._TRUCE_ITEMS[left_index + 1:]:
                distance = cv2.compareHist(
                    histograms[left.key], histograms[right.key],
                    cv2.HISTCMP_BHATTACHARYYA)
                self.assertGreater(distance, 0.08)


class DoneTests(unittest.TestCase):
    class Ctx:
        def __init__(self, done=()):
            self.done = set(done)

        def is_daily_done(self, key):
            return key in self.done

    def test_explicit_empty_selection_is_done(self):
        settings = {SETTINGS_KEY: {item.key: 0 for item in ITEMS}}
        self.assertTrue(run._all_selected_items_done(self.Ctx(), settings))
        self.assertTrue(run._catalog_done(self.Ctx(), settings))

    def test_priority_item_only_needs_daily_sale_done(self):
        settings = {SETTINGS_KEY: {"tribute": True}}
        self.assertFalse(run._all_selected_items_done(self.Ctx(), settings))
        self.assertTrue(run._all_selected_items_done(
            self.Ctx({run.TRIBUTE_DAY_KEY}), settings))

    def test_normal_item_requires_its_own_done_key(self):
        settings = {SETTINGS_KEY: {"chip_100": True}}
        self.assertFalse(run._all_selected_items_done(self.Ctx(), settings))
        self.assertTrue(run._all_selected_items_done(
            self.Ctx({run._item_done_key("chip_100")}), settings))

    def test_newly_checked_item_reopens_job_after_vip_bought(self):
        bought_vip = self.Ctx({run.DAY_KEY})
        self.assertTrue(run._catalog_done(
            bought_vip, {SETTINGS_KEY: {"vip_points": True}}))
        self.assertFalse(run._catalog_done(
            bought_vip, {SETTINGS_KEY: {"vip_points": True, "tribute": True}}))


class SingleSessionTests(unittest.TestCase):
    class Ctx:
        def __init__(self):
            self.done = set()
            self.back_calls = 0
            self.swipes = 0
            self.swipe_args = []
            self.taps = []
            self.logs = []
            self.on_shop = True

        def is_daily_done(self, key):
            return key in self.done

        def mark_daily_done(self, key):
            self.done.add(key)

        def record(self, message):
            self.logs.append(message)

        def check(self):
            pass

        @staticmethod
        def screenshot():
            return np.zeros((704, 396, 3), dtype=np.uint8)

        def back(self, delay=0):
            self.back_calls += 1

        def swipe_percent(self, *args, **kwargs):
            self.swipes += 1
            self.swipe_args.append(args)

        def tap_percent(self, *args, **kwargs):
            self.taps.append(args)

        def find(self, template, threshold=None, screen=None):
            # Mặc định đang ở màn Alliance Shop (thấy tiêu đề shop).
            return (199, 23) if template == run.SHOP_TITLE and self.on_shop else None

    def test_all_visible_items_are_done_before_single_exit(self):
        ctx = self.Ctx()
        settings = {SETTINGS_KEY: {
            "tribute": True, "vip_points": True, "chip_100": True}}
        ranges = {"daily": (350, 600), "below": (350, 660)}
        with mock.patch.object(run, "_open_shop", return_value=True) as opened,                 mock.patch.object(run, "_fast_scroll") as fast, \
                mock.patch.object(run, "_visible_section_ranges",
                                  return_value=(ranges, True, False)), \
                mock.patch.object(run, "_find_item",
                                  return_value=((100, 100), .99, False)), \
                mock.patch.object(run, "_price_green", return_value=False):
            run._run_shop_session(ctx, settings)
        opened.assert_called_once_with(ctx)
        fast.assert_called_once()
        self.assertEqual(2, ctx.back_calls)
        self.assertEqual(0, ctx.swipes)
        self.assertEqual({run.TRIBUTE_DAY_KEY, run.DAY_KEY,
                          run._item_done_key("chip_100")}, ctx.done)

    def test_slow_scroll_down_stops_at_bottom_truce(self):
        ctx = self.Ctx()
        settings = {SETTINGS_KEY: {"chip_100": True}}
        ranges = {"daily": None, "below": None}
        with (mock.patch.object(run, "_open_shop", return_value=True),
              mock.patch.object(run, "_visible_section_ranges",
                                return_value=(ranges, True, False)),
              mock.patch.object(run, "_bottom_reached",
                                side_effect=[False, False, True]),
              mock.patch.object(run, "_find_item",
                                return_value=(None, 0.0, False)),
              mock.patch.object(run, "SCROLLS", 10)):
            run._run_shop_session(ctx, settings)

        self.assertEqual([run.SWIPE, run.SWIPE], ctx.swipe_args)
        self.assertTrue(any("đã quét hết" in line for line in ctx.logs))

    def test_every_swipe_taps_shop_title_first(self):
        ctx = self.Ctx()
        settings = {SETTINGS_KEY: {"chip_100": True}}
        ranges = {"daily": None, "below": None}
        with (mock.patch.object(run, "_open_shop", return_value=True),
              mock.patch.object(run, "_visible_section_ranges",
                                return_value=(ranges, False, False)),
              mock.patch.object(run, "_bottom_reached", return_value=False),
              mock.patch.object(run, "_find_item",
                                return_value=(None, 0.0, False)),
              mock.patch.object(run, "SCROLLS", 4)):
            run._run_shop_session(ctx, settings)

        self.assertEqual(4, ctx.swipes)
        self.assertEqual([run.UNFOCUS_TAP] * 4, ctx.taps)

    def test_no_unfocus_tap_when_not_on_shop_screen(self):
        ctx = self.Ctx()
        ctx.on_shop = False
        run._swipe(ctx, run.SWIPE, run.SWIPE_DURATION)
        self.assertEqual([], ctx.taps)
        self.assertEqual([run.SWIPE], ctx.swipe_args)

    def test_after_fast_scroll_goes_down_to_truce_then_up_to_daily_sale(self):
        ctx = self.Ctx()
        settings = {SETTINGS_KEY: {"vip_points": True, "chip_100": True}}
        below = {"daily": (56, 600), "below": (56, 660), "daily_y": None}
        top = {"daily": (300, 600), "below": (300, 660), "daily_y": 300}
        frames = [below, below, below, top]
        with (mock.patch.object(run, "_open_shop", return_value=True),
              mock.patch.object(run, "_fast_scroll") as fast,
              mock.patch.object(run, "_visible_section_ranges",
                                side_effect=[(f, True, False) for f in frames]),
              mock.patch.object(run, "_bottom_reached",
                                side_effect=[False, True]),
              mock.patch.object(run, "_find_item",
                                return_value=(None, 0.0, False)),
              mock.patch.object(run, "SCROLLS", 10)):
            run._run_shop_session(ctx, settings)

        fast.assert_called_once()
        self.assertEqual([run.SWIPE, run.SWIPE_UP, run.SWIPE_UP], ctx.swipe_args)
        self.assertTrue(any("tiêu đề Daily Sale" in line for line in ctx.logs))

    def test_bought_item_is_done_without_waiting_for_gray_price(self):
        ctx = self.Ctx()
        settings = {SETTINGS_KEY: {"chip_100": True}}
        ranges = {"daily": (350, 600), "below": (350, 660)}
        with (mock.patch.object(run, "_open_shop", return_value=True),
              mock.patch.object(run, "_visible_section_ranges",
                                return_value=(ranges, True, False)),
              mock.patch.object(run, "_find_item",
                                return_value=((100, 400), .99, False)),
              mock.patch.object(run, "_price_green", return_value=True),
              mock.patch.object(run, "_buy", return_value=run._BOUGHT) as buy):
            run._run_shop_session(ctx, settings)

        buy.assert_called_once()
        self.assertEqual({run._item_done_key("chip_100")}, ctx.done)
        self.assertEqual(0, ctx.swipes)

    def test_not_enough_points_marks_all_selected_done_and_stops(self):
        ctx = self.Ctx()
        settings = {SETTINGS_KEY: {"vip_points": True, "chip_100": True,
                                   "food_100k": True}}
        ranges = {"daily": (350, 600), "below": (350, 660)}
        with (mock.patch.object(run, "_open_shop", return_value=True),
              mock.patch.object(run, "_fast_scroll"),
              mock.patch.object(run, "_visible_section_ranges",
                                return_value=(ranges, True, False)),
              mock.patch.object(run, "_find_item",
                                return_value=((100, 400), .99, False)),
              mock.patch.object(run, "_price_green", return_value=True),
              mock.patch.object(run, "_buy", return_value=run._NO_POINTS) as buy):
            run._run_shop_session(ctx, settings)

        buy.assert_called_once()
        self.assertEqual({run.DAY_KEY, run._item_done_key("chip_100"),
                          run._item_done_key("food_100k")}, ctx.done)
        self.assertEqual(0, ctx.swipes)
        self.assertEqual(2, ctx.back_calls)

    def test_no_fast_scroll_without_vip_or_tribute(self):
        ctx = self.Ctx()
        settings = {SETTINGS_KEY: {"chip_100": True}}
        ranges = {"daily": None, "below": None}
        with (mock.patch.object(run, "_open_shop", return_value=True),
              mock.patch.object(run, "_fast_scroll") as fast,
              mock.patch.object(run, "_visible_section_ranges",
                                return_value=(ranges, False, False)),
              mock.patch.object(run, "_find_item",
                                return_value=(None, 0.0, False)),
              mock.patch.object(run, "SCROLLS", 1)):
            run._run_shop_session(ctx, settings)
        fast.assert_not_called()


class SectionRangeTests(unittest.TestCase):
    class Ctx:
        def __init__(self, daily=None, weekly=None):
            self.headers = {run.DAILY_HEADER: daily, run.WEEKLY_HEADER: weekly}

        def find(self, template, screen=None):
            return self.headers[template]

    screen = np.zeros((704, 396, 3), dtype=np.uint8)

    def test_monthly_above_daily_sale_is_never_bought(self):
        ranges, daily, weekly = run._visible_section_ranges(
            self.Ctx(), self.screen, False, False)
        self.assertIsNone(ranges["daily"])
        self.assertIsNone(ranges["below"])
        self.assertFalse(daily or weekly)

    def test_ranges_start_at_daily_sale_header(self):
        ranges, _, _ = run._visible_section_ranges(
            self.Ctx(daily=(199, 494)), self.screen, False, False)
        self.assertEqual(494, ranges["daily"][0])
        self.assertEqual(494, ranges["below"][0])

    def test_vip_range_stops_at_weekly_sale(self):
        ranges, daily, weekly = run._visible_section_ranges(
            self.Ctx(weekly=(199, 628)), self.screen, True, False)
        self.assertEqual(628, ranges["daily"][1])
        self.assertTrue(daily and weekly)


if __name__ == "__main__":
    unittest.main()
