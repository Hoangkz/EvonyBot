import sqlite3
import tempfile
import threading
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from bot.common import NotEnoughGems
from bot.context import BotContext
from bot.context.errors import BossAvailable, BubbleDue, StopRequested
from bot.worker import bot_worker
from bot.worker.bot_worker import BUBBLE_RENEW_BEFORE, BUBBLE_RETRY, BotWorker


def make_worker(bubble=True, bubble_type="3d", activities=("secondary",), bubble_until=""):
    worker = BotWorker("b", list(activities), {
        "Initialization": {"server": "1", "server_time": "known",
                           "bubble": bubble, "bubble_type": bubble_type,
                           "bubble_until": bubble_until},
    })
    worker.ctx = BotContext(SimpleNamespace(serial="b"), worker._stop, None, worker.log)
    worker.found = []
    worker.bubble_found.connect(lambda serial, seconds: worker.found.append(seconds))
    return worker


class FakeGame:
    """Thay keep_bubble: lần gọi thứ i trả về results[i], ghi lại các lần gọi."""

    def __init__(self, results):
        self.results = list(results)
        self.calls = []

    def keep(self, bot, bubble_type, renew_before):
        # Bước bubble không bị boss / deadline cắt ngang.
        assert bot._deadline is None and not bot._boss_interrupt_enabled
        self.calls.append(bubble_type)
        result = self.results.pop(0) if self.results else None
        if isinstance(result, Exception):
            raise result
        return result

    def patch(self):
        return mock.patch.object(bot_worker, "keep_bubble", self.keep)


