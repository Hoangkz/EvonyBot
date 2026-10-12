"""
guards.py — Bubble (khiên) và Auto Times Out: hai việc ưu tiên hơn mọi nhiệm vụ, tách khỏi BotWorker.

Mỗi guard `ensure()` xử lý việc của mình nếu tới hạn (vào game dùng bubble / đóng game), rồi hẹn `ctx` ngắt mọi thứ đang chạy
đúng lúc cần xử lý lần sau (ctx._bubble_due_at / ctx._restart_due_at; `ctx.check()` ném BubbleDue / RestartDue). `Guards.call`
bao quanh một lời gọi: lo guard trước, tới hạn giữa chừng thì xử lý rồi gọi lại từ đầu.

Khi đang xử lý, guard tạm tắt deadline 120 giây và ngắt-bởi-boss (`_quiet`) để bước của nó không bị cắt ngang, rồi khôi phục.
Nhiệm vụ must_finish: `Guards.hold()` hoãn cả hai tới khi xong (`Guards.release()`).
"""
import time
from contextlib import contextmanager
from datetime import datetime, timedelta

from ..common import GAME_PACKAGE, NotEnoughGems, keep_bubble
from ..context.errors import BubbleDue, ResetDue, RestartDue
from ..daily_reset import last_reset

BUBBLE = "Bubble"
BUBBLE_RENEW_BEFORE = 7200   # bubble còn <= 2 tiếng -> dùng bubble mới
BUBBLE_RETRY = 300           # đọc / dùng bubble không được -> 5 phút sau thử lại
AUTO_RESTART = "Auto Times Out"
RESTART_WAIT = 3             # giây chờ sau khi đóng game


def _seconds_until(iso) -> float | None:
    """Số giây từ bây giờ tới thời điểm ISO (giờ máy); None nếu rỗng / sai định dạng."""
    try:
        return (datetime.fromisoformat(iso) - datetime.now()).total_seconds()
    except (TypeError, ValueError):
        return None


@contextmanager
def _quiet(ctx):
    """Tạm tắt deadline và ngắt-bởi-boss (bước của guard không bị cắt ngang); khôi phục khi ra. Mốc hẹn bubble / restart
    cũng tạm xoá; mỗi guard tự hẹn lại sau đó."""
    saved = (ctx._deadline, ctx._boss_interrupt_enabled, ctx._bubble_due_at, ctx._reset_due_at)
    ctx._deadline, ctx._boss_interrupt_enabled = None, False
    ctx._bubble_due_at = ctx._restart_due_at = ctx._reset_due_at = None
    try:
        yield saved[2]
    finally:
        ctx._deadline, ctx._boss_interrupt_enabled, ctx._reset_due_at = saved[0], saved[1], saved[3]


class BubbleGuard:
    """Tích Bubble ở tab Initialization: luôn giữ bubble. `hooks` có found(giây), disabled(), activity(nhãn), log, record."""

    def __init__(self, get_ctx, init: dict, hooks, guards):
        self._ctx = get_ctx
        self._hooks = hooks
        self._guards = guards
        self.enabled = bool(init.get("bubble"))
        self.type = init.get("bubble_type") or "24h"
        self.expiry = None       # time.monotonic() lúc bubble hết; None = chưa biết
        self.next_check = 0.0    # time.monotonic() lần xử lý bubble tiếp theo
        # Thời điểm bubble hết đã lưu trong DB: còn hơn 2 tiếng thì không vào game kiểm tra, hẹn lúc còn 2 tiếng.
        left = _seconds_until(init.get("bubble_until"))
        if left is not None and left > 0:
            self.expiry = time.monotonic() + left
            self.next_check = self.expiry - BUBBLE_RENEW_BEFORE

    def left(self) -> float:
        return self.expiry - time.monotonic()

    def _set_remaining(self, seconds: float):
        seconds = max(0, seconds)
        self.expiry = time.monotonic() + seconds
        self._hooks.found(int(seconds))

    def ensure(self) -> bool:
        """Chưa biết thời gian -> đi lấy; còn <= 2 tiếng -> dùng bubble mới. Rồi hẹn ctx ngắt đúng lúc cần xử lý lần
        sau. True nếu vừa thao tác trong game (màn hình đã đổi)."""
        if not self.enabled:
            return False
        ctx = self._ctx()
        if self._guards.held:
            ctx._bubble_due_at = None
            return False
        if time.monotonic() < self.next_check:
            ctx._bubble_due_at = self.next_check
            return False

        with _quiet(ctx):
            try:
                self._hooks.activity(BUBBLE)
                # Vào game đọc lại cả khi đã biết: có thể bubble đã được gia hạn tay.
                try:
                    remaining = keep_bubble(ctx, self.type, BUBBLE_RENEW_BEFORE)
                except NotEnoughGems:
                    # Không mua được thì thôi giữ bubble: bỏ tích ở UI, không thử lại nữa.
                    self._hooks.record(f"Bubble: không đủ kim cương mua {self.type}, bỏ tích Bubble")
                    self.enabled = False
                    self._hooks.disabled()
                    return True
                if remaining is None:
                    self._hooks.log("Bubble: không đọc được thời gian, sẽ thử lại sau")
                else:
                    self._set_remaining(remaining)
                    if remaining <= BUBBLE_RENEW_BEFORE:
                        self._hooks.log(f"Bubble: chưa dùng được bubble {self.type}, sẽ thử lại sau")
            finally:
                # Còn > 2 tiếng -> hẹn lúc còn đúng 2 tiếng; không thì thử lại sau BUBBLE_RETRY.
                if self.expiry is not None and self.left() > BUBBLE_RENEW_BEFORE:
                    self.next_check = self.expiry - BUBBLE_RENEW_BEFORE
                else:
                    self.next_check = time.monotonic() + BUBBLE_RETRY
                # Đã bỏ tích (không đủ kim cương) thì không hẹn nữa.
                ctx._bubble_due_at = self.next_check if self.enabled else None
        return True


