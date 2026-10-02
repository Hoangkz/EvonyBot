"""
probe.py — screenshot a device, crop templates into Images/, and measure
how well a template matches (same TM_CCOEFF_NORMED as BotContext.find).

    python probe.py devices
    python probe.py shot  [-s SERIAL] -o shot.png
    python probe.py crop  IMAGE X Y W H -o Folder/name.png
    python probe.py match TEMPLATE [-s SERIAL | --image FILE] [--threshold T] [--region X0 Y0 X1 Y1]
"""
import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
IMAGES = ROOT / "Images"


def _device(serial):
    import adbutils
    return adbutils.adb.device(serial=serial) if serial else adbutils.adb.device()


def _screenshot(serial) -> np.ndarray:
    image = _device(serial).screenshot().convert("RGB")
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


def _read(path) -> np.ndarray:
    image = cv2.imread(str(path))
    if image is None:
        sys.exit(f"cannot read image: {path}")
    return image


def cmd_devices(_):
    import adbutils
    for d in adbutils.adb.device_list():
        print(d.serial, d.window_size())


def cmd_shot(args):
    screen = _screenshot(args.serial)
    cv2.imwrite(args.output, screen)
    h, w = screen.shape[:2]
    print(f"saved {args.output} ({w}x{h})")


def cmd_crop(args):
    image = _read(args.image)
    x, y = max(args.x, 0), max(args.y, 0)
    part = image[y:y + args.h, x:x + args.w]
    out = IMAGES / args.output
    if out.exists() and not args.force:
        sys.exit(f"{out} exists (use --force to overwrite)")
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), part)
    print(f"saved {out.relative_to(ROOT)} ({part.shape[1]}x{part.shape[0]})")


def cmd_match(args):
    tpl = _read(IMAGES / args.template)
    screen = _read(args.image) if args.image else _screenshot(args.serial)
    h, w = screen.shape[:2]
    ox = oy = 0
    if args.region:
        x0, y0, x1, y1 = args.region
        ox, oy = int(w * x0 / 100), int(h * y0 / 100)
        screen = screen[oy:int(h * y1 / 100), ox:int(w * x1 / 100)]
    th, tw = tpl.shape[:2]
    if th > screen.shape[0] or tw > screen.shape[1]:
        sys.exit("template is larger than the search area")
    result = cv2.matchTemplate(screen, tpl, cv2.TM_CCOEFF_NORMED)
    _, best, _, loc = cv2.minMaxLoc(result)
    cx, cy = loc[0] + ox + tw // 2, loc[1] + oy + th // 2
    print(f"best score {best:.3f} at center ({cx}, {cy}), top-left ({loc[0] + ox}, {loc[1] + oy})")

    ys, xs = np.where(result >= args.threshold)
    hits = sorted(zip(xs, ys), key=lambda p: result[p[1], p[0]], reverse=True)
    kept = []
    for x, y in hits:
        if all(abs(x - kx) >= tw // 2 or abs(y - ky) >= th // 2 for kx, ky in kept):
            kept.append((x, y))
    print(f"{len(kept)} hit(s) >= {args.threshold}:")
    for x, y in kept[:20]:
        print(f"  {result[y, x]:.3f} center ({x + ox + tw // 2}, {y + oy + th // 2})")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("devices").set_defaults(func=cmd_devices)

    s = sub.add_parser("shot")
    s.add_argument("-s", "--serial")
    s.add_argument("-o", "--output", default="shot.png")
    s.set_defaults(func=cmd_shot)

    c = sub.add_parser("crop")
    c.add_argument("image")
    for name in ("x", "y", "w", "h"):
        c.add_argument(name, type=int)
    c.add_argument("-o", "--output", required=True, help="path under Images/")
    c.add_argument("--force", action="store_true")
    c.set_defaults(func=cmd_crop)

    m = sub.add_parser("match")
    m.add_argument("template", help="path under Images/")
    m.add_argument("-s", "--serial")
    m.add_argument("--image", help="match against this file instead of the device")
    m.add_argument("--threshold", type=float, default=0.9)
    m.add_argument("--region", type=float, nargs=4, metavar=("X0", "Y0", "X1", "Y1"))
    m.set_defaults(func=cmd_match)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
