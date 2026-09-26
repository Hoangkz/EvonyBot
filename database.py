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

Writes never block the caller: they are queued and run on a background
writer thread with its own connection (a commit waits on the disk, which
froze the UI). Reads use the caller's connection and first wait for any
queued writes, so they always see the latest data.
"""
import json
import os
import queue
import shutil
import sqlite3
import threading
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


def _connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    # WAL: readers don't wait for the writer thread, and commits are cheaper.
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


class Database:
    def __init__(self, path: Path = DB_PATH):
        path.parent.mkdir(parents=True, exist_ok=True)
        # First run with the new location: carry over the old database.
        if path == DB_PATH and not path.exists() and _LEGACY_DB_PATH.exists():
            shutil.copy2(_LEGACY_DB_PATH, path)
        self.conn = _connect(path)
        self.conn.executescript(_SCHEMA)
        self.conn.commit()
        # Serials known to be in `devices`, including inserts still queued.
        self._known = {row["serial"] for row in self.conn.execute("SELECT serial FROM devices")}

        self._queue: queue.Queue = queue.Queue()
        self._writer = threading.Thread(
            target=self._write_loop, args=(path,), name="db-writer", daemon=True
        )
        self._writer.start()

    def close(self):
        """Finish every queued write, then close."""
        self._queue.put(None)
        self._writer.join()
        self.conn.close()

    # ---- background writer -------------------------------------------
    def _write(self, job):
        """Queue `job(conn)`; it runs in its own transaction on the writer thread."""
        self._queue.put(job)

    def _write_loop(self, path: Path):
        conn = _connect(path)
        while True:
            job = self._queue.get()
            try:
                if job is None:
                    break
                with conn:
                    job(conn)
            except Exception as e:
                print(f"[Database] write failed: {e}")
            finally:
                self._queue.task_done()
        conn.close()

    def _flush(self):
        """Wait for queued writes (usually none) so a read sees them."""
        self._queue.join()

    # ---- devices -----------------------------------------------------
    def add_device(self, serial: str) -> bool:
        """Insert the device if it's new. Returns True if it was inserted."""
        if serial in self._known:
            return False
        self._known.add(serial)
        now = _now()
        self._write(lambda conn: conn.execute(
            "INSERT OR IGNORE INTO devices (serial, created_at, updated_at) VALUES (?, ?, ?)",
            (serial, now, now),
        ))
        return True

    # ---- settings ----------------------------------------------------
    def save_settings(self, serial: str, settings: dict):
        """Save a DeviceView.get_settings()-style dict (keyed by tab title)."""
        self.save_many_settings({serial: settings})

    def save_many_settings(self, settings_by_serial: dict):
        """save_settings() for several devices ({serial: settings}) in one
        transaction — one commit instead of one per device."""
        now = _now()

        def job(conn):
            for serial, settings in settings_by_serial.items():
                _save_settings(conn, serial, settings, now)

        self._write(job)

    def load_settings(self, serial: str) -> dict:
        """Return saved settings in the same shape DeviceView.set_settings() takes."""
        self._flush()
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
        self._flush()
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
        self._flush()
        rows = self.conn.execute(
            "SELECT task FROM daily_tasks WHERE serial = ? AND enabled = 1 AND done = 0 ORDER BY task",
            (serial,),
        )
        return [r["task"] for r in rows]

    def mark_daily_task_done(self, serial: str, task: str, done: bool = True):
        now = _now()
        self._write(lambda conn: conn.execute(
            """UPDATE daily_tasks SET done = ?, done_at = ?, updated_at = ?
               WHERE serial = ? AND task = ?""",
            (int(done), now if done else None, now, serial, task),
        ))


def _save_settings(conn: sqlite3.Connection, serial: str, settings: dict, now: str):
    conn.execute("UPDATE devices SET updated_at = ? WHERE serial = ?", (now, serial))
    for tab, data in settings.items():
        if tab == INIT_TAB:
            data = {k: v for k, v in data.items() if k != "device_id"}
        if tab == DAILY_TAB:
            _save_daily_tasks(conn, serial, data, now)
            continue
        conn.execute(
            """INSERT INTO device_settings (serial, tab, settings, updated_at)
               VALUES (?, ?, ?, ?)
               ON CONFLICT (serial, tab) DO UPDATE
               SET settings = excluded.settings, updated_at = excluded.updated_at""",
            (serial, tab, json.dumps(data, ensure_ascii=False), now),
        )


def _save_daily_tasks(conn: sqlite3.Connection, serial: str, tasks: dict, now: str):
    # Only `enabled` is updated here; `done` / `done_at` are kept.
    for task, enabled in tasks.items():
        conn.execute(
            """INSERT INTO daily_tasks (serial, task, enabled, updated_at)
               VALUES (?, ?, ?, ?)
               ON CONFLICT (serial, task) DO UPDATE
               SET enabled = excluded.enabled, updated_at = excluded.updated_at""",
            (serial, task, int(bool(enabled)), now),
        )
