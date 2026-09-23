"""
bot_context.py — BotContext: one adbutils device plus the worker's stop
flag and deadline, with the helpers from the mixins.
"""
import threading

import numpy as np

from .device_input import InputMixin
from .flow import FlowMixin
from .screen import ScreenMixin


class BotContext(FlowMixin, InputMixin, ScreenMixin):
    def __init__(self, device, stop_event: threading.Event, deadline: float | None, log):
        self.device = device
        self.serial = device.serial
        self._stop = stop_event
        self._deadline = deadline    # time.monotonic() value, or None for no limit
        self._log = log
        self._templates: dict[str, np.ndarray] = {}
        self._window_size: tuple[int, int] | None = None
        # Every tab's config ({tab title: settings}), for activities that
        # chain into another one (e.g. Battlefield Shop -> Black Market).
        self.settings: dict = {}
