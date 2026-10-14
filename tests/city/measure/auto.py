"""auto.py — đo nhanh một civ mới: đi theo ước lượng (số civ trước), tự bù / tìm quanh tới khi công trình ra giữa màn, in route thật từng đoạn.
Tất cả chạy trong MỘT lần (không về Thành chính giữa các đoạn); chiều về cũng đo. Ước lượng sửa trong GUESS bên dưới (mặc định số civ4)."""
import importlib, os, math, sys, threading, time, json
from pathlib import Path
SERIAL = os.environ.get("EVONY_SERIAL", "127.0.0.1:21933")
CIV = int(os.environ.get("EVONY_CIV", "5"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import adbutils
from bot.city import city_map
from bot.context import BotContext
bot = BotContext(adbutils.adb.device(serial=SERIAL), threading.Event(), None, lambda m: None)
bot.civilization = CIV
C = (197, 345)
try:
    ANCHOR = importlib.import_module(f'bot.city.civ{CIV}.city_tour').ANCHOR_SHIFT   # mốc có ANCHOR_SHIFT: 'giữa' lệch so với ảnh mẫu
except Exception:
    ANCHOR = {}
# (mốc đích, mốc xuất phát, ước lượng dịch từ mốc xuất phát tới mốc đích) — theo thứ tự đi
GUESS = [
    ('academy', 'keep', (176, 77)), ('hospital', 'academy', (399, -50)), ('stables', 'hospital', (172, -151)), ('barracks', 'stables', (-93, -104)),
    ('archer_camp', 'barracks', (228, -117)), ('workshop', 'archer_camp', (172, 87)), ('war_hall', 'workshop', (-618, -291)),
    ('embassy', 'war_hall', (-216, -104)), ('market', 'embassy', (82, 217)), ('tavern', 'market', (-304, 231)), ('forge', 'tavern', (-7, -279)),
    ('trap_factory', 'forge', (-201, 148)), ('prison', 'trap_factory', (-229, 84)), ('keep', 'prison', (439, 252)),
    ('walls', 'keep', (968, -536)), ('keep', 'walls', (-968, 536)),
    ('research_factory', 'keep', (787, 94)), ('art_hall', 'research_factory', (205, -135)), ('pasture', 'art_hall', (230, -112)),
    ('art_hall', 'pasture', (-247, 118)), ('research_factory', 'art_hall', (-205, 135)),
    ('watchtower', 'research_factory', (873, -169)), ('research_factory', 'watchtower', (-873, 169)), ('keep', 'research_factory', (-787, -94)),
    ('rally_spot', 'keep', (-396, -480)), ('keep', 'rally_spot', (396, 480)),
    ('shrine', 'keep', (270, -190)), ('keep', 'shrine', (-270, 190)),
    ('walls', 'keep', (968, -536)), ('battlefield', 'walls', (229, -75)), ('walls', 'battlefield', (-229, 75)),
    ('archer_tower', 'walls', (676, -688)), ('walls', 'archer_tower', (-676, 688)), ('keep', 'walls', (-968, 536)),
]
if os.environ.get('AUTO_GUESS'): GUESS = json.loads(os.environ['AUTO_GUESS'])
only = sys.argv[1] if len(sys.argv) > 1 else None   # "a-b": chỉ chạy GUESS[a:b]
if only:
    a, b = map(int, only.split("-")); GUESS = GUESS[a:b]

def center(name):
    a = ANCHOR.get(name, (0, 0)); return (C[0] + a[0], C[1] + a[1])

def find(name):
    s = city_map.city_screen(bot)
    sc, p = city_map.locate(bot, s, name)
    return (sc, p) if p is not None and sc >= 0.75 else (sc, None)

def move(v, n=None):
    n = n or max(math.ceil(abs(v[0]) / 240), math.ceil(abs(v[1]) / 260), 1)
    step = (round(v[0] / n), round(v[1] / n))
    for _ in range(n):
        city_map.swipe(bot, step); time.sleep(1.1)
    return [step[0] * n, step[1] * n]

for name, frm, g in GUESS:
    tot = move(g[:2], g[2] if len(g) > 2 else None)
    sc, p = find(name)
    probes = [(150, 0), (-150, 0), (0, 150), (0, -150), (150, 150), (-150, -150), (150, -150), (-150, 150), (300, 0), (-300, 0), (0, 300), (0, -300), (300, 300), (-300, -300), (300, -300), (-300, 300)]
    tries = 0
    while p is None and tries < len(probes):
        d = probes[tries]; tries += 1
        city_map.swipe(bot, d); time.sleep(1.1); tot[0] += d[0]; tot[1] += d[1]
        sc, p = find(name)
    for _ in range(3):
        cc = center(name)
        if p is None or (abs(p[0] - cc[0]) <= 12 and abs(p[1] - cc[1]) <= 12): break
        c = (-(p[0] - cc[0]), -(p[1] - cc[1]))
        city_map.swipe(bot, c); time.sleep(1.1); tot[0] += c[0]; tot[1] += c[1]
        sc, p = find(name)
    n = g[2] if len(g) > 2 else max(math.ceil(abs(g[0]) / 240), math.ceil(abs(g[1]) / 260), 1)
    print(f"{frm:17s}->{name:17s} tổng {tuple(tot)} lech {None if p is None else (p[0]-center(name)[0], p[1]-center(name)[1])} điểm {sc:.2f} (ước lượng {g}, {n} cú)", flush=True)
