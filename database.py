"""
database.py — SQLite persistence for devices and their configuration.

Tables:
  devices          one row per ADB serial.
  device_settings  one JSON blob per (device, tab) — every tab except
                   Daily Activities.
  daily_tasks      Daily Activities split into one row per task, so we
                   know whether each task is enabled and whether it has
                   been done today (`done` / `done_at`). Resetting `done`
                   at the start of a new day is handled elsewhere (TODO).
"""
import json
import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

# %LOCALAPPDATA%\EvonyBot\evonybot.db — same place whether run from source or
# installed (the installer also puts the app in %LOCALAPPDATA%\EvonyBot and
# never ships/overwrites the database, so it survives upgrades and uninstall).
DATA_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "EvonyBot"
DB_PATH = DATA_DIR / "evonybot.db"
# Where the database used to live (next to this file).
_LEGACY_DB_PATH = Path(__file__).resolve().parent / "evonybot.db"

DAILY_TAB = "Daily Activities"
INIT_TAB = "Initialization"  # device id is not stored, only the selected activities

_SCHEMA = """
CREATE TABLE IF NOT EXISTS devices (
    serial      TEXT PRIMARY KEY,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS device_settings (
    serial      TEXT NOT NULL REFERENCES devices(serial) ON DELETE CASCADE,
    tab         TEXT NOT NULL,
    settings    TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    PRIMARY KEY (serial, tab)
);

CREATE TABLE IF NOT EXISTS daily_tasks (
    serial      TEXT NOT NULL REFERENCES devices(serial) ON DELETE CASCADE,
    task        TEXT NOT NULL,
    enabled     INTEGER NOT NULL DEFAULT 0,
    done        INTEGER NOT NULL DEFAULT 0,
    done_at     TEXT,
    updated_at  TEXT NOT NULL,
    PRIMARY KEY (serial, task)
);
"""


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class Database:
    def __init__(self, path: Path = DB_PATH):
        path.parent.mkdir(parents=True, exist_ok=True)
        # First run with the new location: carry over the old database.
        if path == DB_PATH and not path.exists() and _LEGACY_DB_PATH.exists():
            shutil.copy2(_LEGACY_DB_PATH, path)
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(_SCHEMA)
        self.conn.commit()

    def close(self):
        self.conn.close()

    # ---- devices -----------------------------------------------------
    def add_device(self, serial: str) -> bool:
        """Insert the device if it's new. Returns True if it was inserted."""
        now = _now()
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO devices (serial, created_at, updated_at) VALUES (?, ?, ?)",
            (serial, now, now),
        )
        self.conn.commit()
        return cur.rowcount > 0

    # ---- settings ----------------------------------------------------
    def save_settings(self, serial: str, settings: dict):
        """Save a DeviceView.get_settings()-style dict (keyed by tab title)."""
        now = _now()
        with self.conn:
            self.conn.execute(
                "UPDATE devices SET updated_at = ? WHERE serial = ?", (now, serial)
            )
            for tab, data in settings.items():
                if tab == INIT_TAB:
                    data = {k: v for k, v in data.items() if k != "device_id"}
                if tab == DAILY_TAB:
                    self._save_daily_tasks(serial, data, now)
                    continue
                self.conn.execute(
                    """INSERT INTO device_settings (serial, tab, settings, updated_at)
                       VALUES (?, ?, ?, ?)
                       ON CONFLICT (serial, tab) DO UPDATE
                       SET settings = excluded.settings, updated_at = excluded.updated_at""",
                    (serial, tab, json.dumps(data, ensure_ascii=False), now),
                )

    def _save_daily_tasks(self, serial: str, tasks: dict, now: str):
        # Only `enabled` is updated here; `done` / `done_at` are kept.
        for task, enabled in tasks.items():
            self.conn.execute(
                """INSERT INTO daily_tasks (serial, task, enabled, updated_at)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT (serial, task) DO UPDATE
                   SET enabled = excluded.enabled, updated_at = excluded.updated_at""",
                (serial, task, int(bool(enabled)), now),
            )

    def load_settings(self, serial: str) -> dict:
        """Return saved settings in the same shape DeviceView.set_settings() takes."""
        result = {
            row["tab"]: json.loads(row["settings"])
            for row in self.conn.execute(
                "SELECT tab, settings FROM device_settings WHERE serial = ?", (serial,)
            )
        }
        daily = {
            row["task"]: bool(row["enabled"])
            for row in self.conn.execute(
                "SELECT task, enabled FROM daily_tasks WHERE serial = ?", (serial,)
            )
        }
        if daily:
            result[DAILY_TAB] = daily
        return result

    # ---- daily task progress -----------------------------------------
    def get_daily_tasks(self, serial: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT task, enabled, done, done_at FROM daily_tasks WHERE serial = ? ORDER BY task",
            (serial,),
        )
        return [
            {"task": r["task"], "enabled": bool(r["enabled"]),
             "done": bool(r["done"]), "done_at": r["done_at"]}
            for r in rows
        ]

    def pending_daily_tasks(self, serial: str) -> list[str]:
        """Enabled tasks that haven't been done yet."""
        rows = self.conn.execute(
            "SELECT task FROM daily_tasks WHERE serial = ? AND enabled = 1 AND done = 0 ORDER BY task",
            (serial,),
        )
        return [r["task"] for r in rows]

    def mark_daily_task_done(self, serial: str, task: str, done: bool = True):
        now = _now()
        with self.conn:
            self.conn.execute(
                """UPDATE daily_tasks SET done = ?, done_at = ?, updated_at = ?
                   WHERE serial = ? AND task = ?""",
                (int(done), now if done else None, now, serial, task),
            )
