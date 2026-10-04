import time
import unittest
from unittest import mock

from bot.activities.join_monster_war.boss_memory import (
    JOINED,
    MAX_ENTRIES,
    SKIPPED,
    TTL,
    BossMemory,
)


class BossMemoryTests(unittest.TestCase):
    def setUp(self):
        self.now = 1000.0
        patcher = mock.patch.object(time, "monotonic", lambda: self.now)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_remembers_status_until_ttl(self):
        memory = BossMemory()
        memory.mark((649, 865), JOINED)
        memory.mark((633, 941), SKIPPED)
        self.assertEqual(memory.status((649, 865)), JOINED)
        self.assertEqual(memory.status((633, 941)), SKIPPED)
        self.assertIsNone(memory.status((1, 2)))

        self.now += TTL - 1
        self.assertEqual(memory.status((649, 865)), JOINED)
        self.now += 1
        self.assertIsNone(memory.status((649, 865)))
        self.assertIsNone(memory.status((633, 941)))

    def test_ttl_is_six_minutes(self):
        self.assertEqual(TTL, 360)

    def test_mark_again_renews_and_updates(self):
        memory = BossMemory()
        memory.mark((649, 865), SKIPPED)
        self.now += TTL - 10
        memory.mark((649, 865), JOINED)
        self.now += 20
        self.assertEqual(memory.status((649, 865)), JOINED)

    def test_unknown_coords_are_not_stored(self):
        memory = BossMemory()
        memory.mark(None, JOINED)
        self.assertIsNone(memory.status(None))

    def test_memory_is_bounded_when_ocr_returns_many_different_coordinates(self):
        memory = BossMemory()
        for value in range(MAX_ENTRIES + 20):
            memory.mark((value, value), JOINED)

        self.assertEqual(len(memory._bosses), MAX_ENTRIES)
        self.assertIsNone(memory.status((0, 0)))
        self.assertEqual(memory.status((MAX_ENTRIES + 19, MAX_ENTRIES + 19)), JOINED)


if __name__ == "__main__":
    unittest.main()
