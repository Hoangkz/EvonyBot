"""Capture animated city launcher variants and keep the sharpest frames."""
import argparse
import time
from pathlib import Path

import adbutils
import cv2
import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--serial", required=True)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prefix", default="launcher_frame")
    parser.add_argument("--frames", type=int, default=12)
    args = parser.parse_args()

    template = cv2.imread(str(args.template))
    device = adbutils.adb.device(serial=args.serial)
    candidates = []
    for index in range(args.frames):
        rgb = np.asarray(device.screenshot())
        screen = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        scores = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        _, score, _, (x, y) = cv2.minMaxLoc(scores)
        crop = screen[y:y + template.shape[0], x:x + template.shape[1]].copy()
        sharpness = cv2.Laplacian(crop, cv2.CV_64F).var()
        candidates.append((sharpness, float(score), index, crop))
        time.sleep(0.3)

    args.output.mkdir(parents=True, exist_ok=True)
    selected = sorted(candidates, reverse=True)[:3]
    for rank, (sharpness, score, frame, crop) in enumerate(selected, 1):
        target = args.output / f"{args.prefix}_{rank}.png"
        cv2.imwrite(str(target), crop)
        print(f"{target}: frame={frame}, match={score:.3f}, sharpness={sharpness:.1f}")


if __name__ == "__main__":
    main()
