import importlib, os
from pathlib import Path
SERIAL = os.environ.get("EVONY_SERIAL", "127.0.0.1:21933")   # máy đang ở màn thành của civ cần đo
CIV = int(os.environ.get("EVONY_CIV", "2"))                   # nền văn minh của máy
import sys, threading, time, os
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import adbutils, cv2
from bot.city import city_map
t = importlib.import_module(f"bot.city.civ{CIV}.city_tour")
from bot.context import BotContext
bot = BotContext(adbutils.adb.device(serial=SERIAL), threading.Event(), None, lambda m: None)
bot.civilization = CIV
order = [int(a) for a in sys.argv[1].split(",")] if len(sys.argv) > 1 else [d['plot'] for d in t.DATA]
by = {d['plot']: d for d in t.DATA}
for k in order:
    d = by[k]
    for a, b in d['swipes']:
        city_map.swipe_from_to(bot, tuple(a), tuple(b)); time.sleep(1.5)
    s = city_map.city_screen(bot)
    cv2.imwrite(os.environ["TEMP"].replace(chr(92), "/") + f"/tour_{k}.png", s)
    hits = []
    for n in city_map.BUILDINGS:
        sc, p = city_map.locate(bot, s, n)
        if p is not None and sc >= 0.5: hits.append(f"{n} {sc:.2f} ({p[0]-197:+d},{p[1]-345:+d})")
    print(f"ô {k} ({next(v for k, v in d.items() if k.startswith('seen_'))}):", "; ".join(hits) or "-", flush=True)
