"""
database.py — SQLite persistence for devices and their configuration.

Table `devices`: one row per ADB serial. Besides the device columns
(server nhập ở tab Initialization, bubble_until, timestamps) every tab has
its own column holding that tab's settings as JSON (see TAB_COLUMNS).
Table `settings`: cài đặt chung mọi thiết bị ({key: value}), VD SERVER_TIME — giờ reset server "HH:MM"
người dùng chọn ở màn Home (mặc định 14:00; DB cũ có cột devices.server_time thì chuyển sang đây rồi xoá cột).
Daily Activities stores {task: enabled}; which tasks are done today lives
in `daily_done` ({task: done_at}) so saving the tab never clears it.
Nothing is reset at a new day: a task counts as done only while its done_at
is after the latest server reset (bot.daily_reset.done_today).

A database in the old layout (device_settings / daily_tasks tables) is
discarded and recreated empty.

Writes never block the caller: they are queued and run on a background
writer thread with its own connection (a commit waits on the disk, which
froze the UI). Reads use the caller's connection and first wait for any
queued writes, so they always see the latest data.
"""
import json
import os
import queue
import sqlite3
import threading
from datetime import datetime
from pathlib import Path

from bot.daily_reset import done_today, reset_clock

# %LOCALAPPDATA%\EvonyBot\evonybot.db — same place whether run from source or
# installed (the installer also puts the app in %LOCALAPPDATA%\EvonyBot and
# never ships/overwrites the database, so it survives upgrades and uninstall).
DATA_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "EvonyBot"
DB_PATH = DATA_DIR / "evonybot.db"

DAILY_TAB = "Daily Activities"
INIT_TAB = "Initialization"  # device id is not stored; server goes to devices.server
# Key trong bảng `settings`: giờ reset server "HH:MM" (chọn ở màn Home), dùng chung mọi thiết bị.
SERVER_TIME = "server_time"

