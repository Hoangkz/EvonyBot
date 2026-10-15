import importlib, os
from pathlib import Path
SERIAL = os.environ.get("EVONY_SERIAL", "127.0.0.1:21933")   # máy đang ở màn thành của civ cần đo
CIV = int(os.environ.get("EVONY_CIV", "2"))                   # nền văn minh của máy
import sys, threading, time
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import adbutils, cv2, numpy as np
from bot.city import city_map
from bot.context import BotContext
bot = BotContext(adbutils.adb.device(serial=SERIAL), threading.Event(), None, lambda m: None)
bot.civilization = CIV
for a in sys.argv[2:]:
    dx, dy = map(int, a.split(","))
    city_map.swipe(bot, (dx, dy)); time.sleep(1)
s = city_map.city_screen(bot)
cv2.imwrite(sys.argv[1], s)
for n in city_map.BUILDINGS:
    sc, p = city_map.locate(bot, s, n)
    if p is not None and sc > 0.45: print(f"{n:16s} {sc:.3f} {p}")
