import threading
import unittest
from types import SimpleNamespace
from unittest import mock

from bot.context import BotContext
from bot.context.errors import BossAvailable, StopRequested
from bot.worker import bot_worker
from bot.worker.boss_board import BossBoard
from bot.worker.bot_worker import BOSS_IDLE, JOIN_BOSS, BotWorker
from bot.worker.server_clock import ServerClock
from bot.worker.tasks import Task


class BossNotificationTests(unittest.TestCase):
    def test_server_isolation_deduplication_and_expiry(self):
        now = [0]
        board = BossBoard(clock=lambda: now[0])
        source, same, other = (threading.Event() for _ in range(3))
        for serial, server, event in [("a", "1", source), ("b", "1", same), ("c", "2", other)]:
            board.register(serial, server, event)
        self.assertTrue(board.publish("a", "1", (10, 20)))
        self.assertTrue(same.is_set())
        self.assertFalse(source.is_set())
        self.assertFalse(other.is_set())
        same.clear()
        self.assertFalse(board.publish("a", "1", (10, 20)))
        self.assertFalse(same.is_set())
        now[0] = 121
        self.assertTrue(board.publish("a", "1", (10, 20)))
        self.assertTrue(same.is_set())
        same.clear()
        board.unregister("b")
        board.publish("a", "1", (30, 40))
        self.assertFalse(same.is_set())
        self.assertFalse(board.publish("a", "", (50, 60)))

    def test_interrupt_only_secondary_activity_and_stop_has_priority(self):
        ctx = BotContext(SimpleNamespace(serial="b"), threading.Event(), None, lambda _: None)
        ctx._boss_event.set()
        ctx.check()  # Boss execution itself must not be interrupted.
        ctx._boss_interrupt_enabled = True
        with self.assertRaises(BossAvailable):
            ctx.sleep(10)
        ctx._stop.set()
        with self.assertRaises(StopRequested):
            ctx.check()

    def test_notification_returns_to_boss_and_retries_pending_activity(self):
        board = BossBoard()
        worker = BotWorker("b", [JOIN_BOSS, "secondary"], {
            "Initialization": {"server": "1"}
        }, boss_board=board, server_clock=ServerClock("known"))
        worker.ctx = BotContext(SimpleNamespace(serial="b"), worker._stop, None, worker.log)
        worker._register_boss_listener()
        calls = []

        def run_activity(activity, settings):
            calls.append(activity)
            self.assertFalse(worker.ctx._boss_interrupt_enabled)
            self.assertIsNone(worker.ctx._deadline)
            if calls.count(JOIN_BOSS) == 3:
                worker._stop.set()   # đủ kịch bản: vòng lặp (sống tới khi Stop) dừng
            return BOSS_IDLE

        def run_secondary(ctx, settings):
            calls.append("secondary")
            if calls.count("secondary") == 1:
                board.publish("a", "1", (10, 20))
                ctx.check()

        worker._run_activity = run_activity
        with mock.patch.object(bot_worker, "build_tasks",
                               return_value=[Task("secondary", "G", 1, run=run_secondary)]),                 self.assertRaises(StopRequested):
            worker._run_tasks()
        self.assertEqual(calls, [JOIN_BOSS, "secondary", JOIN_BOSS, "secondary", JOIN_BOSS])
        self.assertFalse(worker.ctx._boss_interrupt_enabled)
        self.assertIsNone(worker.ctx._deadline)

if __name__ == "__main__":
    unittest.main()
