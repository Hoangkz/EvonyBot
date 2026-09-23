"""
worker — one bot thread per device, plus the manager that owns them.

- bot_worker: BotWorker runs the device's selected activities in a loop on
  its own QThread (its `run`) until it is stopped. Each activity lives in
  its own module under bot/activities/ (see ACTIVITIES there).
- manager: BotManager keeps one worker per device and re-emits the
  workers' signals, so the UI only has to connect to the manager.
- status: the status texts shown for a device.
"""
from .bot_worker import BotWorker
from .manager import BotManager
from .status import (STATUS_ERROR, STATUS_IDLE, STATUS_RUNNING, STATUS_STOPPED,
                     STATUS_STOPPING)

__all__ = ["BotWorker", "BotManager", "STATUS_IDLE", "STATUS_RUNNING",
           "STATUS_STOPPING", "STATUS_STOPPED", "STATUS_ERROR"]
