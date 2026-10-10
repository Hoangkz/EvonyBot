r"""Run one or all gift-claim modules on a real ADB device.

Examples:
    venv\Scripts\python.exe -m tests.gift_claims.real_run --serial 127.0.0.1:21513
    venv\Scripts\python.exe -m tests.gift_claims.real_run --task gift_limited_offer --shots
"""
import argparse
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import adbutils
import cv2

from bot.activities import gift_claims
from bot.activities.gift_claims import event_center
from bot.context import BotContext
from bot.context import BotInterrupted


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--serial", required=True)
    parser.add_argument("--task", action="append", help="gift_* key; repeat to run several")
    parser.add_argument("--slice-seconds", type=float,
                        help="simulate the worker time slice and resume after timeout")
    parser.add_argument("--zone2", action="store_true",
                        help="start the combined flow at the right-rail boundary")
    parser.add_argument("--max-slices", type=int,
                        help="stop a live diagnostic after this many slices")
    parser.add_argument("--shots", action="store_true")
    args = parser.parse_args()

    start = time.monotonic()
    log = lambda message: print(f"[{time.monotonic() - start:7.1f}s] {message}", flush=True)
    bot = BotContext(adbutils.adb.device(serial=args.serial), threading.Event(), None, log)
    bot.record = log
    done = {}
    bot.is_daily_done = done.__contains__
    bot.mark_daily_done = lambda key: done.__setitem__(key, datetime.now().isoformat(timespec="seconds"))

    if args.shots:
        output = Path("tests/gift_claims/adb_runs") / datetime.now().strftime("%Y%m%d-%H%M%S")
        output.mkdir(parents=True, exist_ok=True)
        screenshot, count = bot.screenshot, [0]

        def save_screenshot():
            image = screenshot()
            count[0] += 1
            cv2.imwrite(str(output / f"{count[0]:04d}.png"), image)
            return image

        bot.screenshot = save_screenshot
        log(f"screenshots: {output.resolve()}")

    if args.task:
        if args.task != [event_center.KEY]:
            raise SystemExit(f"live diagnostic only supports {event_center.KEY}")
        bot._deadline = (time.monotonic() + args.slice_seconds
                         if args.slice_seconds else None)
        try:
            clean = event_center.run_opened(bot)
            log(f"Event Center clean: {clean}")
        except BotInterrupted as exc:
            log(f"Event Center yield: {type(exc).__name__}")
        finally:
            bot._deadline = None
        return

    if not args.task:
        log("START complete gift-claim flow")
        if args.zone2:
            bot._gift_claims_progress = gift_claims.GiftProgress(boundary_index=1)
        slices = 0
        while not bot.is_daily_done(gift_claims.KEY):
            if args.max_slices is not None and slices >= args.max_slices:
                break
            slices += 1
            bot._deadline = (time.monotonic() + args.slice_seconds
                             if args.slice_seconds else None)
            try:
                gift_claims.run(bot)
            except BotInterrupted as exc:
                log(f"YIELD slice {slices} ({type(exc).__name__}); "
                    "simulating Join Boss then resume")
            finally:
                bot._deadline = None
        log("END complete gift-claim flow")
        log(f"slices: {slices}")
        log(f"daily_done: {done}")
        progress = getattr(bot, "_gift_claims_progress", None)
        if progress is not None:
            log(f"boundary_index: {progress.boundary_index}")
            log(f"unresolved: {sorted(item.value for item in progress.unresolved_parents)}")
            log(f"outcomes: {progress.outcomes}")
        return

if __name__ == "__main__":
    main()
