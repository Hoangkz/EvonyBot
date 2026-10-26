"""Calibrate the Soul of Spiritual Beast reward-chest detector from live ADB.

The utility never taps or navigates.  It accepts only frames which still show
``Challenge Quest``, captures the fixed green-frame chest rectangle, and writes
the median chest crop plus measured genuine/distractor bounds.

Run from the repository root:

    venv\\Scripts\\python.exe -m tests.gift_claims.capture_soul_beast_chest \
        --serial 127.0.0.1:21513
"""
import argparse
import json
import threading
import time
from pathlib import Path

import adbutils
import cv2
import numpy as np

from bot.activities.gift_claims.common import REFERENCE_WIDTH, find
from bot.activities.gift_claims.valuable_event.soul_of_spiritual_beast.run import (
    CHALLENGE_QUEST,
    MAIN_CHEST_REGION,
)
from bot.context import BotContext


FRAME_COUNT = 50
MAX_ATTEMPTS = 75
MIN_SOURCE_SCORE = 0.60
SOURCE_TEMPLATE = Path("Images/GiftClaims/Common/button_reward_chest.png")
TARGET_TEMPLATE = Path(
    "Images/GiftClaims/SuperValueReturn/SoulOfSpiritualBeast/"
    "button_reward_chest_median.png"
)


def _bounds(screen, region):
    height, width = screen.shape[:2]
    left, top, right, bottom = region
    return (round(width * left / 100), round(height * top / 100),
            round(width * right / 100), round(height * bottom / 100))


def _scale(template, screen):
    factor = screen.shape[1] / REFERENCE_WIDTH
    width = max(1, round(template.shape[1] * factor))
    height = max(1, round(template.shape[0] * factor))
    interpolation = cv2.INTER_AREA if factor < 1 else cv2.INTER_CUBIC
    return cv2.resize(template, (width, height), interpolation=interpolation)


def _best_match(screen, template):
    left, top, right, bottom = _bounds(screen, MAIN_CHEST_REGION)
    scores = cv2.matchTemplate(screen[top:bottom, left:right], template,
                               cv2.TM_CCOEFF_NORMED)
    _, score, _, (x, y) = cv2.minMaxLoc(scores)
    return float(score), (left + x, top + y)


def _distractor_score(screen, template, location):
    """Best alternate match in the same green rectangle, excluding the chest."""
    left, top, right, bottom = _bounds(screen, MAIN_CHEST_REGION)
    scores = cv2.matchTemplate(screen[top:bottom, left:right], template,
                               cv2.TM_CCOEFF_NORMED)
    x = location[0] - left
    y = location[1] - top
    height, width = template.shape[:2]
    scores[max(0, y - height):y + height + 1,
           max(0, x - width):x + width + 1] = -1.0
    return float(scores.max())


def _chest_crop(screen, location, template):
    x, y = location
    height, width = template.shape[:2]
    crop = screen[y:y + height, x:x + width]
    if crop.shape != template.shape:
        raise RuntimeError("reward chest crop left the screenshot bounds")
    return crop


def _is_soul_main(bot, screen):
    return find(bot, CHALLENGE_QUEST, screen, threshold=0.78,
                region=(55, 30, 100, 55)) is not None


def _stats(values):
    return {
        "min": round(float(min(values)), 4),
        "median": round(float(np.median(values)), 4),
        "max": round(float(max(values)), 4),
    }


def capture(serial: str, frame_count: int = FRAME_COUNT):
    device = adbutils.adb.device(serial=serial)
    bot = BotContext(device, threading.Event(), None, lambda _message: None)
    source = cv2.imread(str(SOURCE_TEMPLATE))
    if source is None:
        raise FileNotFoundError(SOURCE_TEMPLATE)

    accepted = []
    rejected = {"not_soul_main": 0, "no_source_chest": 0}
    while len(accepted) < frame_count and sum(rejected.values()) + len(accepted) < MAX_ATTEMPTS:
        screen = bot.screenshot()
        if not _is_soul_main(bot, screen):
            rejected["not_soul_main"] += 1
            time.sleep(0.2)
            continue
        template = _scale(source, screen)
        score, location = _best_match(screen, template)
        if score < MIN_SOURCE_SCORE:
            rejected["no_source_chest"] += 1
            time.sleep(0.2)
            continue
        accepted.append((screen, location, template))
        time.sleep(0.12)

    if len(accepted) != frame_count:
        raise RuntimeError(
            f"only captured {len(accepted)}/{frame_count} stable Soul Beast "
            f"chest frames; rejected={rejected}"
        )

    first_template = accepted[0][2]
    crops = [_chest_crop(screen, location, template)
             for screen, location, template in accepted]
    median = np.median(np.stack(crops), axis=0).astype(np.uint8)
    if median.shape != first_template.shape:
        raise RuntimeError("median chest shape changed during capture")

    TARGET_TEMPLATE.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(TARGET_TEMPLATE), median):
        raise OSError(f"could not write {TARGET_TEMPLATE}")

    genuine = []
    distractors = []
    locations = []
    for screen, location, _template in accepted:
        scaled = _scale(median, screen)
        score, detected = _best_match(screen, scaled)
        genuine.append(score)
        distractors.append(_distractor_score(screen, scaled, detected))
        locations.append(detected)
    threshold = (min(genuine) + max(distractors)) / 2
    return {
        "frames": len(accepted),
        "rejected": rejected,
        "template": str(TARGET_TEMPLATE).replace("\\\\", "/"),
        "crop_size": [int(median.shape[1]), int(median.shape[0])],
        "genuine": _stats(genuine),
        "distractor": _stats(distractors),
        "recommended_threshold": round(float(threshold), 4),
        "match_locations": {
            "first": list(locations[0]),
            "last": list(locations[-1]),
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--serial", default="127.0.0.1:21513")
    parser.add_argument("--frames", type=int, default=FRAME_COUNT)
    args = parser.parse_args()
    print(json.dumps(capture(args.serial, args.frames), ensure_ascii=False))
