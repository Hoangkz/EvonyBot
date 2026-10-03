import unittest
from unittest import mock

from bot.worker.bot_worker import BotWorker, DAILY, JOIN_BOSS


class BotWorkerPreflightTests(unittest.TestCase):
    def _worker(self):
        return BotWorker("test-device", [], {DAILY: {}, JOIN_BOSS: {}})

    def test_daily_does_not_open_settings_to_discover_server(self):
        worker = self._worker()
        worker._ensure_server_time = mock.Mock()
        worker._ensure_server = mock.Mock()
        worker._run_activity = mock.Mock()

        worker._run_once([DAILY])

        worker._ensure_server_time.assert_called_once_with()
        worker._ensure_server.assert_not_called()
        worker._run_activity.assert_called_once_with(DAILY, {})

    def test_join_monster_war_still_discovers_server(self):
        worker = self._worker()
        worker._ensure_server_time = mock.Mock()
        worker._ensure_server = mock.Mock()
        worker._run_activity = mock.Mock()

        worker._run_once([JOIN_BOSS])

        worker._ensure_server.assert_called_once_with()
        worker._run_activity.assert_called_once_with(JOIN_BOSS, {})


if __name__ == "__main__":
    unittest.main()
