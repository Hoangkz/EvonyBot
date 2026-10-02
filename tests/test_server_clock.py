"""
Giờ reset server dùng chung mọi thiết bị: ServerClock (worker đầu tiên đi lấy, worker khác chạy bình
thường) và bảng `settings` của DB (chuyển cột devices.server_time cũ sang, xoá cột).
"""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import database
from bot.worker import bot_worker
from bot.worker.bot_worker import BotWorker
from bot.worker.server_clock import ServerClock


def make_worker(clock):
    worker = BotWorker("b", ["secondary"], {"Initialization": {"server": "1"}}, server_clock=clock)
    worker.ctx = SimpleNamespace()
    worker.found = []
    worker.server_time_found.connect(lambda serial, value: worker.found.append(value))
    return worker


class ServerClockTests(unittest.TestCase):
    def test_first_worker_fetches_others_skip(self):
        """Worker A đang đi lấy (đã claim): worker B không lấy, chạy tiếp; A lấy xong thì B dùng chung."""
        clock = ServerClock()
        self.assertTrue(clock.claim())          # A nhận việc
        b = make_worker(clock)
        with mock.patch.object(bot_worker, "get_server_time") as fetch:
            b._ensure_server_time()
        fetch.assert_not_called()
        self.assertEqual(b.server_time, "")
        clock.release("2026-10-03T09:00:00")    # A lấy xong
        self.assertEqual(b.server_time, "2026-10-03T09:00:00")

    def test_fetch_once_then_shared(self):
        clock = ServerClock()
        a, b = make_worker(clock), make_worker(clock)
        with mock.patch.object(bot_worker, "get_server_time", return_value="2026-10-03T09:00:00") as fetch:
            a._ensure_server_time()
            b._ensure_server_time()
        fetch.assert_called_once()
        self.assertEqual((a.server_time, b.server_time), ("2026-10-03T09:00:00",) * 2)
        self.assertEqual(a.found, ["2026-10-03T09:00:00"])
        self.assertEqual(b.found, [])

    def test_failed_fetch_lets_next_try(self):
        clock = ServerClock()
        a, b = make_worker(clock), make_worker(clock)
        with mock.patch.object(bot_worker, "get_server_time", side_effect=[None, "2026-10-03T09:00:00"]):
            a._ensure_server_time()             # đọc lỗi -> nhả việc
            self.assertEqual(a.server_time, "")
            b._ensure_server_time()             # máy khác thử lại được
        self.assertEqual(b.server_time, "2026-10-03T09:00:00")

    def test_known_value_never_fetches(self):
        worker = make_worker(ServerClock("known"))
        with mock.patch.object(bot_worker, "get_server_time") as fetch:
            worker._ensure_server_time()
        fetch.assert_not_called()


class SettingsTableTests(unittest.TestCase):
    def setUp(self):
        self.path = Path(tempfile.mkdtemp()) / "t.db"

    def test_old_server_time_column_moves_to_settings(self):
        conn = sqlite3.connect(self.path)
        conn.execute("CREATE TABLE devices (serial TEXT PRIMARY KEY, server TEXT, server_time TEXT, "
                     "bubble_until TEXT, " + ", ".join(f"{c} TEXT NOT NULL DEFAULT '{{}}'"
                                                      for c in database._JSON_COLUMNS)
                     + ", created_at TEXT NOT NULL, updated_at TEXT NOT NULL)")
        conn.execute("INSERT INTO devices (serial, server, server_time, event, created_at, updated_at) "
                     "VALUES ('a', '1', '2026-10-01T09:00:00', ?, 'n', '2026-10-01')",
                     (json.dumps({"kings_path_patrol": {"value": 200}}),))
        conn.execute("INSERT INTO devices (serial, server, server_time, created_at, updated_at) "
                     "VALUES ('b', '1', NULL, 'n', '2026-10-02')")
        conn.commit()
        conn.close()

        db = database.Database(self.path)
        try:
            columns = {row["name"] for row in db.conn.execute("PRAGMA table_info(devices)")}
            self.assertNotIn("server_time", columns)
            self.assertEqual(db.server_time(), "2026-10-01T09:00:00")
            self.assertEqual(db.load_settings("a")["Event"], {"kings_path_patrol": {"value": 200}})
        finally:
            db.close()

    def test_set_server_time_is_shared(self):
        db = database.Database(self.path)
        try:
            self.assertEqual(db.server_time(), "")
            db.set_server_time("2026-10-03T09:00:00")
            self.assertEqual(db.server_time(), "2026-10-03T09:00:00")
            db.set_server_time("2026-10-04T09:00:00")
            self.assertEqual(db.server_time(), "2026-10-04T09:00:00")
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
