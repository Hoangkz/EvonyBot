"""Run one Daily Activities task against a connected emulator.

This is intentionally outside unittest discovery. It records matched templates
and every input action under ``test-results/daily-live`` for real-device flow
audits without going through the PyQt UI.
"""
import argparse
import json
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path

import adbutils

from bot.activities.daily_activities.run import REWARDS, TASKS, _run_task, run as run_daily
from bot.context import BotContext, BotInterrupted


class TracedDevice:
    def __init__(self, device, events):
        self._device = device
        self.serial = device.serial
        self.events = events

    def _event(self, kind, **data):
        self.events.append({"at": datetime.now().isoformat(timespec="milliseconds"),
                            "kind": kind, **data})

    def screenshot(self):
        return self._device.screenshot()

    def click(self, x, y):
        self._event("tap", x=int(x), y=int(y))
        return self._device.click(x, y)

    def swipe(self, x1, y1, x2, y2, duration):
        self._event("swipe", x1=int(x1), y1=int(y1), x2=int(x2), y2=int(y2),
                    duration=float(duration))
        return self._device.swipe(x1, y1, x2, y2, duration)

    def keyevent(self, key):
        self._event("key", key=str(key))
        return self._device.keyevent(key)

    def shell(self, command):
        self._event("shell", command=command)
        return self._device.shell(command)

    def window_size(self):
        return self._device.window_size()


class TracedContext(BotContext):
    def __init__(self, device, stop_event, deadline, log, events):
        super().__init__(device, stop_event, deadline, log)
        self.events = events

    def find(self, template, *args, **kwargs):
        pos = super().find(template, *args, **kwargs)
        if pos is not None and isinstance(template, str):
            self.events.append({"at": datetime.now().isoformat(timespec="milliseconds"),
                                "kind": "match", "template": template,
                                "position": [int(pos[0]), int(pos[1])],
                                "region": kwargs.get("region")})
        return pos


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("task", choices=[task.label for task in TASKS] + ["ALL"])
    parser.add_argument("--serial", default="127.0.0.1:21503")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--monster-marches", type=int, default=0,
                        help="Resume Monster Killing trace after confirmed marches")
    parser.add_argument("--pre-done", action="append", default=[],
                        choices=[task.label for task in TASKS],
                        help="Task already completed/claimed before this audit run")
    args = parser.parse_args()

    task = None if args.task == "ALL" else next(
        task for task in TASKS if task.label == args.task)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_name = args.task.lower().replace(" ", "-")
    result_dir = Path("test-results/daily-live") / f"{stamp}-{safe_name}"
    result_dir.mkdir(parents=True, exist_ok=True)

    events = []
    raw_device = adbutils.adb.device(args.serial)
    device = TracedDevice(raw_device, events)
    logs = []

    def log(message):
        text = str(message)
        logs.append(text)
        print(text, flush=True)

    raw_device.screenshot().save(result_dir / "before.png")
    ctx = TracedContext(device, threading.Event(), time.monotonic() + args.timeout,
                        log, events)
    ctx._daily_monster_marches = max(0, args.monster_marches)
    ctx._daily_monster_first_claimed = args.monster_marches >= 2
    daily_done = set(args.pre_done)
    ctx.is_daily_done = daily_done.__contains__
    ctx.mark_daily_done = daily_done.add
    status, completed, passes = "unknown", False, 0
    try:
        if args.task == "ALL":
            run_daily(ctx, {item.label: True for item in TASKS})
            completed = (all(item.label in daily_done for item in TASKS)
                         and REWARDS in daily_done)
            status = "full-flow-complete" if completed else "full-flow-incomplete"
        else:
            for passes in range(1, 6):
                log(f"LIVE {args.task}: pass {passes}/5")
                if _run_task(ctx, task):
                    completed = True
                    status = "task-complete"
                    break
            else:
                status = "five-passes-performed-without-completion"
    except BotInterrupted as error:
        status = type(error).__name__
    except Exception as error:
        status = f"error: {type(error).__name__}: {error}"
        logs.append(traceback.format_exc())
    finally:
        raw_device.screenshot().save(result_dir / "after.png")
        report = {"task": args.task, "serial": args.serial, "status": status,
                  "completed": completed, "passes": passes, "logs": logs,
                  "daily_done": sorted(daily_done), "events": events}
        (result_dir / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"result_dir": str(result_dir), "status": status,
                          "completed": completed, "passes": passes,
                          "event_count": len(events)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
