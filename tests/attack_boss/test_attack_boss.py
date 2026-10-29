"""Attack Boss: chọn nguồn, lọc boss, xen Crazy Eggs (không cần giả lập / ảnh)."""
import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace

from bot.activities import ACTIVITIES, EXCLUSIVE_ACTIVITIES
from bot.activities.attack_boss.constants import (EGGS_KEY, PLAYER_KEY, SOURCE_API, SOURCE_KEY, SOURCE_PLAYER)
from bot.activities.attack_boss.run import attack_type, eggs_due, eggs_hours, order_by_distance, wanted
from bot.activities.attack_boss.sources import (AllianceChatSource, ApiSource, BossOffer, PlayerChatSource, make_source)
from bot.activities.event_center.crazy_eggs.constants import DONE_KEY, TRIED_KEY


class SourceTests(unittest.TestCase):
    def test_make_source(self):
        self.assertIsInstance(make_source({}), AllianceChatSource)
        self.assertIsInstance(make_source({SOURCE_KEY: "lạ"}), AllianceChatSource)
        self.assertIsInstance(make_source({SOURCE_KEY: SOURCE_API}), ApiSource)
        source = make_source({SOURCE_KEY: SOURCE_PLAYER, PLAYER_KEY: " Bob "})
        self.assertIsInstance(source, PlayerChatSource)
        self.assertEqual(source.player_name, "Bob")

    def test_registered_and_exclusive(self):
        self.assertIn("Attack Boss", ACTIVITIES)
        self.assertIn("Attack Boss", EXCLUSIVE_ACTIVITIES)


class WantedTests(unittest.TestCase):
    def test_whisper_attacks_whatever_is_sent(self):
        settings = {SOURCE_KEY: SOURCE_PLAYER, "selected_bosses": []}
        self.assertTrue(wanted(settings, BossOffer(1, 2, "Zombie")))
        self.assertTrue(wanted(settings, BossOffer(1, 2, "Viking")))
        self.assertTrue(wanted(settings, BossOffer(ident=3)))

    def test_other_sources_follow_selection(self):
        self.assertFalse(wanted({"selected_bosses": []}, BossOffer(1, 2, "Zombie")))
        self.assertTrue(wanted({}, BossOffer(1, 2, "Zombie")))    # chưa có lựa chọn: boss nào cũng đánh


class AttackTypeTests(unittest.TestCase):
    def test_type(self):
        self.assertEqual(attack_type({}), "attack")
        self.assertEqual(attack_type({"attack_type": "alliance_war"}), "alliance_war")
        self.assertEqual(attack_type({"attack_type": "lạ"}), "attack")

    def test_player_message_always_attack(self):
        self.assertEqual(attack_type({SOURCE_KEY: SOURCE_PLAYER, "attack_type": "alliance_war"}), "attack")


class OrderTests(unittest.TestCase):
    OFFERS = [BossOffer(538, 133, "Yasha", 7), BossOffer(572, 112, "Centaur", 3), BossOffer(550, 86, "Viking", 2)]

    def test_nearest_first(self):
        ordered = order_by_distance(self.OFFERS, (562, 93))
        self.assertEqual([o.coords for o in ordered], [(550, 86), (572, 112), (538, 133)])

    def test_unknown_home_keeps_order(self):
        self.assertEqual(order_by_distance(self.OFFERS, None), self.OFFERS)


class SpeedupTests(unittest.TestCase):
    def test_plan(self):
        from bot.activities.attack_boss.speedup import COUNT, NONE, UNTIL, plan
        self.assertEqual(plan("No"), (NONE, 0))
        self.assertEqual(plan(None), (NONE, 0))
        self.assertEqual(plan("All"), (UNTIL, 0))
        self.assertEqual([plan(x) for x in ("5s", "10s", "15s", "20s", "30s")], [(UNTIL, n) for n in (5, 10, 15, 20, 30)])
        self.assertEqual([plan(str(n)) for n in range(1, 11)], [(COUNT, n) for n in range(1, 11)])    # số lượng cứng: không đọc thời gian

    def test_uses_needed(self):
        from bot.activities.attack_boss.speedup import uses_needed
        self.assertEqual(uses_needed(60, 30), 1)      # 60 -> 30
        self.assertEqual(uses_needed(61, 30), 2)      # 61 -> 30,5 -> 15,25
        self.assertEqual(uses_needed(556, 10), 6)     # 556 / 64 = 8,7
        self.assertEqual(uses_needed(8, 10), 0)       # đã đủ
        self.assertEqual(uses_needed(100, 0), 7)      # All = còn <= 1 giây: 100 / 128
        self.assertEqual(uses_needed(10 ** 9, 5), 12)   # chặn trần

    def test_choices(self):
        from bot.activities.attack_boss.constants import SPEEDUP_CHOICES, SPEEDUP_DEFAULT
        self.assertEqual(SPEEDUP_CHOICES[:7], ("No", "All", "5s", "10s", "15s", "20s", "30s"))
        self.assertEqual(SPEEDUP_CHOICES[7:], tuple(str(n) for n in range(1, 11)))
        self.assertEqual(SPEEDUP_DEFAULT, "No")


class LanesTests(unittest.TestCase):
    def test_capacity(self):
        from bot.activities.attack_boss.lanes import capacity
        self.assertEqual(capacity(5, 8), 5)        # tài khoản có 5 đường
        self.assertEqual(capacity(6, 8), 6)        # tối đa 6
        self.assertEqual(capacity(9, 9), 6)        # không vượt MAX_LANES
        self.assertEqual(capacity(6, 3), 3)        # chọn ít đội: giảm xuống số đội
        self.assertEqual(capacity(None, 4), 4)     # chưa đọc được số đường tối đa: theo số đội
        self.assertEqual(capacity(5, 0), 1)        # ít nhất 1
        self.assertEqual(capacity(6, 8, learned=4), 4)   # game đã báo hết đường ở 4 đường: học được tối đa 4


class EggsTests(unittest.TestCase):
    @staticmethod
    def bot(done=(), tried=None):
        return SimpleNamespace(is_daily_done=lambda key: key in done,
                               done_at=lambda key: tried if key == TRIED_KEY else None)

    def test_hours(self):
        self.assertEqual(eggs_hours({EGGS_KEY: 2}), 2)
        self.assertEqual(eggs_hours({}), 0)
        self.assertEqual(eggs_hours({EGGS_KEY: "x"}), 0)

    def test_due(self):
        self.assertFalse(eggs_due(self.bot(), 0))
        self.assertTrue(eggs_due(self.bot(), 2))                       # chưa thử lần nào
        self.assertFalse(eggs_due(self.bot(done={DONE_KEY}), 2))       # đủ 4 quả hôm nay
        recent = (datetime.now() - timedelta(hours=1)).isoformat()
        old = (datetime.now() - timedelta(hours=3)).isoformat()
        self.assertFalse(eggs_due(self.bot(tried=recent), 2))
        self.assertTrue(eggs_due(self.bot(tried=old), 2))


if __name__ == "__main__":
    unittest.main()