# Tab title -> column of `devices` holding that tab's settings JSON.
TAB_COLUMNS = {
    "Initialization": "initialization",
    "Join Monster War": "join_monster_war",
    "Alliance Capacity": "alliance_capacity",
    "Daily Activities": "daily_activities",
    "Open Gift Box": "open_gift_box",
    "Black Market": "black_market",
    "Event": "event",
    "Battlefield Shop": "battlefield_shop",
}
_JSON_COLUMNS = [*TAB_COLUMNS.values(), "daily_done"]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS devices (
    serial      TEXT PRIMARY KEY,
    server      TEXT,
    bubble_until TEXT,
    {json_columns},
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS settings (
    key         TEXT PRIMARY KEY,
    value       TEXT,
    updated_at  TEXT NOT NULL
);
""".format(json_columns=",\n    ".join(f"{c} TEXT NOT NULL DEFAULT '{{}}'" for c in _JSON_COLUMNS))


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    # WAL: readers don't wait for the writer thread, and commits are cheaper.
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


def _reset_old_layout(conn: sqlite3.Connection):
    """Drop every table of an old-layout database so _SCHEMA starts fresh."""
    tables = {row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(devices)")}
    if tables & {"device_settings", "daily_tasks"} or (columns and not set(_JSON_COLUMNS) <= columns):
        for table in ("device_settings", "daily_tasks", "devices"):
            conn.execute(f"DROP TABLE IF EXISTS {table}")


# Key nhiệm vụ đã đổi tên (bot/worker/priority.json): key cũ -> key mới. Đổi trong cột `event`
# (cấu hình tab Event) và `daily_done` (kể cả "<key>_locked") của DB cũ, để không mất cấu hình / tiến độ.
KEY_RENAMES = {old: f"gather_troops_{old}" for old in
               ("ground_troop", "mounted_troop", "ranged_troop", "siege_machine", "defense_force")}


def _rename_keys(conn: sqlite3.Connection):
    """Đổi key cũ (KEY_RENAMES) sang key mới trong cột `event` và `daily_done`."""
    def renamed(data: dict) -> dict:
        out = {}
        for key, value in data.items():
            base, suffix = (key[:-len("_locked")], "_locked") if key.endswith("_locked") else (key, "")
            new = KEY_RENAMES.get(base)
            out[new + suffix if new and (new + suffix) not in data else key] = value
        return out

    for row in conn.execute("SELECT serial, event, daily_done FROM devices").fetchall():
        event, done = json.loads(row["event"]), json.loads(row["daily_done"])
        new_event, new_done = renamed(event), renamed(done)
        if new_event != event or new_done != done:
            conn.execute("UPDATE devices SET event = ?, daily_done = ? WHERE serial = ?",
                         (json.dumps(new_event, ensure_ascii=False),
                          json.dumps(new_done, ensure_ascii=False), row["serial"]))


def _move_server_time(conn: sqlite3.Connection):
    """DB cũ có cột devices.server_time: lấy giá trị đầu tiên khác rỗng làm SERVER_TIME chung (nếu
    bảng settings chưa có) rồi xoá cột."""
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(devices)")}
    if "server_time" not in columns:
        return
    row = conn.execute("SELECT server_time FROM devices WHERE server_time IS NOT NULL AND server_time != '' "
                       "ORDER BY updated_at DESC LIMIT 1").fetchone()
    if row is not None:
        conn.execute("INSERT OR IGNORE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
                     (SERVER_TIME, row["server_time"], _now()))
    conn.execute("ALTER TABLE devices DROP COLUMN server_time")


def _add_missing_columns(conn: sqlite3.Connection):
    """Thêm cột mới vào DB cũ mà không xoá dữ liệu."""
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(devices)")}
    if "bubble_until" not in columns:
        conn.execute("ALTER TABLE devices ADD COLUMN bubble_until TEXT")


class Database:
    def __init__(self, path: Path = DB_PATH):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = _connect(path)
        _reset_old_layout(self.conn)
        self.conn.executescript(_SCHEMA)
        _add_missing_columns(self.conn)
        _move_server_time(self.conn)
        _rename_keys(self.conn)
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

    def _row(self, serial: str):
        self._flush()
        return self.conn.execute("SELECT * FROM devices WHERE serial = ?", (serial,)).fetchone()

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

    def set_server(self, serial: str, server: str):
        """Lưu server của thiết bị (rỗng -> NULL)."""
        now = _now()
        self._write(lambda conn: conn.execute(
            "UPDATE devices SET server = ?, updated_at = ? WHERE serial = ?",
            (server or None, now, serial),
        ))

    # ---- settings chung -----------------------------------------------
    def get_setting(self, key: str, default: str = "") -> str:
        """Giá trị cài đặt chung `key` (bảng settings), hoặc `default` nếu chưa có."""
        self._flush()
        row = self.conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row is not None and row["value"] is not None else default

    def set_setting(self, key: str, value: str):
        """Lưu cài đặt chung `key` (rỗng -> NULL)."""
        now = _now()
        self._write(lambda conn: conn.execute(
            "INSERT INTO settings (key, value, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at",
            (key, value or None, now),
        ))

    def server_time(self) -> str:
        """Giờ reset server "HH:MM" (chọn ở màn Home) dùng chung mọi thiết bị; chưa có / giá trị ISO cũ
        -> đổi qua bot.daily_reset.reset_clock (mặc định 14:00)."""
        return reset_clock(self.get_setting(SERVER_TIME))

    def set_server_time(self, server_time: str):
        """Lưu giờ reset server "HH:MM", chung mọi thiết bị."""
        self.set_setting(SERVER_TIME, reset_clock(server_time))

    def set_bubble_until(self, serial: str, bubble_until: str):
        """Lưu thời điểm bubble hết (ISO theo giờ máy; rỗng -> NULL = chưa biết)."""
        now = _now()
        self._write(lambda conn: conn.execute(
            "UPDATE devices SET bubble_until = ?, updated_at = ? WHERE serial = ?",
            (bubble_until or None, now, serial),
        ))

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
        row = self._row(serial)
        if row is None:
            return {}
        result = {tab: json.loads(row[column]) for tab, column in TAB_COLUMNS.items()}
        result = {tab: data for tab, data in result.items() if data}
        result.setdefault(INIT_TAB, {})["server"] = row["server"] or ""
        result[INIT_TAB]["bubble_until"] = row["bubble_until"] or ""
        return result

    # ---- daily task progress -----------------------------------------
    def get_daily_tasks(self, serial: str) -> list[dict]:
        row = self._row(serial)
        if row is None:
            return []
        enabled = json.loads(row["daily_activities"])
        done = json.loads(row["daily_done"])
        server_time = self.server_time()
        return [
            {"task": task, "enabled": bool(enabled.get(task)),
             "done": done_today(done.get(task), server_time), "done_at": done.get(task)}
            for task in sorted(enabled.keys() | done.keys())
        ]

    def daily_done(self, serial: str) -> dict:
        """Raw {task: done_at} (có cả ngày cũ); người dùng tự so với mốc reset."""
        row = self._row(serial)
        return json.loads(row["daily_done"]) if row is not None else {}

    def pending_daily_tasks(self, serial: str) -> list[str]:
        """Enabled tasks that haven't been done yet."""
        return [t["task"] for t in self.get_daily_tasks(serial) if t["enabled"] and not t["done"]]

    def mark_daily_task_done(self, serial: str, task: str, done: bool = True):
        now = _now()

        def job(conn):
            row = conn.execute("SELECT daily_done FROM devices WHERE serial = ?", (serial,)).fetchone()
            if row is None:
                return
            progress = json.loads(row["daily_done"])
            if done:
                progress[task] = now
            else:
                progress.pop(task, None)
            conn.execute(
                "UPDATE devices SET daily_done = ?, updated_at = ? WHERE serial = ?",
                (json.dumps(progress, ensure_ascii=False), now, serial),
            )

        self._write(job)


def _save_settings(conn: sqlite3.Connection, serial: str, settings: dict, now: str):
    conn.execute("UPDATE devices SET updated_at = ? WHERE serial = ?", (now, serial))
    for tab, data in settings.items():
        column = TAB_COLUMNS.get(tab)
        if column is None:
            continue
        if tab == INIT_TAB:
            # Server lưu ở cột devices.server; chỉ cập nhật khi dữ liệu có key này
            # (Apply ALL bỏ key server nên không ghi đè server của máy khác).
            if "server" in data:
                conn.execute("UPDATE devices SET server = ? WHERE serial = ?",
                             (data["server"] or None, serial))
            # bubble_until chỉ được ghi qua set_*, không sao chép qua Apply ALL.
            data = {k: v for k, v in data.items()
                    if k not in ("device_id", "server", "server_time", "bubble_until")}
        conn.execute(
            f"UPDATE devices SET {column} = ? WHERE serial = ?",
            (json.dumps(data, ensure_ascii=False), serial),
        )
