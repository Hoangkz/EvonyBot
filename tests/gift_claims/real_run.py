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
from bot.context import BotContext


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--serial", required=True)
    parser.add_argument("--task", action="append", help="gift_* key; repeat to run several")
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

    if not args.task:
        log("START complete gift-claim flow")
        gift_claims.run(bot)
        log("END complete gift-claim flow")
        log(f"daily_done: {done}")
        return

    wanted = set(args.task)
    tasks = [task for task in gift_claims.TASKS if not wanted or task.key in wanted]
    missing = wanted - {task.key for task in tasks}
    if missing:
        raise SystemExit("Unknown task(s): " + ", ".join(sorted(missing)))

    for task in tasks:
        log(f"START {task.key} ({task.label})")
        result = task.run(bot)
        log(f"END {task.key}: {result!r}")
        bot.mark_daily_done(task.key)
    log(f"daily_done: {done}")


if __name__ == "__main__":
    main()
