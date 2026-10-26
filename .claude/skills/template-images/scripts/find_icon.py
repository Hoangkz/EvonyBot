"""
find_icon.py — tự tìm ảnh mẫu (ít nhất có thể) cho một icon có hiệu ứng ánh sáng
chạy liên tục, VD icon nút event dưới "Event Center".

    python find_icon.py --name haunted_castle
    python find_icon.py --name wine_glass --bursts 6 --threshold 0.8
    python find_icon.py --name x --abs 347 205          # không dùng neo, toạ độ góc trái-trên của lõi icon
    python find_icon.py --name x --no-save               # chỉ đo, không lưu

Cách làm (xem FIND_ICON.md):
  1. Tìm "neo" (mặc định Images/Event/eventCenter.png) trong vùng tìm, suy ra vị trí lõi icon.
  2. Chụp nhiều đợt khung hình (mỗi đợt --frames khung), cắt lõi icon.
  3. Biến đổi ảnh: xám -> mờ 5x5 -> Laplacian (bỏ sáng tối chập chờn, giữ nét cấu trúc).
  4. Thử vài ô con trong lõi, mỗi ô: chọn ít ảnh nhất sao cho mọi khung đều khớp >= ngưỡng,
     rồi kiểm tra chéo giữa các đợt (chọn từ đợt khác, thử trên đợt còn lại).
  5. Lưu ảnh màu (chưa biến đổi) vào Images/<out>/, chụp thêm 1 đợt mới để kiểm tra lần cuối.

Khi dùng trong bot phải áp đúng biến đổi `laplacian()` bên dưới lên CẢ ảnh mẫu và vùng tìm.
"""
import argparse
import sys
import tempfile
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
IMAGES = ROOT / "Images"
PAD = 4            # độ lệch tối đa (px) của icon giữa các khung mà vẫn khớp
BLUR = 5
# Ô con thử trong lõi (rộng, cao): lớn trước, nhỏ sau; vị trí quét bước STEP.
SIZES = [(18, 12), (14, 10), (10, 8), (26, 20)]
STEP = 3


def laplacian(img):
    """Biến đổi dùng chung cho ảnh mẫu và vùng tìm."""
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    g = cv2.GaussianBlur(g, (BLUR, BLUR), 0)
    return cv2.Laplacian(g, cv2.CV_32F, ksize=3)


def find_icon(screen, templates, region=(60, 0, 100, 50), threshold=0.8):
    """Tìm icon trong `region` (% màn hình). Trả về (điểm, (x, y) góc trái-trên toàn màn hình) hoặc None."""
    h, w = screen.shape[:2]
    x0, y0, x1, y1 = (int(w * region[0] / 100), int(h * region[1] / 100),
                      int(w * region[2] / 100), int(h * region[3] / 100))
    roi = laplacian(screen[y0:y1, x0:x1])
    best = None
    for t in templates:
        _, s, _, p = cv2.minMaxLoc(cv2.matchTemplate(roi, laplacian(t), cv2.TM_CCOEFF_NORMED))
        if best is None or s > best[0]:
            best = (float(s), (p[0] + x0, p[1] + y0))
    return best if best and best[0] >= threshold else None


def _device(serial):
    import adbutils
    return adbutils.adb.device(serial=serial) if serial else adbutils.adb.device()


def _grab(dev):
    raw = dev.shell("screencap", encoding=None)          # ảnh thô, nhanh hơn PNG
    w, h = np.frombuffer(raw[:8], np.uint32)
    px = np.frombuffer(raw[len(raw) - w * h * 4:], np.uint8).reshape(h, w, 4)
    return cv2.cvtColor(px, cv2.COLOR_RGBA2BGR)