class BubbleFlowTests(unittest.TestCase):
    def test_disabled_does_nothing(self):
        worker = make_worker(bubble=False)
        game = FakeGame([10])
        with game.patch():
            self.assertFalse(worker._ensure_bubble())
        self.assertEqual(game.calls, [])
        self.assertIsNone(worker.ctx._bubble_due_at)

    def test_schedules_one_hour_before_expiry(self):
        worker = make_worker()
        game = FakeGame([5 * 3600])
        with game.patch():
            self.assertTrue(worker._ensure_bubble())
            # Còn nhiều thời gian: activity sau không vào game xem lại.
            self.assertFalse(worker._ensure_bubble())
        self.assertEqual(game.calls, ["3d"])
        self.assertEqual(worker.found, [5 * 3600])
        self.assertAlmostEqual(worker.ctx._bubble_due_at - time.monotonic(),
                               5 * 3600 - BUBBLE_RENEW_BEFORE, delta=2)

    def test_could_not_renew_retries_later(self):
        worker = make_worker()
        game = FakeGame([1800])     # vẫn còn <= 1 tiếng: dùng không được
        with game.patch():
            worker._ensure_bubble()
            worker._ensure_bubble()
        self.assertEqual(game.calls, ["3d"])
        self.assertEqual(worker.found, [1800])
        self.assertAlmostEqual(worker.ctx._bubble_due_at - time.monotonic(), BUBBLE_RETRY, delta=2)

    def test_read_failure_retries_later_not_before_every_activity(self):
        worker = make_worker()
        game = FakeGame([None])
        with game.patch():
            worker._ensure_bubble()
            worker._ensure_bubble()
        self.assertEqual(game.calls, ["3d"])
        self.assertEqual(worker.found, [])
        self.assertAlmostEqual(worker.ctx._bubble_due_at - time.monotonic(), BUBBLE_RETRY, delta=2)

    def test_not_enough_gems_unticks_bubble(self):
        worker = make_worker()
        disabled = []
        worker.bubble_disabled.connect(disabled.append)
        game = FakeGame([NotEnoughGems()])
        with game.patch():
            self.assertTrue(worker._ensure_bubble())
            self.assertFalse(worker._ensure_bubble())   # đã bỏ tích: không vào game nữa
        self.assertEqual(game.calls, ["3d"])
        self.assertEqual(disabled, ["b"])
        self.assertFalse(worker.bubble_enabled)
        self.assertFalse(worker.settings["Initialization"]["bubble"])
        self.assertIsNone(worker.ctx._bubble_due_at)

    def test_stop_during_bubble_is_not_swallowed(self):
        worker = make_worker()
        game = FakeGame([StopRequested()])
        with game.patch(), self.assertRaises(StopRequested):
            worker._ensure_bubble()

    def test_bubble_due_interrupts_activity_then_reruns_it(self):
        worker = make_worker()
        game = FakeGame([5 * 3600, 3 * 86400])
        runs = []

        def activity(ctx, settings):
            runs.append(ctx._bubble_due_at is not None)
            if len(runs) == 1:
                # Giả lập đã tới lúc bubble còn 1 tiếng giữa activity.
                worker._bubble_next_check = ctx._bubble_due_at = time.monotonic() - 1
                ctx.check()
            return "done"

        worker.ctx._deadline = time.monotonic() + 120
        worker.ctx._boss_interrupt_enabled = True
        saved_deadline = worker.ctx._deadline
        with game.patch(), mock.patch.dict(bot_worker.ACTIVITIES, {"secondary": activity}):
            self.assertEqual(worker._run_activity("secondary", {}), "done")
        self.assertEqual(runs, [True, True])
        self.assertEqual(game.calls, ["3d", "3d"])
        self.assertEqual(worker.found, [5 * 3600, 3 * 86400])
        # Bước bubble không làm mất deadline / ngắt boss của cửa sổ activity phụ.
        self.assertEqual(worker.ctx._deadline, saved_deadline)
        self.assertTrue(worker.ctx._boss_interrupt_enabled)

    def test_saved_bubble_skips_check_until_one_hour_left(self):
        until = (datetime.now() + timedelta(hours=5)).isoformat(timespec="seconds")
        worker = make_worker(bubble_until=until)
        game = FakeGame([])
        with game.patch():
            self.assertFalse(worker._ensure_bubble())
        self.assertEqual(game.calls, [])
        self.assertAlmostEqual(worker.ctx._bubble_due_at - time.monotonic(),
                               4 * 3600, delta=5)

    def test_saved_bubble_almost_over_is_checked(self):
        until = (datetime.now() + timedelta(minutes=30)).isoformat(timespec="seconds")
        worker = make_worker(bubble_until=until)
        game = FakeGame([24 * 3600])
        with game.patch():
            self.assertTrue(worker._ensure_bubble())
        self.assertEqual(game.calls, ["3d"])

    def test_database_keeps_bubble_until_and_migrates_old_db(self):
        from database import Database
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "old.db"
            # DB cũ chưa có cột bubble_until: phải giữ nguyên dữ liệu.
            db = Database(path)
            db.add_device("b")
            db.set_server("b", "123")
            db.close()
            conn = sqlite3.connect(path)
            conn.execute("ALTER TABLE devices DROP COLUMN bubble_until")
            conn.commit()
            conn.close()

            db = Database(path)
            self.assertEqual(db.load_settings("b")["Initialization"]["server"], "123")
            db.set_bubble_until("b", "2026-10-05T10:00:00")
            self.assertEqual(db.load_settings("b")["Initialization"]["bubble_until"],
                             "2026-10-05T10:00:00")
            # Lưu tab Initialization (Apply ALL) không ghi đè bubble_until.
            db.save_settings("b", {"Initialization": {"bubble": True, "bubble_until": ""}})
            self.assertEqual(db.load_settings("b")["Initialization"]["bubble_until"],
                             "2026-10-05T10:00:00")
            db.close()

    def test_check_priority_stop_then_bubble_then_boss(self):
        ctx = BotContext(SimpleNamespace(serial="b"), threading.Event(), None, lambda _: None)
        ctx._boss_event.set()
        ctx._boss_interrupt_enabled = True
        ctx._bubble_due_at = time.monotonic() - 1
        with self.assertRaises(BubbleDue):
            ctx.check()
        ctx._bubble_due_at = None
        with self.assertRaises(BossAvailable):
            ctx.check()
        ctx._bubble_due_at = time.monotonic() - 1
        ctx._stop.set()
        with self.assertRaises(StopRequested):
            ctx.check()


if __name__ == "__main__":
    unittest.main()
