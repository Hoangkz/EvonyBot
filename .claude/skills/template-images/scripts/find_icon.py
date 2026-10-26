"""
find_icon.py — tạo bộ ảnh mẫu cho icon nút event (dưới "Event Center") có animation.

Icon có hiệu ứng chạy liên tục nên MỖI TRẠNG THÁI animation cần một ảnh mẫu; bot nhận icon nếu BẤT KỲ ảnh
nào trong Images/Event/ButtonIcon/ khớp >= ngưỡng của bot (0,8). Để ngoài thực tế chắc chắn thấy, bộ ảnh phải phủ
mọi khung với điểm >= --cover (mặc định 0,85, KHÔNG sát ngưỡng 0,8). Quy trình (giống cách cắt tay: cắt một ảnh, khung
nào khớp dưới 0,85 thì cắt thêm ảnh từ khung đó, lặp đến khi mọi khung đều khớp):

    python find_icon.py --name haunted_castle                       # chụp giả lập, tự chọn ô cắt
    python find_icon.py --name beer_mugs --seed my_crop.png         # bắt đầu từ ảnh cắt tay
    python find_icon.py --name x --images "tests/**/03_main.png"    # dùng ảnh chụp có sẵn thay vì chụp giả lập
    python find_icon.py --name beer_mugs --add-from tests/a.png tests/b.png   # cắt thêm từ ảnh bị sót
    python find_icon.py --name beer_mugs --add-from near                       # cắt thêm cho mọi ảnh điểm < --cover
    python find_icon.py --name x --no-save                          # chỉ đo, không lưu

Các bước: (1) lấy khung (chụp --bursts đợt x --frames khung, cách nhau --gap giây để phủ hết chu kỳ animation, hoặc
--images); (2) định vị icon qua neo Event Center; (3) với mỗi ô cắt thử, chọn bộ ảnh theo cách lặp ở trên, kiểm tra
chéo giữa các đợt; (4) in số ảnh cần khi thêm từng đợt (ngừng tăng = đã gặp đủ trạng thái); (5) lưu ảnh; (6) kiểm tra
bằng CHÍNH hàm của bot (button_icon.find_button_icon) trên mọi ảnh màn thành chính trong tests/, lấy hàm ruy băng
làm chuẩn: trùng nút / sai nút / bị sót / sát ngưỡng (nhận được nhưng điểm < --cover).

Điểm của một ảnh mẫu = điểm cao hơn của khớp màu thẳng và khớp Laplacian (xám -> mờ 5x5 -> Laplacian), giống bot.
"""
import argparse
import glob
import sys
import tempfile
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
IMAGES = ROOT / "Images"
sys.path.insert(0, str(ROOT))

PAD = 4          # độ lệch tối đa (px) của icon giữa các khung
MARGIN = 8       # lề lấy thêm khi tính Laplacian cửa sổ, để không dính hiệu ứng viền của biến đổi
BLUR = 5
SIZES = [(32, 20), (26, 20), (18, 12), (14, 10), (10, 8)]   # (rộng, cao) ô cắt thử, lớn trước
STEP = 3
MAX_CANDIDATES = 60   # số khung dùng làm ứng viên ảnh mẫu (còn lại chỉ để chấm điểm)
MAX_TEMPLATES = 14
ANCHOR = "Event/eventCenter.png"
ANCHOR_REGION = (60, 0, 100, 50)
TMP_DIR = "Event/_find_icon_tmp"      # thư mục tạm trong Images/ để bot đo thử đúng bộ ảnh mới
TAP_TOL = 25                          # icon và ruy băng cùng một nút nếu điểm bấm lệch <= số px này


