"""
test_boss_watch.py — theo dõi số boss khi tìm route công trình (bot_worker._watch_boss_count): cứ 3 cú vuốt đọc số trên huy hiệu
icon listboss; bằng thì vuốt tiếp, giảm thì ghi đè số cũ, tăng thì vào Join Boss tới khi rảnh rồi đọc lại.
"""
import unittest
from unittest import mock

from bot.worker import bot_worker
from bot.worker.bot_worker import BotWorker
from bot.worker.server_clock import ServerClock


class BossWatchTests(unittest.TestCase):
    def make_worker(self, counts):
        worker = BotWorker("b", ["Join Monster War"], {"Initialization": {"server": "1"}}, server_clock=ServerClock("known"))
        worker.ctx = mock.Mock()
        values = iter(counts)
        worker._read_boss_count = lambda: next(values)
        worker._ensure_server = mock.Mock()
        worker._check_boss = mock.Mock(return_value=True)
        return worker

    def test_equal_or_lower_count_keeps_swiping(self):
        worker = self.make_worker([2, 2, 1, 1])
        for _ in range(4):
            worker._watch_boss_count(worker.ctx)
        worker._check_boss.assert_not_called()
        self.assertEqual(worker._boss_count, 1)     # giảm: số cũ bị ghi đè

    def test_first_read_is_only_the_baseline(self):
        worker = self.make_worker([3])
        worker._watch_boss_count(worker.ctx)
        worker._check_boss.assert_not_called()
        self.assertEqual(worker._boss_count, 3)

    def test_higher_count_runs_join_boss_then_resumes(self):
        worker = self.make_worker([1, 2, 0])        # baseline 1 -> tăng 2 -> Join Boss -> đọc lại 0
        worker._watch_boss_count(worker.ctx)
        worker._watch_boss_count(worker.ctx)
        worker._check_boss.assert_called_once()
        self.assertEqual(worker._boss_count, 0)

    def test_unreadable_count_is_ignored(self):
        worker = self.make_worker([2, None, 2])
        for _ in range(3):
            worker._watch_boss_count(worker.ctx)
        worker._check_boss.assert_not_called()
        self.assertEqual(worker._boss_count, 2)


if __name__ == "__main__":
    unittest.main()
