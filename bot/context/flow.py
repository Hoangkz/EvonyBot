"""
flow.py — flow control: stop / time-out checks, interruptible sleep, log.
"""
import time

from .errors import BossAvailable, BubbleDue, StopRequested, TimedOut


class FlowMixin:
    def check(self):
        if self._stop.is_set():
            raise StopRequested()
        # Bubble ưu tiên hơn mọi activity: tới hạn là nhường ngay.
        if self._bubble_due_at is not None and time.monotonic() >= self._bubble_due_at:
            raise BubbleDue()
        if self._boss_interrupt_enabled and self._boss_event.is_set():
            raise BossAvailable()
        if self._deadline is not None and time.monotonic() >= self._deadline:
            raise TimedOut()

    def sleep(self, seconds: float):
        """Like time.sleep, but wakes up immediately on Stop / time-out."""
        end = time.monotonic() + seconds
        while True:
            self.check()
            remaining = end - time.monotonic()
            if remaining <= 0:
                return
            self._stop.wait(min(remaining, 0.2))

    def log(self, message: str):
        self._log(message)
