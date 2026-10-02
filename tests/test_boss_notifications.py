import threading
import unittest
from types import SimpleNamespace

from bot.context import BotContext
from bot.context.errors import BossAvailable, StopRequested, YieldToBoss
from bot.worker.boss_board import BossBoard
from bot.worker.bot_worker import BOSS_IDLE, JOIN_BOSS, BotWorker
from bot.worker.server_clock import ServerClock


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
            if activity == JOIN_BOSS:
                self.assertFalse(worker.ctx._boss_interrupt_enabled)
                self.assertIsNone(worker.ctx._deadline)
                return BOSS_IDLE
            if calls.count("secondary") == 1:
                board.publish("a", "1", (10, 20))
                worker.ctx.check()

        worker._run_activity = run_activity
        worker._boss_priority(["secondary"])
        self.assertEqual(calls, [JOIN_BOSS, "secondary", JOIN_BOSS, "secondary", JOIN_BOSS])
        self.assertFalse(worker.ctx._boss_interrupt_enabled)
        self.assertIsNone(worker.ctx._deadline)

    def test_yield_to_boss_only_in_boss_window(self):
        """yield_to_boss(): ngoài lượt activity phụ (không bật ngắt boss) không làm gì; trong lượt
        thì nhường (YieldToBoss)."""
        ctx = BotContext(SimpleNamespace(serial="b"), threading.Event(), None, lambda _: None)
        ctx.yield_to_boss()
        ctx._boss_interrupt_enabled = True
        with self.assertRaises(YieldToBoss):
            ctx.yield_to_boss()

    def test_task_done_returns_to_boss_and_retries_activity(self):
        """Activity phụ xong 1 nhiệm vụ (yield_to_boss) -> worker kiểm tra boss ngay, rồi gọi lại
        activity đó (chưa bỏ khỏi danh sách chờ)."""
        worker = BotWorker("b", [JOIN_BOSS, "secondary"], {
            "Initialization": {"server": "1"}
        }, server_clock=ServerClock("known"))
        worker.ctx = BotContext(SimpleNamespace(serial="b"), worker._stop, None, worker.log)
        calls = []

        def run_activity(activity, settings):
            calls.append(activity)
            if activity == JOIN_BOSS:
                return BOSS_IDLE
            if calls.count("secondary") == 1:
                worker.ctx.yield_to_boss()

        worker._run_activity = run_activity
        worker._boss_priority(["secondary"])
        self.assertEqual(calls, [JOIN_BOSS, "secondary", JOIN_BOSS, "secondary", JOIN_BOSS])
        self.assertFalse(worker.ctx._boss_interrupt_enabled)


if __name__ == "__main__":
    unittest.main()
