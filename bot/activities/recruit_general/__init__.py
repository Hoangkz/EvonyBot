"""
recruit_general — "Recruit General" activity (chạy một mình, xem bot/activities/constants.py EXCLUSIVE_ACTIVITIES).

- run.py:       entry point, `run(bot, settings)`, and its helpers
- constants.py: image folder, thresholds and waits
"""
from .run import run

__all__ = ["run"]
