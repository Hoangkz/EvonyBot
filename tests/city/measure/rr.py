"""rr.py FROM TO [fromkeep] — chay dung ROUTES[(FROM,TO)] cua civ CIV, in lech cua TO so voi tam (cong ANCHOR_SHIFT)"""
import importlib, os
from pathlib import Path
SERIAL = os.environ.get("EVONY_SERIAL", "127.0.0.1:21933")   # máy đang ở màn thành của civ cần đo
CIV = int(os.environ.get("EVONY_CIV", "2"))                   # nền văn minh của máy
import sys, threading, time
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import adbutils
from bot.city import city_map
t = importlib.import_module(f"bot.city.civ{CIV}.city_tour")
from bot.context import BotContext
from bot.activities.daily_activities import common
from bot.activities.daily_activities.gold_levy import TASK
bot = BotContext(adbutils.adb.device(serial=SERIAL), threading.Event(), None, lambda m: None)
bot.civilization = CIV
if "fromkeep" in sys.argv: print("go keep:", common.open_task_or_finish(bot, TASK), flush=True)
a, b = sys.argv[1], sys.argv[2]
for f in t.ROUTES[(a, b)]:
    city_map.swipe(bot, f); time.sleep(1.2)
s = city_map.city_screen(bot)
sc, p = city_map.locate(bot, s, b)
sh = t.ANCHOR_SHIFT.get(b, (0, 0))
print(f"{a}->{b}: {sc:.3f} {p} lech so voi tam+anchor {None if p is None else (p[0]-197-sh[0], p[1]-345-sh[1])}", flush=True)