def _locate(screen, anchor, region):
    h, w = screen.shape[:2]
    x0, y0, x1, y1 = (int(w * region[0] / 100), int(h * region[1] / 100),
                      int(w * region[2] / 100), int(h * region[3] / 100))
    _, s, _, p = cv2.minMaxLoc(cv2.matchTemplate(screen[y0:y1, x0:x1], anchor, cv2.TM_CCOEFF_NORMED))
    th, tw = anchor.shape[:2]
    return float(s), (p[0] + x0 + tw // 2, p[1] + y0 + th // 2)      # tâm neo


def _greedy(S, idx, th):
    """Chọn ít ảnh nhất (theo chỉ số trong idx) sao cho mọi khung trong idx có ảnh khớp >= th."""
    left, pick = set(idx), []
    while left:
        i = max(idx, key=lambda i: (sum(S[i, j] >= th for j in left), np.mean([S[i, j] for j in left])))
        gain = {j for j in left if S[i, j] >= th} or {i}
        pick.append(i)
        left -= gain
    return pick


def _evaluate(wins, lab, bursts, cfg, th):
    sx, sy, sw, sh = cfg
    ws = [laplacian(w) for w in wins]
    R = [w[sy:sy + sh + 2 * PAD, sx:sx + sw + 2 * PAD] for w in ws]
    T = [w[sy + PAD:sy + PAD + sh, sx + PAD:sx + PAD + sw] for w in ws]
    n = len(ws)
    S = np.full((n, n), -1.0)
    for i in range(n):
        if T[i].std() < 1e-6:
            continue
        for j in range(n):
            S[i, j] = cv2.matchTemplate(R[j], T[i], cv2.TM_CCOEFF_NORMED).max()
    cv = []
    for k in range(bursts):
        tr = [i for i in range(n) if lab[i] != k]
        te = [i for i in range(n) if lab[i] == k]
        p = _greedy(S, tr, th)
        cv += [S[p][:, j].max() for j in te]
    cv = np.array(cv)
    pick = _greedy(S, list(range(n)), th)
    return S, pick, float((cv >= th).mean()), float(cv.min())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True, help="tên file ảnh lưu ra (không đuôi)")
    ap.add_argument("-s", "--serial")
    ap.add_argument("--bursts", type=int, default=4, help="số đợt chụp để chọn ảnh (>= 3 mới kiểm tra chéo được)")
    ap.add_argument("--frames", type=int, default=30, help="số khung mỗi đợt (~0,45 s/khung)")
    ap.add_argument("--threshold", type=float, default=0.8)
    ap.add_argument("--region", type=float, nargs=4, default=(60, 0, 100, 50), metavar=("X0", "Y0", "X1", "Y1"),
                    help="vùng tìm, %% màn hình (mặc định góc trên phải)")
    ap.add_argument("--anchor", default="Event/eventCenter.png", help="ảnh neo trong Images/")
    ap.add_argument("--core", type=int, nargs=4, default=(-12, 32, 26, 20), metavar=("DX", "DY", "W", "H"),
                    help="lõi icon: lệch so với TÂM neo (DX DY) và kích thước (W H); mặc định cho icon dưới Event Center")
    ap.add_argument("--abs", type=int, nargs=2, metavar=("X", "Y"), help="bỏ neo, đặt thẳng góc trái-trên của lõi")
    ap.add_argument("--out", default="Event/ButtonIcon", help="thư mục lưu trong Images/")
    ap.add_argument("--no-save", action="store_true")
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    th = a.threshold
    dev = _device(a.serial)

    screen = _grab(dev)
    cw, ch = a.core[2], a.core[3]
    if a.abs:
        x0, y0 = a.abs
    else:
        anchor = cv2.imread(str(IMAGES / a.anchor))
        if anchor is None:
            sys.exit(f"không đọc được ảnh neo: {IMAGES / a.anchor}")
        s, (cx, cy) = _locate(screen, anchor, a.region)
        if s < 0.8:
            sys.exit(f"không thấy neo {a.anchor} (điểm {s:.2f}). Về màn hình chính rồi chạy lại, hoặc dùng --abs X Y.")
        x0, y0 = cx + a.core[0], cy + a.core[1]
        print(f"neo khớp {s:.3f}, tâm ({cx}, {cy}) -> lõi icon tại ({x0}, {y0}) {cw}x{ch}")
    core_png = Path(tempfile.gettempdir()) / "find_icon_core.png"
    cv2.imwrite(str(core_png), cv2.resize(screen[y0:y0 + ch, x0:x0 + cw], None, fx=8, fy=8, interpolation=cv2.INTER_NEAREST))
    print(f"lõi icon vừa cắt (phóng 8 lần): {core_png} — mở ra xem có dính viền / chấm đỏ / ruy băng không.")

    def crop(f):
        return f[y0 - PAD:y0 + ch + PAD, x0 - PAD:x0 + cw + PAD].copy()

    wins, lab = [], []
    for b in range(a.bursts):
        t0 = time.time()
        wins += [crop(_grab(dev)) for _ in range(a.frames)]
        lab += [b] * a.frames
        print(f"đợt {b + 1}/{a.bursts}: {a.frames} khung, {time.time() - t0:.1f} s")

    cfgs = [(sx, sy, sw, sh) for sw, sh in SIZES if sw <= cw and sh <= ch
            for sx in range(0, cw - sw + 1, STEP) for sy in range(0, ch - sh + 1, STEP)]
    results = []
    for cfg in cfgs:
        S, pick, rate, mn = _evaluate(wins, lab, a.bursts, cfg, th)
        results.append((len(pick), -rate, -mn, cfg, S, pick))
        print(f"  ô {cfg[2]}x{cfg[3]} tại ({cfg[0]},{cfg[1]}): {len(pick)} ảnh, chéo {rate:.3f}, thấp nhất {mn:.2f}")
    # ưu tiên: kiểm tra chéo 100% -> ít ảnh nhất -> ô lớn nhất (ít khớp nhầm chỗ khác) -> điểm thấp nhất cao nhất
    results.sort(key=lambda r: (r[1] > -1.0, r[0], r[1], -r[3][2] * r[3][3], r[2]))
    _, nrate, nmin, cfg, S, pick = results[0]
    sx, sy, sw, sh = cfg
    if len(pick) == 1:       # 1 ảnh: lấy ảnh có điểm thấp nhất cao nhất trên mọi khung (an toàn nhất)
        pick = [max(range(len(wins)), key=lambda i: (round(float(S[i].min()), 3), S[i].mean()))]
    tpls = [wins[i][sy + PAD:sy + PAD + sh, sx + PAD:sx + PAD + sw] for i in pick]
    print(f"\nCHỌN: ô {sw}x{sh} tại ({sx},{sy}) trong lõi, {len(tpls)} ảnh, chéo {-nrate:.3f}, thấp nhất {-nmin:.2f}")

    if not a.no_save:
        out = IMAGES / a.out
        out.mkdir(parents=True, exist_ok=True)
        for k, t in enumerate(tpls, 1):
            p = out / (f"{a.name}.png" if len(tpls) == 1 else f"{a.name}_{k}.png")
            cv2.imwrite(str(p), t)
            print("đã lưu", p)

    # kiểm tra lần cuối trên 1 đợt mới
    ex, ey = x0 + sx, y0 + sy
    scores, okpos, other = [], 0, -1.0
    for _ in range(a.frames):
        f = _grab(dev)
        h, w = f.shape[:2]
        rx0, ry0 = int(w * a.region[0] / 100), int(h * a.region[1] / 100)
        roi = laplacian(f[ry0:int(h * a.region[3] / 100), rx0:int(w * a.region[2] / 100)])
        best, bp, m_best = -1, None, None
        for t in tpls:
            m = cv2.matchTemplate(roi, laplacian(t), cv2.TM_CCOEFF_NORMED)
            _, s, _, p = cv2.minMaxLoc(m)
            if s > best:
                best, bp, m_best = float(s), (p[0] + rx0, p[1] + ry0), m
        scores.append(best)
        okpos += abs(bp[0] - ex) <= PAD and abs(bp[1] - ey) <= PAD
        mm = m_best.copy()
        mm[max(ey - ry0 - 8, 0):ey - ry0 + 9, max(ex - rx0 - 8, 0):ex - rx0 + 9] = -1
        other = max(other, float(mm.max()))
    sc = np.array(scores)
    print(f"\nKIỂM TRA {a.frames} khung mới: đạt >= {th}: {(sc >= th).sum()}/{a.frames}, "
          f"thấp nhất {sc.min():.3f}, trung bình {sc.mean():.3f}")
    print(f"  đúng vị trí icon: {okpos}/{a.frames} | chỗ khác trong vùng tìm cao nhất: {other:.3f}")
    ok = (sc >= th).all() and other < th - 0.15
    print("KẾT LUẬN:", "ổn" if ok else "CHƯA ĐẠT — tăng --bursts / --frames, hoặc kiểm tra lại lõi icon (find_icon_core.png)")


if __name__ == "__main__":
    main()
