"""
Giờ reset server: người dùng chọn ở màn Home ("HH:MM", mặc định 14:00), lưu bảng `settings` của DB, dùng
chung mọi thiết bị (ServerClock); bot không vào game đọc giờ reset nữa.
"""
import json
import os
import sqlite3
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

import database
from bot.daily_reset import DEFAULT_RESET_TIME, done_today, last_reset, reset_clock
from bot.worker.bot_worker import BotWorker
from bot.worker.server_clock import ServerClock


class ResetTimeTests(unittest.TestCase):
    def test_last_reset_today_or_yesterday(self):
        self.assertEqual(last_reset("14:00", datetime(2026, 10, 3, 15, 30)), datetime(2026, 10, 3, 14, 0))
        self.assertEqual(last_reset("14:00", datetime(2026, 10, 3, 14, 0)), datetime(2026, 10, 3, 14, 0))
        self.assertEqual(last_reset("14:00", datetime(2026, 10, 3, 9, 0)), datetime(2026, 10, 2, 14, 0))

    def test_default_and_old_iso(self):
        self.assertEqual(DEFAULT_RESET_TIME, "14:00")
        for value in ("", None, "known", "25:99"):
            self.assertEqual(reset_clock(value), "14:00")
        self.assertEqual(last_reset("", datetime(2026, 10, 3, 15)), datetime(2026, 10, 3, 14, 0))
        # Giá trị cũ dạng ISO (một lần reset bất kỳ) vẫn đọc được: lấy giờ của nó.
        self.assertEqual(reset_clock("2026-09-01T09:30:12"), "09:30")
        self.assertEqual(last_reset("2026-09-01T09:30:12", datetime(2026, 10, 3, 10)), datetime(2026, 10, 3, 9, 30))

    def test_done_today(self):
        now = datetime(2026, 10, 3, 15)
        self.assertTrue(done_today("2026-10-03T14:05:00", "14:00", now))
        self.assertFalse(done_today("2026-10-03T13:55:00", "14:00", now))
        self.assertFalse(done_today(None, "14:00", now))

    def test_server_clock(self):
        clock = ServerClock()
        self.assertEqual(clock.value, "14:00")
        clock.set("08:15")
        self.assertEqual(clock.value, "08:15")
        clock.set("")
        self.assertEqual(clock.value, "14:00")

    def test_worker_never_reads_server_time_in_game(self):
        worker = BotWorker("b", ["x"], {"Initialization": {"server": "1"}}, server_clock=ServerClock("09:00"))
        self.assertFalse(hasattr(worker, "_ensure_server_time"))
        self.assertEqual(worker.server_time, "09:00")


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
            self.assertEqual(db.server_time(), "09:00")
            self.assertEqual(db.load_settings("a")["Event"], {"kings_path_patrol": {"value": 200}})
        finally:
            db.close()

    def test_default_and_set(self):
        db = database.Database(self.path)
        try:
            self.assertEqual(db.server_time(), "14:00")
            db.set_server_time("08:30")
            self.assertEqual(db.server_time(), "08:30")
            self.assertEqual(db.get_setting(database.SERVER_TIME), "08:30")
        finally:
            db.close()


class HomeResetTimeTests(unittest.TestCase):
    """Ô "Reset Time" ở màn Home: mặc định 14:00, đổi thì phát reset_time_changed("HH:MM")."""

    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PyQt5.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def test_picker(self):
        from PyQt5.QtCore import QTime
        from ui.home_view import HomeView
        view = HomeView()
        self.assertEqual(view.reset_time_edit.time().toString("HH:mm"), "14:00")
        changed = []
        view.reset_time_changed.connect(changed.append)
        view.set_reset_time("09:45")          # nạp giá trị đã lưu: không phát tín hiệu
        self.assertEqual(view.reset_time_edit.time().toString("HH:mm"), "09:45")
        self.assertEqual(changed, [])
        view.reset_time_edit.setTime(QTime(16, 30))   # người dùng đổi
        self.assertEqual(changed, ["16:30"])


if __name__ == "__main__":
    unittest.main()
