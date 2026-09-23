"""
flow.py — flow control: stop / time-out checks, interruptible sleep, log.
"""
import time

from .errors import StopRequested, TimedOut


class FlowMixin:
    def check(self):
        if self._stop.is_set():
            raise StopRequested()
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
