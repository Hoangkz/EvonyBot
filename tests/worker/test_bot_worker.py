import unittest
from types import SimpleNamespace
from unittest import mock

from bot.common import no_gems
from bot.worker.bot_worker import BotWorker, JOIN_BOSS


DAILY = "Daily Activities"


class BotWorkerPreflightTests(unittest.TestCase):
    def _worker(self):
        return BotWorker("test-device", [], {DAILY: {}, JOIN_BOSS: {}})

    def test_daily_does_not_open_settings_to_discover_server(self):
        worker = self._worker()
        worker._ensure_server = mock.Mock()
        worker._run_activity = mock.Mock()

        worker._run_once([DAILY])

        worker._ensure_server.assert_not_called()
        worker._run_activity.assert_called_once_with(DAILY, {})

    def test_join_monster_war_still_discovers_server(self):
        worker = self._worker()
        worker._ensure_server = mock.Mock()
        worker._run_activity = mock.Mock()

        worker._run_once([JOIN_BOSS])

        worker._ensure_server.assert_called_once_with()
        worker._run_activity.assert_called_once_with(JOIN_BOSS, {})


class OutOfGemsTests(unittest.TestCase):
    """Nhiệm vụ báo hết kim cương (no_gems.flag) -> worker loại nó khỏi danh sách ngay, không thử lại (không lưu DB)."""

    def _worker(self, run_one):
        worker = BotWorker("test-device", [], {DAILY: {}, JOIN_BOSS: {}})
        worker.ctx = mock.Mock()
        worker.guards = mock.Mock()
        worker.activity_changed = mock.Mock()
        worker.record = mock.Mock()
        worker._run_one = lambda task: run_one(worker)
        return worker

    @staticmethod
    def _task(key="patrol"):
        return SimpleNamespace(key=key, must_finish=False, idle_only=False, done=None, group="Event")

    def test_flagged_task_is_dropped(self):
        worker = self._worker(lambda w: no_gems.flag(w.ctx))
        worker._run_task(self._task("patrol"), False)
        self.assertEqual(worker.gems_out, {"patrol"})

    def test_unflagged_task_stays(self):
        worker = self._worker(lambda w: None)
        worker._run_task(self._task("patrol"), False)
        self.assertEqual(worker.gems_out, set())

    def test_stale_flag_from_earlier_run_is_ignored(self):
        worker = self._worker(lambda w: None)
        no_gems.flag(worker.ctx)   # cờ sót lại từ lần trước
        worker._run_task(self._task("patrol"), False)
        self.assertEqual(worker.gems_out, set())


if __name__ == "__main__":
    unittest.main()
