"""ApiSource (IsCout): lượt 6 boss gần thành nhất, boss dời chỗ theo id, popup + dừng khi có vấn đề (không cần Chrome / giả lập)."""
import unittest
from types import SimpleNamespace
from unittest import mock

from bot.activities.attack_boss import sources
from bot.activities.attack_boss.constants import ISCOUT_BATCH
from bot.activities.attack_boss.run import wanted
from bot.activities.attack_boss.sources import ApiSource, BossOffer
from bot.context.errors import StopRequested
from bot.iscout.hub import IScoutNoCredentials, IScoutNotOpen


def boss(uid, x, y):
    return {"id": uid, "name": "Rùa Nham thạch", "level": 1, "x": x, "y": y}


def make_bot(home=(0, 0)):
    bot = SimpleNamespace(server="1835", attack_home=home, alerts=[], logs=[])
    bot.alert = bot.alerts.append
    bot.log = bot.logs.append
    return bot


class ApiSourceTests(unittest.TestCase):
    def feed(self, *pages):
        pages = iter(pages)

        def bosses(server, email="", password=""):
            page = next(pages)
            if isinstance(page, Exception):
                raise page
            return page
        patch = mock.patch.object(sources.iscout, "get_hub", lambda: SimpleNamespace(bosses=bosses))
        patch.start()
        self.addCleanup(patch.stop)

    def test_batch_is_the_six_nearest_to_home_and_skips_done(self):
        self.feed([boss(str(i), 100 - i, 0) for i in range(10)])        # id 9 gần thành (0, 0) nhất
        source = ApiSource("a@b.c", "pw", clock=lambda: 100.0)
        source.done["9"] = 100.0
        offers = source.poll(make_bot())
        self.assertEqual([o.uid for o in offers], ["8", "7", "6", "5", "4", "3"])
        self.assertEqual(len(offers), ISCOUT_BATCH)

    def test_next_batch_only_after_the_whole_batch_is_finished(self):
        bosses = [boss(str(i), 10 + i, 0) for i in range(8)]
        self.feed(bosses, bosses, bosses, bosses)
        source, bot = ApiSource("a@b.c", "pw"), make_bot()
        first = source.poll(bot)
        self.assertEqual([o.uid for o in first], ["0", "1", "2", "3", "4", "5"])
        for offer in first[:-1]:
            source.finished(offer)
        self.assertEqual(source.poll(bot), [])                 # còn 1 boss của lượt chưa xong: chưa lấy lượt mới
        source.finished(first[-1])
        self.assertEqual([o.uid for o in source.poll(bot)], ["6", "7"])
        self.assertEqual(source.poll(bot), [])

    def test_moved_boss_in_batch_is_offered_with_new_coords_and_done_is_not_repeated(self):
        self.feed([boss("a", 556, 66)], [boss("a", 554, 66)], [boss("a", 552, 66)])
        source, bot = ApiSource("a@b.c", "pw"), make_bot()
        self.assertEqual([o.coords for o in source.poll(bot)], [(556, 66)])
        moved = source.poll(bot)
        self.assertEqual([(o.uid, o.coords) for o in moved], [("a", (554, 66))])
        source.finished(moved[0])
        self.assertEqual(source.poll(bot), [])

    def test_dead_boss_leaves_the_batch(self):
        self.feed([boss("a", 1, 2), boss("b", 3, 4)], [boss("b", 3, 4)], [boss("b", 3, 4)])
        source, bot = ApiSource("a@b.c", "pw"), make_bot()
        first = source.poll(bot)
        source.finished(first[0])
        self.assertEqual(source.poll(bot), [])                 # b đã trả rồi, vẫn trong lượt
        source.finished(first[1])
        self.assertEqual(source.poll(bot), [])                 # b đã tính là đã đánh

    def test_boss_not_found_also_counts_as_attacked(self):
        self.feed([boss("a", 1, 2)], [boss("a", 1, 2)])
        source, bot = ApiSource("a@b.c", "pw"), make_bot()
        source.finished(source.poll(bot)[0])      # run bỏ boss vì không thấy ở toạ độ đó -> cũng gọi finished
        self.assertEqual(source.poll(bot), [])

    def test_attacked_boss_is_remembered_for_10_minutes_only(self):
        now = [1000.0]
        bosses = [boss("a", 1, 2)]
        self.feed(bosses, bosses, bosses)
        source, bot = ApiSource("a@b.c", "pw", clock=lambda: now[0]), make_bot()
        source.finished(source.poll(bot)[0])
        now[0] += 9 * 60
        self.assertEqual(source.poll(bot), [])                       # 9 phút: vẫn nhớ, không đánh lại
        now[0] += 2 * 60
        self.assertEqual([o.uid for o in source.poll(bot)], ["a"])   # 11 phút: quá hạn, boss còn sống thì đánh lại

    def test_problem_alerts_and_stops(self):
        self.feed(IScoutNotOpen())
        bot = make_bot()
        with self.assertRaises(StopRequested):
            ApiSource("a@b.c", "pw").poll(bot)
        self.assertEqual(bot.alerts, [IScoutNotOpen.message])

    def test_missing_email_or_password_alerts_and_stops_before_opening_anything(self):
        self.feed([boss("a", 1, 2)])
        for email, password in (("", "pw"), ("a@b.c", ""), ("", "")):
            bot = make_bot()
            with self.assertRaises(StopRequested):
                ApiSource(email, password).poll(bot)
            self.assertEqual(bot.alerts, [IScoutNoCredentials.message])

    def test_api_source_attacks_every_boss_without_filter(self):
        self.assertTrue(wanted({"source": "api"}, BossOffer(556, 66, "Rùa Nham thạch", 1)))


if __name__ == "__main__":
    unittest.main()
