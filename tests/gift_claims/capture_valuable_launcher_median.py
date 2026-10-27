"""Capture a live Valuable Event launcher-name median and its match bounds.

Run from the repository root, for example:
    venv\\Scripts\\python.exe -m tests.gift_claims.capture_valuable_launcher_median

The utility returns the selected device to the city, takes 50 fresh frames,
and replaces only the stable name crop. It neither opens an event nor claims a
reward.
"""
import argparse
import json
import threading
from pathlib import Path

import adbutils
import cv2
import numpy as np

from bot.activities.gift_claims.common import REFERENCE_WIDTH, return_home
from bot.context.bot_context import BotContext


FRAME_COUNT = 50
MIN_CAPTURE_MATCH = 0.70
MAX_CAPTURE_ATTEMPTS = 70
TEMPLATE_PATH = Path("Images/GiftClaims/ValuableEvent/launcher_name_median.png")
SEARCH_REGION = (40, 68, 88, 96)
REFERENCE_CROP = (232, 577)


def _bounds(screen, region):
    height, width = screen.shape[:2]
    x0, y0, x1, y1 = region
    return (int(width * x0 / 100), int(height * y0 / 100),
            int(width * x1 / 100), int(height * y1 / 100))


def _match_bounds(screen, template, region):
    left, top, right, bottom = _bounds(screen, region)
    area = screen[top:bottom, left:right]
    scores = cv2.matchTemplate(area, template, cv2.TM_CCOEFF_NORMED)
    _, score, _, (x, y) = cv2.minMaxLoc(scores)
    return float(score), (left + x, top + y)


def _outside_best(screen, template, region):
    left, top, right, bottom = _bounds(screen, region)
    scores = cv2.matchTemplate(screen[top:bottom, left:right], template,
                               cv2.TM_CCOEFF_NORMED)
    _, _, _, (x, y) = cv2.minMaxLoc(scores)
    height, width = template.shape[:2]
    scores[max(0, y - height):y + height + 1,
           max(0, x - width):x + width + 1] = -1.0
    return float(scores.max())


def build_from_frames(frames: list[np.ndarray], output: Path) -> dict:
    """Build a name median from same-size city frames and measure its bounds."""
    reference = cv2.imread(str(TEMPLATE_PATH))
    if reference is None:
        raise FileNotFoundError(TEMPLATE_PATH)
    height, width = reference.shape[:2]
    x, y = REFERENCE_CROP
    crops = [frame[y:y + height, x:x + width] for frame in frames]
    if any(crop.shape != reference.shape for crop in crops):
        raise RuntimeError("launcher crop left the screenshot bounds")
    median = np.median(np.stack(crops), axis=0).astype(np.uint8)
    if not cv2.imwrite(str(output), median):
        raise OSError(f"could not write {output}")
    real = [_match_bounds(frame, median, SEARCH_REGION)[0] for frame in frames]
    outside = [_outside_best(frame, median, SEARCH_REGION) for frame in frames]
    return {
        "frames": len(frames),
        "crop_xywh": [x, y, width, height],
        "real_min": round(min(real), 4),
        "real_median": round(float(np.median(real)), 4),
        "real_max": round(max(real), 4),
        "outside_max": round(max(outside), 4),
        "recommended_threshold": round((min(real) + max(outside)) / 2, 4),
    }


def capture(serial: str) -> dict:
    device = adbutils.adb.device(serial=serial)
    bot = BotContext(device, threading.Event(), None, lambda _message: None)
    if not return_home(bot):
        raise RuntimeError("could not return the device to the city")

    previous = cv2.imread(str(TEMPLATE_PATH))
    if previous is None:
        raise FileNotFoundError(TEMPLATE_PATH)
    first = bot.screenshot()
    initial_score, (x, y) = _match_bounds(first, previous, SEARCH_REGION)
    if initial_score < 0.70:
        raise RuntimeError(f"existing launcher crop did not match the city: {initial_score:.4f}")

    frames = []
    discarded = 0
    while len(frames) < FRAME_COUNT and len(frames) + discarded < MAX_CAPTURE_ATTEMPTS:
        frame = bot.screenshot()
        stable_score, _ = _match_bounds(frame, previous, SEARCH_REGION)
        if stable_score >= MIN_CAPTURE_MATCH:
            frames.append(frame)
        else:
            discarded += 1
    if len(frames) != FRAME_COUNT:
        raise RuntimeError("could not collect 50 stable city frames")
    result = build_from_frames(frames, TEMPLATE_PATH)
    result["discarded_transition_frames"] = discarded
    result["previous_score"] = round(initial_score, 4)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--serial", default="127.0.0.1:21513")
    parser.add_argument("--source-images", nargs="+", type=Path)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    if arguments.source_images:
        if arguments.output is None:
            parser.error("--output is required with --source-images")
        frames = [cv2.imread(str(path)) for path in arguments.source_images]
        if any(frame is None for frame in frames):
            parser.error("one or more --source-images could not be read")
        result = build_from_frames(frames, arguments.output)
    else:
        result = capture(arguments.serial)
    print(json.dumps(result, ensure_ascii=True))
