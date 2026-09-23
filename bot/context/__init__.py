"""
context — what an activity gets to talk to the device with.

BotContext wraps one adbutils device plus the worker's stop flag and
deadline. Every helper calls `check()` first, so an activity stops as
soon as the user presses Stop or the auto time-out is reached, without
having to test for it itself.

- bot_context: BotContext, built from the mixins below
- flow: check / sleep / log
- device_input: tap / swipe / back / shell / window_size
- screen: screenshot / find / find_all / wait_for / tap_image
- errors: the exceptions that end a run early
- templates: where template images live
"""
from .bot_context import BotContext
from .errors import BotInterrupted, StopRequested, TimedOut
from .templates import DEFAULT_THRESHOLD, TEMPLATE_DIR

__all__ = ["BotContext", "BotInterrupted", "StopRequested", "TimedOut",
           "DEFAULT_THRESHOLD", "TEMPLATE_DIR"]
