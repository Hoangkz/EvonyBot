"""
boss_memory.py — BossMemory: toạ độ boss mà một giả lập đã tham gia hoặc đã bỏ
qua, để khi thấy lại trong danh sách War thì không kiểm tra / Join nữa.

Mỗi giả lập có một BossMemory riêng, gắn vào BotContext của worker, nên nó
còn qua các lần Join Boss nhường activity khác và mất khi bấm Stop. Mỗi toạ
độ tự hết hạn sau TTL (boss đã chết, có thể có boss mới ở cùng chỗ).
"""
import time

JOINED = "joined"       # đã hành quân tới rally của boss này
SKIPPED = "skipped"     # không tham gia (chữ Join đỏ, boss bị cấu hình skip)
TTL = 6 * 60            # giây nhớ một toạ độ


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
        if coords is not None:
            self._bosses[coords] = (status, time.monotonic() + self.ttl)

    def _purge(self):
        now = time.monotonic()
        for coords in [c for c, (_, expires) in self._bosses.items() if expires <= now]:
            del self._bosses[coords]