def lap(img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    return cv2.Laplacian(cv2.GaussianBlur(g, (BLUR, BLUR), 0), cv2.CV_32F, ksize=3)


def ncc(area, tpl):
    if tpl.shape[0] > area.shape[0] or tpl.shape[1] > area.shape[1] or tpl.std() < 1e-6:
        return -1.0
    return float(cv2.matchTemplate(area, tpl, cv2.TM_CCOEFF_NORMED).max())


def locate(screen, anchor):
    h, w = screen.shape[:2]
    x0, y0, x1, y1 = (int(w * ANCHOR_REGION[0] / 100), int(h * ANCHOR_REGION[1] / 100),
                      int(w * ANCHOR_REGION[2] / 100), int(h * ANCHOR_REGION[3] / 100))
    _, s, _, p = cv2.minMaxLoc(cv2.matchTemplate(screen[y0:y1, x0:x1], anchor, cv2.TM_CCOEFF_NORMED))
    th, tw = anchor.shape[:2]
    return float(s), (p[0] + x0 + tw // 2, p[1] + y0 + th // 2)


class Frame:
    """Một ảnh chụp có neo Event Center tại (cx, cy). cfg = (dx, dy, w, h) so với tâm neo."""
    B = 48

    def __init__(self, img, cx, cy, group, name=""):
        self.p = cv2.copyMakeBorder(img, self.B, self.B, self.B, self.B, cv2.BORDER_REPLICATE)
        self.cx, self.cy, self.group, self.name = cx + self.B, cy + self.B, group, name
        self._w = {}

    def crop(self, cfg):
        dx, dy, w, h = cfg
        return self.p[self.cy + dy:self.cy + dy + h, self.cx + dx:self.cx + dx + w].copy()

    def window(self, cfg):
        """(ảnh màu, ảnh Laplacian) của vùng ô cắt mở rộng PAD mỗi phía."""
        if cfg not in self._w:
            dx, dy, w, h = cfg
            x, y, W, H, m = self.cx + dx - PAD, self.cy + dy - PAD, w + 2 * PAD, h + 2 * PAD, MARGIN
            self._w[cfg] = (self.p[y:y + H, x:x + W], lap(self.p[y - m:y + H + m, x - m:x + W + m])[m:m + H, m:m + W])
        return self._w[cfg]


def score(tpl, tpl_lap, frame, cfg):
    win, win_lap = frame.window(cfg)
    return max(ncc(win, tpl), ncc(win_lap, tpl_lap))


def build_set(frames, cfg, th, seed=None, cands=None):
    """Chọn bộ ảnh mẫu cho `cfg`: bắt đầu từ `seed` (hoặc ảnh phủ nhiều khung nhất), rồi lặp: trong các khung chưa
    khớp >= th, lấy ảnh cắt từ khung phủ được nhiều khung chưa khớp nhất, đến khi hết. Trả (danh sách ảnh, điểm tốt nhất
    mỗi khung, số khung không phủ nổi)."""
    n = len(frames)
    tpls, best = [], np.full(n, -1.0)

    def add(t):
        tl = lap(t)
        s = np.array([score(t, tl, f, cfg) for f in frames])
        tpls.append(t)
        np.maximum(best, s, out=best)

    def gain(i):
        t = frames[i].crop(cfg)
        tl = lap(t)
        return sum(1 for j in range(n) if best[j] < th and score(t, tl, frames[j], cfg) >= th)

    cands = list(range(n)) if cands is None else cands
    if seed is not None:
        add(seed)
    else:
        add(frames[max(cands[:MAX_CANDIDATES], key=gain)].crop(cfg))
    while len(tpls) < MAX_TEMPLATES:
        low = [int(j) for j in np.argsort(best) if best[j] < th]
        if not low:
            break
        pool = low[:8]
        j = max(pool, key=gain)
        if gain(j) == 0:
            j = pool[0]               # không ảnh nào phủ thêm được: lấy chính khung thấp nhất
        add(frames[j].crop(cfg))
    return tpls, best, int((best < th).sum())


def min_cover(frames, cfg, th, seed=None, tries=200):
    """Bộ ảnh NHỎ NHẤT phủ mọi khung >= th: lấy MỌI khung làm ứng viên (ma trận điểm n x n), phủ tập tham lam nhiều lần có
    ngẫu nhiên rồi loại ảnh thừa. Thường nhỏ hơn nhiều so với cách thêm từng ảnh của build_set (cốc bia: 16 -> 4 ảnh)."""
    import random
    n = len(frames)
    cands = [f.crop(cfg) for f in frames]
    cl = [lap(c) for c in cands]
    S = np.array([[score(cands[i], cl[i], frames[j], cfg) for j in range(n)] for i in range(n)], np.float32)
    base = np.zeros(n, bool)
    if seed is not None:
        sl = lap(seed)
        base = np.array([score(seed, sl, f, cfg) >= th for f in frames])

    def greedy(rng=None):
        left = ~base
        sel = []
        while left.any():
            gain = ((S >= th) & left).sum(1)
            i = int(gain.argmax()) if rng is None else int(rng.choice(np.argsort(-gain)[:3]))
            if gain[i] == 0:
                i = int(np.where(left)[0][0])
            sel.append(i)
            left = left & ~(S[i] >= th)
        return sel

    def prune(sel):
        sel = list(sel)
        changed = True
        while changed:
            changed = False
            for i in sorted(sel, key=lambda i: int((S[i] >= th).sum())):
                rest = [j for j in sel if j != i]
                if (S[rest].max(0) >= th)[~base].all() if rest else not (~base).any():
                    sel, changed = rest, True
                    break
        return sel
    rng = random.Random(1)
    best = prune(greedy())
    for _ in range(tries):
        cand = prune(greedy(rng))
        if len(cand) < len(best):
            best = cand
    best = sorted(best, key=lambda i: -int((S[i] >= th).sum()))
    return ([seed] if seed is not None else []) + [cands[i] for i in best]


def cross_validate(frames, cfg, th, seed):
    groups = sorted({f.group for f in frames})
    if len(groups) < 2:
        return 1.0, 1.0
    ok = n = 0
    worst = 1.0
    for g in groups:
        train = [f for f in frames if f.group != g]
        test = [f for f in frames if f.group == g]
        tpls, _, _ = build_set(train, cfg, th, seed)
        tl = [lap(t) for t in tpls]
        for f in test:
            s = max(score(t, l, f, cfg) for t, l in zip(tpls, tl))
            ok += s >= th
            n += 1
            worst = min(worst, s)
    return ok / n, worst


def grab(dev):
    raw = dev.shell("screencap", encoding=None)          # ảnh thô, nhanh hơn PNG
    w, h = np.frombuffer(raw[:8], np.uint32)
    px = np.frombuffer(raw[len(raw) - w * h * 4:], np.uint8).reshape(h, w, 4)
    return cv2.cvtColor(px, cv2.COLOR_RGBA2BGR)


def make_ctx():
    from bot.context import BotContext
    return BotContext(SimpleNamespace(serial="t"), threading.Event(), None, lambda m: None)


def verify(templates, corpus_globs, th, cover, quiet=False):
    """Đo bằng chính hàm của bot: bộ `templates` (chỉ bộ này) trên mọi ảnh màn thành chính trong corpus, lấy
    hàm ruy băng làm chuẩn. Trả dict kết quả + lệch trung vị (tâm ảnh mẫu - điểm bấm ruy băng)."""
    from bot.activities.event import button_icon as bi, common
    from bot.activities.event.constants import MAIN_SCREEN
    ctx = make_ctx()
    logs = []
    ctx.log = lambda m: logs.append(m)
    tmp = IMAGES / TMP_DIR
    tmp.mkdir(parents=True, exist_ok=True)
    for old in tmp.glob("*.png"):
        old.unlink()
    for k, t in enumerate(templates):
        cv2.imwrite(str(tmp / f"t{k:02d}.png"), t)
    files = sorted({f for g in corpus_globs for f in glob.glob(str(ROOT / g), recursive=True)})
    saved_dir, saved_th = bi.BUTTON_ICON_DIR, bi.BUTTON_ICON_THRESHOLD
    res = {"agree": [], "ribbon_none": [], "other": [], "missed": [], "near": [], "neither": 0, "main": 0}
    offs = []
    try:
        for f in files:
            img = cv2.imread(f)
            if img is None or img.shape[:2] != (704, 396) or ctx.find(MAIN_SCREEN, screen=img) is None:
                continue
            res["main"] += 1
            bi.BUTTON_ICON_DIR, bi.BUTTON_ICON_THRESHOLD = TMP_DIR, -1.0     # -1: lấy điểm tốt nhất rồi tự so với th
            bi._cache.clear()
            logs.clear()
            icon = bi.find_button_icon(ctx, img)
            sc = float(logs[-1].rsplit("score ", 1)[1]) if icon and logs else -1.0
            if sc < th:
                icon = None
            bi.BUTTON_ICON_DIR = "Event/__no_such_dir__"
            ribbon = common.find_event_button(ctx, img)
            name = str(Path(f).relative_to(ROOT)).replace("\\", "/")
            if icon and ribbon:
                if abs(icon[0] - ribbon[0]) <= TAP_TOL and abs(icon[1] - ribbon[1]) <= TAP_TOL:
                    res["agree"].append(name)
                    if sc < cover:
                        res["near"].append((name, sc, ribbon))
                    offs.append((icon[0] - ribbon[0], icon[1] - ribbon[1]))
                else:
                    res["other"].append((name, icon, ribbon))
            elif icon:
                res["ribbon_none"].append(name)
            elif ribbon:
                res["missed"].append((name, ribbon))
            else:
                res["neither"] += 1
    finally:
        bi.BUTTON_ICON_DIR, bi.BUTTON_ICON_THRESHOLD = saved_dir, saved_th
        bi._cache.clear()
        for old in tmp.glob("*.png"):
            old.unlink()
        try:
            tmp.rmdir()
        except OSError:
            pass
    res["offset"] = tuple(int(v) for v in np.median(np.array(offs), axis=0)) if offs else None
    if not quiet:
        print(f"\nKIỂM TRA bằng hàm của bot trên {res['main']} ảnh màn thành chính trong tests/ (chuẩn = ruy băng):")
        print(f"  icon nhận đúng nút (trùng ruy băng <= {TAP_TOL} px): {len(res['agree'])}")
        print(f"  icon nhận, ruy băng không thấy nút (thường do popup che): {len(res['ribbon_none'])}")
        print(f"  icon nhận SAI nút (khác ruy băng): {len(res['other'])}")
        print(f"  icon nhận nhưng điểm < {cover} (SÁT NGƯỠNG {th}, ngoài thực tế dễ tụt): {len(res['near'])}"
              + ("  <- chạy --add-from near để cắt thêm" if res["near"] else ""))
        for name, sc, _ in sorted(res["near"], key=lambda r: r[1])[:8]:
            print(f"      {sc:.3f} {name}")
        for name, icon, ribbon in res["other"][:10]:
            print(f"      {name}: icon {icon}, ruy băng {ribbon}")
        print(f"  ruy băng thấy nút, icon KHÔNG nhận: {len(res['missed'])}  <- xem các ảnh này: nếu là event này thì cắt thêm (--add-from)")
        for name, ribbon in res["missed"][:12]:
            print(f"      {name}: ruy băng {ribbon}")
        if len(res["missed"]) > 12:
            print(f"      ... và {len(res['missed']) - 12} ảnh nữa (có thể là event khác, không có ảnh mẫu)")
        if res["offset"]:
            print(f"  lệch tâm ảnh mẫu so với điểm bấm ruy băng: {res['offset']} (dùng cho --add-from)")
    return res


def save(templates, out_dir, name):
    out = IMAGES / out_dir
    out.mkdir(parents=True, exist_ok=True)
    for old in list(out.glob(f"{name}.png")) + list(out.glob(f"{name}_[0-9]*.png")):
        old.unlink()
    paths = []
    for k, t in enumerate(templates, 1):
        p = out / (f"{name}.png" if k == 1 else f"{name}_{k}.png")
        cv2.imwrite(str(p), t)
        paths.append(p)
    return paths


def existing(out_dir, name):
    out = IMAGES / out_dir
    files = ([out / f"{name}.png"] if (out / f"{name}.png").exists() else []) + sorted(out.glob(f"{name}_[0-9]*.png"))
    return files, [cv2.imread(str(f)) for f in files]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True, help="tên file ảnh lưu ra (không đuôi); nhiều ảnh: <name>.png, <name>_2.png, ...")
    ap.add_argument("-s", "--serial")
    ap.add_argument("--bursts", type=int, default=6, help="số đợt chụp (>= 3 mới kiểm tra chéo được)")
    ap.add_argument("--frames", type=int, default=30, help="số khung mỗi đợt (~0,45 s/khung)")
    ap.add_argument("--gap", type=float, default=10, help="giây nghỉ giữa các đợt, để phủ hết chu kỳ animation")
    ap.add_argument("--images", nargs="+", metavar="GLOB", help="dùng ảnh chụp có sẵn (glob, tính từ gốc repo) thay vì chụp giả lập")
    ap.add_argument("--seed", help="ảnh cắt tay làm ảnh đầu tiên (ô cắt lấy theo ảnh này)")
    ap.add_argument("--add-from", nargs="+", metavar="IMAGE", help="chỉ cắt THÊM ảnh mẫu từ các ảnh này (ảnh bị sót) rồi đo lại")
    ap.add_argument("--threshold", type=float, default=0.8, help="ngưỡng khớp của bot (BUTTON_ICON_THRESHOLD)")
    ap.add_argument("--cover", type=float, default=0.85, help="điểm tối thiểu bộ ảnh phải phủ trên MỌI khung (cao hơn --threshold để có dư địa)")
    ap.add_argument("--core", type=int, nargs=4, default=(-12, 32, 26, 20), metavar=("DX", "DY", "W", "H"),
                    help="lõi tìm ô cắt: lệch so với TÂM chữ Event Center và kích thước. KHÔNG được dính viền, chấm đỏ, ruy băng")
    ap.add_argument("--corpus", nargs="+", default=["tests/**/*.png"], help="ảnh dùng để kiểm tra bằng hàm của bot")
    ap.add_argument("--out", default="Event/ButtonIcon", help="thư mục lưu trong Images/")
    ap.add_argument("--no-save", action="store_true")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    th, cov = a.threshold, a.cover

    if a.add_from:                                   # chế độ chỉ cắt thêm
        from bot.activities.event import common, button_icon as bi
        files, tpls = existing(a.out, a.name)
        if not tpls:
            sys.exit(f"chưa có ảnh {a.name}*.png trong Images/{a.out}; chạy không có --add-from trước")
        print(f"có sẵn {len(tpls)} ảnh; đo để lấy độ lệch tâm ảnh mẫu so với ruy băng...")
        first = verify(tpls, a.corpus, th, cov, quiet=True)
        off = first["offset"]
        if off is None:
            sys.exit("không đo được độ lệch (ảnh hiện có không nhận được ảnh nào)")
        h, w = tpls[0].shape[:2]
        ctx = make_ctx()
        bi.BUTTON_ICON_DIR = "Event/__no_such_dir__"
        if a.add_from == ["near"]:                   # cắt thêm lặp lại cho mọi ảnh điểm < cover
            cfg = (-(w // 2), -(h // 2), w, h)
            fr = [Frame(cv2.imread(str(ROOT / name)), tap[0] + off[0], tap[1] + off[1], 0, name)
                  for name, _, tap in first["near"]]
            tls = [lap(t) for t in tpls]
            best = np.array([max(score(t, l, f, cfg) for t, l in zip(tpls, tls)) for f in fr])
            added = 0
            while len(fr) and (best < cov).any() and added < 25:
                low = [int(j) for j in np.argsort(best) if best[j] < cov]

                def gain(j):
                    t = fr[j].crop(cfg)
                    l = lap(t)
                    return sum(1 for k in low if score(t, l, fr[k], cfg) >= cov)
                j = max(low[:12], key=gain)
                t = fr[j].crop(cfg)
                l = lap(t)
                tpls.append(t)
                added += 1
                best = np.maximum(best, np.array([score(t, l, f, cfg) for f in fr]))
                print(f"  cắt thêm từ {fr[j].name}: còn {int((best < cov).sum())} khung dưới {cov}")
            if not added:
                print(f"không có ảnh nào dưới {cov}")
            a.add_from = []
        for path in a.add_from:
            img = cv2.imread(path)
            tap = common.find_event_button(ctx, img) if img is not None else None
            if tap is None:
                print("  bỏ qua", path, "(ruy băng không thấy nút)")
                continue
            cx, cy = tap[0] + off[0], tap[1] + off[1]
            tpls.append(img[cy - h // 2:cy - h // 2 + h, cx - w // 2:cx - w // 2 + w].copy())
            print(f"  cắt thêm từ {path}: tâm {cx, cy}, {w}x{h}")
        if not a.no_save:
            for p in save(tpls, a.out, a.name):
                print("đã lưu", p)
        verify(tpls, a.corpus, th, cov)
        return

    anchor = cv2.imread(str(IMAGES / ANCHOR))
    frames = []
    if a.images:
        files = sorted({f for g in a.images for f in glob.glob(str(ROOT / g), recursive=True)})
        for k, f in enumerate(files):
            img = cv2.imread(f)
            if img is None:
                continue
            s, (cx, cy) = locate(img, anchor)
            if s >= 0.8:
                frames.append(Frame(img, cx, cy, k, Path(f).name))
        print(f"{len(frames)}/{len(files)} ảnh có chữ Event Center")
    else:
        import adbutils
        dev = adbutils.adb.device(serial=a.serial) if a.serial else adbutils.adb.device()
        for b in range(a.bursts):
            t0, got = time.time(), 0
            for _ in range(a.frames):
                img = grab(dev)
                s, (cx, cy) = locate(img, anchor)
                if s >= 0.8:
                    frames.append(Frame(img, cx, cy, b))
                    got += 1
            print(f"đợt {b + 1}/{a.bursts}: {got}/{a.frames} khung có Event Center, {time.time() - t0:.0f} s")
            if b + 1 < a.bursts and a.gap > 0:
                time.sleep(a.gap)
    if len(frames) < 3:
        sys.exit("quá ít khung có chữ Event Center. Về màn thành chính (thấy Event Center và icon bên dưới) rồi chạy lại.")

    seed, cfgs = None, []
    if a.seed:
        seed = cv2.imread(a.seed)
        sh, sw = seed.shape[:2]
        f0 = frames[0]
        area = f0.p[f0.cy - 60:f0.cy + 160, f0.cx - 80:f0.cx + 80]
        _, s, _, (x, y) = cv2.minMaxLoc(cv2.matchTemplate(area, seed, cv2.TM_CCOEFF_NORMED))
        cfgs = [(x - 80, y - 60, sw, sh)]
        print(f"ảnh seed {sw}x{sh} khớp khung đầu {s:.2f} tại lệch so với tâm Event Center {cfgs[0][:2]}")
    else:
        dx, dy, cw, ch = a.core
        cfgs = [(dx + sx, dy + sy, sw, sh) for sw, sh in SIZES if sw <= cw and sh <= ch
                for sx in range(0, cw - sw + 1, STEP) for sy in range(0, ch - sh + 1, STEP)]
        core_png = Path(tempfile.gettempdir()) / "find_icon_core.png"
        f0 = frames[0]
        cv2.imwrite(str(core_png), cv2.resize(f0.crop((dx, dy, cw, ch)), None, fx=8, fy=8, interpolation=cv2.INTER_NEAREST))
        print(f"lõi icon (phóng 8 lần): {core_png} — mở ra xem có dính viền / chấm đỏ / ruy băng không")

    cands = list(range(0, len(frames), max(1, len(frames) // MAX_CANDIDATES)))
    results = []
    for cfg in cfgs:
        tpls, best, bad = build_set(frames, cfg, cov, seed, cands)
        rate, worst = cross_validate(frames, cfg, cov, seed) if len(cfgs) > 1 or seed is None else (1.0, 1.0)
        results.append((rate < 1.0, bad > 0, len(tpls), -cfg[2] * cfg[3], -worst, cfg, tpls, rate, worst))
        print(f"  ô {cfg[2]}x{cfg[3]} tại {cfg[:2]}: {len(tpls)} ảnh, chéo {rate:.3f}, thấp nhất {worst:.2f}")
    results.sort(key=lambda r: r[:5])
    _, _, _, _, _, cfg, tpls, rate, worst = results[0]
    print(f"\nCHỌN (mọi khung phủ >= {cov}): ô {cfg[2]}x{cfg[3]} tại {cfg[:2]} so với tâm Event Center: {len(tpls)} ảnh, chéo {rate:.3f}, thấp nhất {worst:.2f}")
    if len(frames) <= 600:
        small = min_cover(frames, cfg, cov, seed)
        if len(small) < len(tpls):
            print(f"phủ tập tối ưu (mọi khung làm ứng viên): {len(tpls)} -> {len(small)} ảnh")
            tpls = small

    if not a.images and a.bursts >= 3:               # đã gặp đủ trạng thái animation chưa?
        print("\nSỐ ẢNH CẦN khi thêm từng đợt chụp (ngừng tăng và đợt sau đã được phủ = đã gặp đủ trạng thái):")
        for b in range(a.bursts - 1):
            train = [f for f in frames if f.group <= b]
            nxt = [f for f in frames if f.group == b + 1]
            if not train or not nxt:
                continue
            t, _, _ = build_set(train, cfg, cov, seed)
            tl = [lap(x) for x in t]
            hit = sum(max(score(x, l, f, cfg) for x, l in zip(t, tl)) >= cov for f in nxt)
            print(f"  {b + 1} đợt đầu: {len(t)} ảnh, phủ {hit}/{len(nxt)} khung của đợt {b + 2}")

    if not a.no_save:
        for p in save(tpls, a.out, a.name):
            print("đã lưu", p)
    res = verify(tpls, a.corpus, th, cov)
    ok = not res["other"] and not res["near"] and (res["agree"] or res["ribbon_none"]) and worst >= cov
    print("\nKẾT LUẬN:", ("ổn" if ok else "CHƯA CHẮC — xem các mục trên (ảnh sai nút, ảnh sát ngưỡng, số ảnh còn tăng khi thêm đợt, điểm thấp nhất < cover)")
          + (f"; còn {len(res['missed'])} ảnh ruy băng thấy nút mà icon không nhận: nếu có ảnh của event này thì --add-from, "
             "còn lại là event khác" if res["missed"] else ""))


if __name__ == "__main__":
    main()
