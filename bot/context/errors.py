"""
errors.py — the exceptions that end a run early (not an error).
"""


class BotInterrupted(Exception):
    """Base for the exceptions that end a run early (not an error)."""


class StopRequested(BotInterrupted):
    pass


class TimedOut(BotInterrupted):
    pass


class BossAvailable(BotInterrupted):
    """Yield a secondary activity to a new boss on the same server."""
