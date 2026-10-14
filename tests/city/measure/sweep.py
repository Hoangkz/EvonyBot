"""sweep.py NAME dx,dy [bước_ngang] — từ Thành chính vuốt tới (dx,dy) rồi quét ngang qua lại / dọc tìm NAME; in tổng vuốt khi thấy (>= 0,8)."""
import os, sys, math, threading, time
from pathlib import Path
SERIAL = os.environ.get("EVONY_SERIAL", "127.0.0.1:21933"); CIV = int(os.environ.get("EVONY_CIV", "5"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import adbutils
from bot.city import city_map
from bot.context import BotContext
bot = BotContext(adbutils.adb.device(serial=SERIAL), threading.Event(), None, lambda m: None); bot.civilization = CIV
name = sys.argv[1]; gx, gy = map(int, sys.argv[2].split(","))
tot = [0, 0]
def mv(v):
    n = max(math.ceil(abs(v[0]) / 240), math.ceil(abs(v[1]) / 260), 1); st = (round(v[0] / n), round(v[1] / n))
    for _ in range(n): city_map.swipe(bot, st); time.sleep(1.1)
    tot[0] += st[0] * n; tot[1] += st[1] * n
def look():
    s = city_map.city_screen(bot); sc, p = city_map.locate(bot, s, name); return sc, p
mv((gx, gy))
path = [(0, 0)] + [(170, 0)] * 3 + [(0, 170)] + [(-170, 0)] * 6 + [(0, 170)] + [(170, 0)] * 6 + [(0, -520)] + [(-170, 0)] * 6
for d in path:
    if d != (0, 0): mv(d)
    sc, p = look()
    print(f"tổng {tuple(tot)} {name} {sc:.2f} {p}", flush=True)
    if p is not None and sc >= 0.8:
        for _ in range(3):
            if abs(p[0] - 197) <= 12 and abs(p[1] - 345) <= 12: break
            c = (-(p[0] - 197), -(p[1] - 345)); mv(c); sc, p = look()
        print("FOUND tổng", tuple(tot), "lech", None if p is None else (p[0] - 197, p[1] - 345)); break
