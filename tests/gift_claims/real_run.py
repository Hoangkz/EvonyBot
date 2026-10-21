r"""Chạy thật một hoạt động quà trên thiết bị ADB (không lưu log/ảnh vào test-results/).

Ví dụ:
    venv\Scripts\python.exe -m tests.gift_claims.real_run --serial 127.0.0.1:21513 --zone valuable_event
    venv\Scripts\python.exe -m tests.gift_claims.real_run --serial 127.0.0.1:21513 --zone event_center --slice-seconds 120
    # Chỉ bật --shots khi cần phân tích nhận diện ảnh; ảnh được lưu trong thư mục tạm.
    venv\Scripts\python.exe -m tests.gift_claims.real_run --serial 127.0.0.1:21513 --zone event_center --shots
"""
import argparse
import sys
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path

import adbutils
import cv2

from bot.activities import gift_claims
from bot.activities.gift_claims.event_center import zone as event_center_zone
from bot.activities.gift_claims.valuable_event import zone as valuable_event_zone
from bot.activities.gift_claims.valuable_event.super_value_return import zone as super_value_return_zone
from bot.context import BotContext
from bot.context import BotInterrupted

ZONES = {
    "valuable_event": gift_claims.valuable_event,
    "super_value_return": gift_claims.super_value_return,
    "event_center": gift_claims.event_center,
}
ZONE_TASKS = {
    "event_center": event_center_zone.TASKS,
    "valuable_event": [(task.key, task.label) for task in valuable_event_zone.TASKS],
    "super_value_return": [
        (task.key, task.label) for task in super_value_return_zone.TASKS
    ],
}
TASKS_BY_ZONE = {
    zone: {key.removeprefix("gift_"): key for key, _label in tasks}
    for zone, tasks in ZONE_TASKS.items()
}
ALL_TASKS = sorted(set().union(*(tasks for tasks in TASKS_BY_ZONE.values())))


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--serial", required=True)
    parser.add_argument("--zone", required=True, choices=sorted(ZONES), help="hoạt động cần chạy")
    parser.add_argument(
        "--task", choices=ALL_TASKS,
        help="chỉ chạy một task trong zone đã chọn; task khác được giả lập DONE trong bộ nhớ",
    )
    parser.add_argument("--slice-seconds", type=float,
                        help="mô phỏng worker nhường Join Boss sau số giây này rồi chạy tiếp; bỏ đi để chạy tới khi xong")
    parser.add_argument("--max-slices", type=int, help="dừng sau số lát này")
    parser.add_argument("--shots", action="store_true",
                        help="lưu mọi ảnh bot chụp vào thư mục tạm để chẩn đoán nhận diện")
    args = parser.parse_args()
    if args.task and args.task not in TASKS_BY_ZONE[args.zone]:
        parser.error(f"--task {args.task} không thuộc --zone {args.zone}")

    start = time.monotonic()
    log = lambda message: print(f"[{time.monotonic() - start:7.1f}s] {message}", flush=True)
    bot = BotContext(adbutils.adb.device(serial=args.serial), threading.Event(), None, log)
    bot.record = log
    done = {}
    if args.task:
        target_key = TASKS_BY_ZONE[args.zone][args.task]
        timestamp = datetime.now().isoformat(timespec="seconds")
        zone_tasks = ZONE_TASKS[args.zone]
        done.update({key: timestamp for key, _label in zone_tasks if key != target_key})
        log(f"chỉ test task: {args.task} ({target_key})")
    bot.is_daily_done = done.__contains__
    bot.mark_daily_done = lambda key: done.__setitem__(key, datetime.now().isoformat(timespec="seconds"))
    bot.done_at = done.get
    bot.forget_daily = lambda key: done.pop(key, None)

    if args.shots:
        output = (Path(tempfile.gettempdir()) / "evonybot_gift_claims" /
                  datetime.now().strftime("%Y%m%d-%H%M%S"))
        output.mkdir(parents=True, exist_ok=True)
        screenshot, count = bot.screenshot, [0]

        def save_screenshot():
            image = screenshot()
            count[0] += 1
            cv2.imwrite(str(output / f"{count[0]:04d}.png"), image)
            return image

        bot.screenshot = save_screenshot
        log(f"screenshots: {output.resolve()}")

    zone = ZONES[args.zone]
    finished, slices = False, 0
    while not finished and (args.max_slices is None or slices < args.max_slices):
        slices += 1
        bot._deadline = time.monotonic() + args.slice_seconds if args.slice_seconds else None
        try:
            finished = zone.run(bot)
        except BotInterrupted as exc:
            log(f"YIELD lát {slices} ({type(exc).__name__}); mô phỏng Join Boss rồi chạy tiếp")
        finally:
            bot._deadline = None
    log(f"{args.zone} xong: {finished}; số lát: {slices}")
    log(f"daily_done: {sorted(done)}")


if __name__ == "__main__":
    main()
