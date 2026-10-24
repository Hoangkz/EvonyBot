"""Mốc hết thể lực (stamina_wait.py): Join Boss đặt "bây giờ + 20 phút" trên ctx (không lưu DB), worker hỏi mốc mỗi vòng."""
import unittest
from types import SimpleNamespace
from unittest import mock

from bot.activities.join_monster_war import stamina_wait as sw

NOW = 1000.0   # time.monotonic() giả


class StaminaWaitTests(unittest.TestCase):
    def test_save_sets_now_plus_20_minutes_on_ctx_only(self):
        ctx = mock.Mock(spec=["stamina_until"])   # không có mark_daily_done: gọi tới DB là lỗi
        sw.save(ctx, NOW)
        self.assertEqual(ctx.stamina_until, NOW + 20 * 60)

    def test_waiting_until_the_mark_then_join_boss_again(self):
        ctx = SimpleNamespace()
        sw.save(ctx, NOW)
        self.assertTrue(sw.waiting(ctx, NOW + 20 * 60 - 1))
        self.assertFalse(sw.waiting(ctx, NOW + 20 * 60))

    def test_new_mark_replaces_old(self):
        ctx = SimpleNamespace()
        sw.save(ctx, NOW)
        sw.save(ctx, NOW + 600)
        self.assertTrue(sw.waiting(ctx, NOW + 20 * 60 + 1))

    def test_fresh_context_is_not_waiting(self):
        self.assertFalse(sw.waiting(SimpleNamespace(), NOW))
        self.assertEqual(sw.remaining(SimpleNamespace(), NOW), 0.0)


if __name__ == "__main__":
    unittest.main()
