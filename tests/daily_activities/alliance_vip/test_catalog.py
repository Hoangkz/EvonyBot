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
            center = (image.shape[1] // 2, image.shape[0] // 2)
            for expected in items:
                self.assertEqual(
                    visible.key == expected.key,
                    run._truce_color_matches(
                        bot, image, center, expected.template),
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
                self.assertGreater(distance, run.TRUCE_COLOR_MIN_MARGIN)


class DoneTests(unittest.TestCase):
    class Ctx:
        def __init__(self, done=()):
            self.done = set(done)

        def is_daily_done(self, key):
            return key in self.done

    def test_explicit_empty_selection_is_done(self):
        settings = {SETTINGS_KEY: {item.key: 0 for item in ITEMS}}
        self.assertTrue(run._all_selected_items_done(self.Ctx(), settings))
        self.assertFalse(run._catalog_done(self.Ctx(), settings))

    def test_priority_item_requires_monthly_and_daily_done(self):
        settings = {SETTINGS_KEY: {"tribute": True}}
        self.assertFalse(run._all_selected_items_done(self.Ctx(), settings))
        self.assertTrue(run._all_selected_items_done(
            self.Ctx({run.TRIBUTE_MONTH_KEY, run.TRIBUTE_DAY_KEY}), settings))

    def test_normal_item_requires_its_own_done_key(self):
        settings = {SETTINGS_KEY: {"chip_100": True}}
        self.assertFalse(run._all_selected_items_done(self.Ctx(), settings))
        self.assertTrue(run._all_selected_items_done(
            self.Ctx({run._item_done_key("chip_100")}), settings))

    def test_total_done_key_skips_whole_job(self):
        settings = {SETTINGS_KEY: {"tribute": True, "food_100k": True}}
        self.assertTrue(run._catalog_done(
            self.Ctx({run.ALL_DONE_KEY}), settings))


class SingleSessionTests(unittest.TestCase):
    class Ctx:
        def __init__(self):
            self.done = set()
            self.back_calls = 0
            self.swipes = 0
            self.logs = []

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

    def test_all_visible_items_are_done_before_single_exit(self):
        ctx = self.Ctx()
        settings = {SETTINGS_KEY: {
            "tribute": True, "vip_points": True, "chip_100": True}}
        ranges = {"monthly": (50, 350), "daily": (350, 660)}
        with mock.patch.object(run, "_open_shop", return_value=True) as opened, \
                mock.patch.object(run, "_shop_to_top"), \
                mock.patch.object(run, "_visible_section_ranges",
                                  return_value=(ranges, True, False)), \
                mock.patch.object(run, "_find_item",
                                  return_value=((100, 100), .99, False)), \
                mock.patch.object(run, "_price_green", return_value=False):
            run._run_shop_session(ctx, settings)
        opened.assert_called_once_with(ctx)
        self.assertEqual(2, ctx.back_calls)
        self.assertEqual(0, ctx.swipes)
        self.assertTrue({run.TRIBUTE_MONTH_KEY, run.TRIBUTE_DAY_KEY,
                         run.MONTH_KEY, run.DAY_KEY,
                         run._item_done_key("chip_100")}.issubset(ctx.done))

    def test_shop_requires_weekly_marker_and_three_stable_swipes_for_bottom(self):
        ctx = self.Ctx()
        settings = {SETTINGS_KEY: {"chip_100": True}}
        ranges = {"monthly": None, "daily": None}
        with (mock.patch.object(run, "_open_shop", return_value=True),
              mock.patch.object(run, "_shop_to_top"),
              mock.patch.object(run, "_visible_section_ranges",
                                return_value=(ranges, True, True)),
              mock.patch.object(run, "_find_item",
                                return_value=(None, 0.0, False)),
              mock.patch.object(run, "SCROLLS", 10)):
            run._run_shop_session(ctx, settings)

        self.assertEqual(3, ctx.swipes)
        self.assertTrue(any("xác nhận đã tới cuối" in line
                            for line in ctx.logs))

    def test_shop_does_not_call_stable_frame_bottom_before_weekly_marker(self):
        ctx = self.Ctx()
        settings = {SETTINGS_KEY: {"chip_100": True}}
        ranges = {"monthly": None, "daily": None}
        with (mock.patch.object(run, "_open_shop", return_value=True),
              mock.patch.object(run, "_shop_to_top"),
              mock.patch.object(run, "_visible_section_ranges",
                                return_value=(ranges, False, False)),
              mock.patch.object(run, "_find_item",
                                return_value=(None, 0.0, False)),
              mock.patch.object(run, "SCROLLS", 4)):
            run._run_shop_session(ctx, settings)

        self.assertEqual(4, ctx.swipes)
        self.assertFalse(any("xác nhận đã tới cuối" in line
                             for line in ctx.logs))


if __name__ == "__main__":
    unittest.main()
