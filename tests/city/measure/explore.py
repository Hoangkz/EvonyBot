"""explore.py — di zigzag khap thanh, ghi cac cong trinh thay + toa do camera (cong don theo cong trinh trung nhau)."""
import importlib, os
from pathlib import Path
SERIAL = os.environ.get("EVONY_SERIAL", "127.0.0.1:21933")   # máy đang ở màn thành của civ cần đo
CIV = int(os.environ.get("EVONY_CIV", "2"))                   # nền văn minh của máy
import sys, json, threading, time, statistics
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import adbutils
from bot.city import city_map
from bot.context import BotContext

OUT = sys.argv[1]
bot = BotContext(adbutils.adb.device(serial=SERIAL), threading.Event(), None, lambda m: None)
bot.civilization = CIV

def observe():
    s = city_map.city_screen(bot)
    found = city_map.visible(bot, s, city_map.BUILDINGS)
    out = {}
    for n, p in found.items():
        sc, _ = city_map.locate(bot, s, n)
        out[n] = [p[0], p[1], round(float(sc), 3)]
    return out

cam = [0.0, 0.0]
frames = []
prev = observe()
frames.append({"cam": list(cam), "finger": [0, 0], "seen": prev})

def step(finger):
    global prev
    city_map.swipe(bot, finger)
    time.sleep(1.0)
    now = observe()
    shared = [n for n in now if n in prev]
    if shared:
        dx = statistics.median(now[n][0] - prev[n][0] for n in shared)
        dy = statistics.median(now[n][1] - prev[n][1] for n in shared)
        how = f"shared {len(shared)}"
    else:
        dx, dy = finger
        how = "finger"
    cam[0] += dx; cam[1] += dy
    frames.append({"cam": [round(cam[0]), round(cam[1])], "finger": list(finger), "how": how, "seen": now})
    print(f"cam ({cam[0]:.0f},{cam[1]:.0f}) {how} moved ({dx:.0f},{dy:.0f}) seen {sorted(now)}", flush=True)
    prev = now
    json.dump(frames, open(OUT, "w"))

DX, DY = 180, 150
# huong dong (ngon tay + => noi dung sang phai). Di sang phai: ngon tay +DX; xuong thanh: ngon tay -DY.
path = []
for row in range(5):
    sx = 1 if row % 2 == 0 else -1
    cols = 6 if row % 2 == 0 else 6
    path += [(DX * sx, 0)] * cols
    if row < 4:
        path.append((0, -DY))
for f in path:
    step(f)
print("DONE", flush=True)
