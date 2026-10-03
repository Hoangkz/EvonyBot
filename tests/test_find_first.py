import unittest

import numpy as np

from bot.common import find_first


class _Bot:
    def __init__(self, answers):
        self.answers = list(answers)
        self.calls = []

    def find(self, path, **kwargs):
        self.calls.append((path, kwargs["region"]))
        return self.answers.pop(0)


class AdaptiveRegionTests(unittest.TestCase):
    def setUp(self):
        self.screen = np.zeros((100, 200, 3), dtype=np.uint8)

    def test_cached_position_uses_small_region(self):
        cache = {"button.png": (100, 50)}
        bot = _Bot([(102, 51)])

        action, pos = find_first(bot, self.screen, [("button.png", "tap")],
                                 position_cache=cache, fallback_full=True)

        self.assertEqual((action, pos), ("tap", (102, 51)))
        self.assertEqual(len(bot.calls), 1)
        self.assertEqual(bot.calls[0][1], (36.0, 40.0, 64.0, 60.0))
        self.assertEqual(cache["button.png"], (102, 51))

    def test_region_miss_falls_back_to_full_screen(self):
        cache = {"button.png": (20, 20)}
        bot = _Bot([None, (170, 80)])

        action, pos = find_first(bot, self.screen, [("button.png", "tap")],
                                 position_cache=cache, fallback_full=True)

        self.assertEqual((action, pos), ("tap", (170, 80)))
        self.assertIsNotNone(bot.calls[0][1])
        self.assertIsNone(bot.calls[1][1])
        self.assertEqual(cache["button.png"], (170, 80))


if __name__ == "__main__":
    unittest.main()
