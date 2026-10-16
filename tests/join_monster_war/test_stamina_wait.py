"""Mốc hết thể lực (stamina_wait.py): Join Boss lưu "bây giờ + 20 phút", worker so mốc đó với giờ hiện tại."""
import unittest
from datetime import datetime, timedelta
from unittest import mock

from bot.activities.join_monster_war import stamina_wait as sw

NOW = datetime(2026, 10, 15, 21, 0, 0)


class StaminaWaitTests(unittest.TestCase):
    def test_save_stores_now_plus_20_minutes_in_the_key(self):
        ctx = mock.Mock()
        ctx.daily_keys.return_value = []
        until = sw.save(ctx, NOW)
        self.assertEqual(until, NOW + timedelta(minutes=20))
        ctx.mark_daily_done.assert_called_once_with("join_boss_stamina_until_2026-10-15 21:20:00")

    def test_save_removes_old_marks_only(self):
        ctx = mock.Mock()
        ctx.daily_keys.return_value = ["join_boss_stamina_until_2026-10-15 20:00:00", "daily_offering"]
        sw.save(ctx, NOW)
        ctx.forget_daily.assert_called_once_with("join_boss_stamina_until_2026-10-15 20:00:00")

    def test_waiting_until_the_mark_then_join_boss_again(self):
        keys = ["daily_offering", "join_boss_stamina_until_2026-10-15 21:20:00"]
        self.assertTrue(sw.waiting(keys, NOW + timedelta(minutes=19, seconds=59)))
        self.assertFalse(sw.waiting(keys, NOW + timedelta(minutes=20)))

    def test_no_mark_or_bad_mark_is_not_waiting(self):
        self.assertFalse(sw.waiting([], NOW))
        self.assertFalse(sw.waiting(["join_boss_stamina_until_xyz"], NOW))


if __name__ == "__main__":
    unittest.main()
