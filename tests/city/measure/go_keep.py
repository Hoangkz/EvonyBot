import importlib, os
from pathlib import Path
SERIAL = os.environ.get("EVONY_SERIAL", "127.0.0.1:21933")   # máy đang ở màn thành của civ cần đo
CIV = int(os.environ.get("EVONY_CIV", "2"))                   # nền văn minh của máy
import sys, threading
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import adbutils
from bot.context import BotContext
from bot.activities.daily_activities import common
from bot.activities.daily_activities.gold_levy import TASK
bot = BotContext(adbutils.adb.device(serial=SERIAL), threading.Event(), None, print)
bot.civilization = CIV
print("open_task_or_finish ->", common.open_task_or_finish(bot, TASK))
