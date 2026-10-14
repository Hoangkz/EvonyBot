import importlib, os
from pathlib import Path
SERIAL = os.environ.get("EVONY_SERIAL", "127.0.0.1:21933")   # máy đang ở màn thành của civ cần đo
CIV = int(os.environ.get("EVONY_CIV", "2"))                   # nền văn minh của máy
import sys, threading, time, os, math, random
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import adbutils, cv2
from bot.city import city_map
t = importlib.import_module(f"bot.city.civ{CIV}.city_tour")
from bot.context import BotContext
from bot.activities.daily_activities import common
from bot.activities.daily_activities.gold_levy import TASK
bot = BotContext(adbutils.adb.device(serial=SERIAL), threading.Event(), None, lambda m: None)
bot.civilization = CIV
V = {d['plot']: d['view'] for d in t.DATA}; N = {d['plot']: next(v for k, v in d.items() if k.startswith('seen_')) for d in t.DATA}
def go(a, b):
    fx, fy = V[b][0] - a[0], V[b][1] - a[1]
    n = max(math.ceil(abs(fx) / 320), math.ceil(abs(fy) / 260), 1)
    for _ in range(n):
        city_map.swipe(bot, (round(fx / n), round(fy / n))); time.sleep(1.5)
def report(k):
    s = city_map.city_screen(bot)
    cv2.imwrite(os.environ["TEMP"].replace(chr(92), "/") + f"/pair_{k}.png", s)
    hits = []
    for n in city_map.BUILDINGS:
        sc, p = city_map.locate(bot, s, n)
        if p is not None and sc >= 0.5 and n != "stables" and n != "battlefield": hits.append(f"{n} {sc:.2f} ({p[0]-197:+d},{p[1]-345:+d})")
    return "; ".join(hits) or "-"
for pair in sys.argv[1:]:
    a, b = map(int, pair.split("-"))
    common.open_task_or_finish(bot, TASK)           # ve Thanh chinh
    go((0, 0), a)                                   # keep -> a
    print(f"  đang ở ô {a}: {report(f'{a}_start')}", flush=True)
    go(V[a], b)                                     # a -> b theo duong thang
    print(f"{a} -> {b} ({N[b]}): {report(f'{a}to{b}')}", flush=True)
