"""
boss_memory.py — bộ nhớ tọa độ boss của một giả lập.

Mỗi giả lập có một BossMemory riêng, gắn vào BotContext của worker, nên nó
còn qua các lần Join Boss nhường activity khác và mất khi bấm Stop. Flow hiện
chỉ dùng JOINED để chặn theo tọa độ; SKIPPED được giữ để tương thích dữ liệu/test
cũ nhưng không được dùng để bỏ qua boss trong run.py.
"""
import time

JOINED = "joined"       # đã hành quân tới rally của boss này
SKIPPED = "skipped"     # tương thích cũ; run.py không dùng trạng thái này để chặn boss
TTL = 6 * 60            # giây nhớ một toạ độ
MAX_ENTRIES = 256        # chặn bộ nhớ tăng vô hạn nếu OCR liên tục sinh tọa độ sai khác nhau


class BossMemory:
    def __init__(self, ttl: float = TTL):
        self.ttl = ttl
        self._bosses: dict[tuple[int, int], tuple[str, float]] = {}  # coords -> (status, hết hạn)

    def status(self, coords) -> str | None:
        """JOINED / SKIPPED nếu `coords` còn được nhớ, ngược lại None."""
        self._purge()
        entry = self._bosses.get(coords)
        return entry[0] if entry else None

    def mark(self, coords, status: str):
        """Nhớ `coords` với `status` trong TTL giây kể từ bây giờ (None thì bỏ qua)."""
        if coords is None:
            return
        self._purge()
        self._bosses[coords] = (status, time.monotonic() + self.ttl)
        if len(self._bosses) > MAX_ENTRIES:
            oldest = min(self._bosses, key=lambda key: self._bosses[key][1])
            del self._bosses[oldest]

    def _purge(self):
        now = time.monotonic()
        for coords in [c for c, (_, expires) in self._bosses.items() if expires <= now]:
            del self._bosses[coords]
