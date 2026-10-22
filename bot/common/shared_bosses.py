"""
shared_bosses.py — nhớ các boss đã chia sẻ (share) vào liên minh, theo SERVER và toạ độ X:Y: mọi bot cùng một server dùng chung một danh sách, bot nào đã chia sẻ boss ở toạ độ
đó thì các bot khác (và các lần chạy sau) không chia sẻ lại.

    shared = SharedBosses.for_server("1257")     # cùng server trả cùng một đối tượng (mọi bot / luồng dùng chung)
    if not shared.has(x, y): ...gửi...; shared.add(x, y, name="Zombie", level=1)

Một boss đứng yên tại một toạ độ tới khi bị đánh chết, nên toạ độ là khoá và bản ghi không hết hạn theo thời gian (chỉ khi đặt TTL_HOURS). Lưu ra file
shared_bosses.json trong thư mục dữ liệu của app (cùng chỗ evonybot.db, {server: [bản ghi]}); has() đọc lại file khi nó đổi nên nhiều tiến trình cùng thấy nhau.
"""
import json
import os
import threading
import time
from pathlib import Path

DEFAULT_PATH = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "EvonyBot" / "app" / "shared_bosses.json"   # cùng thư mục với database.DATA_DIR (không import database để khỏi vòng import)
NEAR_KM = 5                          # km: cùng tên / tầng, cách nhau không quá chừng này theo mỗi trục = cùng một boss (toạ độ đọc ở thanh X:Y có thể lệch vài km)
TTL_HOURS = None                     # boss không đổi theo thời gian (đứng yên tới khi bị đánh chết): bản ghi không hết hạn; đặt số giờ để cho hết hạn

_lock = threading.RLock()            # một khoá cho mọi đối tượng: đọc / ghi file và bản ghi trong bộ nhớ đi chung
_instances: dict = {}                # (đường dẫn file, server) -> SharedBosses


class SharedBosses:
    def __init__(self, server: str, path: Path | None = None, ttl_hours: float | None = TTL_HOURS):
        self.server = str(server).strip()
        self.path = Path(path) if path else DEFAULT_PATH
        self.ttl = ttl_hours * 3600 if ttl_hours else None
        self.records: list[dict] = []
        self._mtime = None
        self._refresh()

    @classmethod
    def for_server(cls, server: str, path: Path | None = None) -> "SharedBosses":
        """Danh sách chung của `server`: mọi lần gọi cùng server (và cùng file) trả về cùng một đối tượng."""
        key = (str(path or DEFAULT_PATH), str(server).strip())
        with _lock:
            if key not in _instances:
                _instances[key] = cls(server, path)
            return _instances[key]

    def _read_file(self) -> dict:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    def _fresh(self, records) -> list[dict]:
        now = time.time()
        return [r for r in records if isinstance(r, dict) and "x" in r and "y" in r and (self.ttl is None or now - r.get("time", 0) < self.ttl)]

    def _refresh(self) -> None:
        """Đọc lại bản ghi của server từ file nếu file đã đổi (bot / tiến trình khác vừa ghi)."""
        try:
            mtime = self.path.stat().st_mtime_ns
        except OSError:
            mtime = None
        if mtime != self._mtime:
            self.records = self._fresh(self._read_file().get(self.server, []))
            self._mtime = mtime

    def has(self, x: int, y: int, name: str | None = None, tier: str | None = None) -> bool:
        """Boss ở toạ độ (x, y) của server này đã chia sẻ chưa. Có `name` (và `tier`): boss cùng tên / tầng cách nhau không quá NEAR_KM theo mỗi trục là cùng một boss (thanh toạ độ đọc lệch
        vài km tuỳ lúc camera đã dừng hẳn chưa); không thì phải đúng toạ độ."""
        with _lock:
            self._refresh()
            for r in self._fresh(self.records):
                if r["x"] == x and r["y"] == y:
                    return True
                if name is not None and r.get("name") == name and r.get("tier") == tier and abs(r["x"] - x) <= NEAR_KM and abs(r["y"] - y) <= NEAR_KM:
                    return True
            return False

    def add(self, x: int, y: int, **info) -> None:
        """Ghi boss ở (x, y) đã chia sẻ (kèm thông tin tuỳ ý như name, level, tier) rồi lưu ra file (giữ nguyên bản ghi của các server khác)."""
        with _lock:
            self._refresh()
            self.records = [r for r in self._fresh(self.records) if not (r["x"] == x and r["y"] == y)]
            self.records.append({"x": x, "y": y, "time": time.time(), **info})
            data = self._read_file()
            data[self.server] = self.records
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
            tmp.replace(self.path)
            self._mtime = self.path.stat().st_mtime_ns