class RestartGuard:
    """Auto Times Out (phút, màn Home; 0 = tắt): chạy đủ số phút kể từ lần đóng game trước -> đóng game (bot đang chạy tự
    mở lại qua go_home)."""

    def __init__(self, get_ctx, auto_timeout, hooks, guards):
        self._ctx = get_ctx
        self._minutes = auto_timeout   # hàm trả số phút (đọc lại mỗi lần, đổi là dùng ngay)
        self._hooks = hooks
        self._guards = guards
        self.last = time.monotonic()

    def ensure(self) -> bool:
        """Chưa tới giờ thì hẹn ctx ngắt đúng lúc. True nếu vừa đóng game (màn hình đã đổi)."""
        ctx = self._ctx()
        minutes = self._minutes()
        if self._guards.held or minutes <= 0:
            ctx._restart_due_at = None
            return False
        due = self.last + minutes * 60
        if time.monotonic() < due:
            ctx._restart_due_at = due
            return False

        self.close_game(f"Auto Times Out: đã chạy {minutes} phút")
        return True

    def close_game(self, reason: str):
        """Đóng game (bot tự mở lại khi chạy tiếp, qua go_home), rồi tính lại mốc Auto Times Out từ lúc này. Dùng cho Auto
        Times Out và cho mốc reset server (Guards.restart_game)."""
        ctx = self._ctx()
        with _quiet(ctx) as bubble_due:
            try:
                self._hooks.activity(AUTO_RESTART)
                self._hooks.record(f"{reason}, đóng game")
                # Chỉ đóng game; activity chạy sau thấy launcher thì tự mở lại (go_home).
                ctx.shell(f"am force-stop {GAME_PACKAGE}")
                ctx.sleep(RESTART_WAIT)
            finally:
                ctx._bubble_due_at = bubble_due
                self.last = time.monotonic()
                minutes = self._minutes()
                ctx._restart_due_at = self.last + minutes * 60 if minutes > 0 else None


class Guards:
    """Bubble + Auto Times Out của một thiết bị."""

    def __init__(self, get_ctx, init: dict, auto_timeout, hooks, server_time=lambda: ""):
        self._get_ctx = get_ctx
        self._hooks = hooks
        self._server_time = server_time   # hàm trả giờ reset server "HH:MM" (đọc lại mỗi lần, đổi là dùng ngay)
        # Mốc reset server đã xử lý (đã tắt game bật lại): worker đặt lúc bắt đầu chạy nên vừa Start không đóng game.
        self.reset_handled = datetime.min
        self.held = False   # đang chạy nhiệm vụ must_finish: hoãn bubble / Auto Times Out tới khi xong
        self.bubble = BubbleGuard(get_ctx, init, hooks, self)
        self.restart = RestartGuard(get_ctx, auto_timeout, hooks, self)

    def hold(self):
        """Nhiệm vụ must_finish bắt đầu: bubble / Auto Times Out vừa lo xong -> hoãn, gỡ mốc hẹn."""
        self.held = True
        ctx = self._get_ctx()
        ctx._bubble_due_at = ctx._restart_due_at = None

    def release(self):
        self.held = False

    def arm_reset(self):
        """Hẹn ctx ngắt (ResetDue) đúng mốc reset server kế tiếp — kể cả khi đang chạy nhiệm vụ must_finish."""
        now = datetime.now()
        next_reset = last_reset(self._server_time(), now) + timedelta(days=1)
        self._get_ctx()._reset_due_at = time.monotonic() + (next_reset - now).total_seconds()

    def restart_for_reset(self, reset_at: datetime) -> bool:
        """Tới mốc reset server `reset_at`: tắt game rồi để bot bật lại (đến mốc reset chỉ làm một lần). False nếu mốc này đã
        xử lý rồi."""
        if reset_at <= self.reset_handled:
            return False
        self.reset_handled = reset_at
        self.restart.close_game("Tới mốc reset server")
        return True

    def call(self, label, fn, *args):
        """Gọi fn sau khi lo xong bubble rồi Auto Times Out. Tới hạn giữa chừng (BubbleDue / RestartDue) -> xử lý rồi
        gọi lại fn từ đầu."""
        while True:
            self.arm_reset()
            acted = self.bubble.ensure()
            acted = self.restart.ensure() or acted
            if acted and label:
                self._hooks.activity(label)
            try:
                return fn(*args)
            except BubbleDue:
                self._hooks.log(f"Bubble tới hạn; xử lý bubble rồi làm lại {label or 'bước đang dở'}")
            except RestartDue:
                self._hooks.log(f"Tới giờ Auto Times Out; đóng game rồi làm lại {label or 'bước đang dở'}")
            except ResetDue:
                self._hooks.log(f"Tới mốc reset server; tắt game bật lại rồi làm lại {label or 'bước đang dở'}")
                self.restart_for_reset(last_reset(self._server_time()))
