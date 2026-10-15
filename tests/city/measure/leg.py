"""leg.py FROM TO TOTALDX TOTALDY N [fromkeep] — vuot N cu bang nhau, tim TO, bu toi khi lech<=12, in route cuoi + toa do"""
import importlib, os
from pathlib import Path
SERIAL = os.environ.get("EVONY_SERIAL", "127.0.0.1:21933")   # máy đang ở màn thành của civ cần đo
CIV = int(os.environ.get("EVONY_CIV", "2"))                   # nền văn minh của máy
import sys, threading, time, os
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import adbutils, cv2
from bot.city import city_map
from bot.context import BotContext
from bot.activities.daily_activities import common
from bot.activities.daily_activities.gold_levy import TASK
frm, to = sys.argv[1], sys.argv[2]
tx, ty, n = int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
bot = BotContext(adbutils.adb.device(serial=SERIAL), threading.Event(), None, lambda m: None)
bot.civilization = CIV
if "fromkeep" in sys.argv:
    print("go keep:", common.open_task_or_finish(bot, TASK), flush=True)
def look(tag):
    s = city_map.city_screen(bot)
    cv2.imwrite(os.environ["TEMP"].replace(chr(92), "/") + f"/leg_{to}_{tag}.png", s)
    sc, p = city_map.locate(bot, s, to)
    return sc, p
step = (round(tx / n), round(ty / n))
for _ in range(n):
    city_map.swipe(bot, step); time.sleep(1.2)
total = [step[0] * n, step[1] * n]
sc, p = look("a")
print(f"sau {n} cu {step}: {to} {sc:.3f} {p} lech {None if p is None else (p[0]-197, p[1]-345)}", flush=True)
for i in range(3):
    if p is None or (abs(p[0] - 197) <= 12 and abs(p[1] - 345) <= 12): break
    c = (-(p[0] - 197), -(p[1] - 345))
    city_map.swipe(bot, c); time.sleep(1.2)
    total[0] += c[0]; total[1] += c[1]
    sc, p = look(f"b{i}")
    print(f"  bu {c}: {to} {sc:.3f} {p} lech {None if p is None else (p[0]-197, p[1]-345)}", flush=True)
print("TONG", total, "ROUTE", [(round(total[0]/n), round(total[1]/n))] * n)
