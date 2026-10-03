"""
real_run.py — chạy THẬT một hàm của bot trên giả lập SERIAL (không phải unit test: tên file không
bắt đầu bằng "test" nên `unittest discover` không chạy nó).

    venv\\Scripts\\poe test            (hoặc: .\\venv\\Scripts\\python.exe -m tests.real_run)
    venv\\Scripts\\poe test --shots    lưu mọi ảnh bot chụp vào thư mục tạm (in đường dẫn)

Muốn test hàm khác: sửa `target()` bên dưới (và DAILY_DONE nếu cần nạp sẵn việc đã xong hôm nay).
daily_done chỉ giữ trong bộ nhớ của lần chạy, không đụng DB của app; in ra cuối lần chạy.
Ctrl+C để dừng.
"""
import argparse
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path

import adbutils
import cv2

from bot.context import BotContext, StopRequested

SERIAL = "127.0.0.1:21923"

# Việc coi như đã xong hôm nay khi bắt đầu, VD {"crazy_eggs_lucky_hammer"} để không dùng búa vàng.
DAILY_DONE: set[str] = set()


def target(bot):
    """Hàm cần test — sửa ở đây."""
    return test_crazy_eggs(bot)


def main():
    parser = argparse.ArgumentParser(description=f"Chạy thật target() trên {SERIAL}.")
    parser.add_argument("--shots", action="store_true", help="lưu mọi ảnh bot chụp vào thư mục tạm")
    args = parser.parse_args()

    start = time.monotonic()

    def log(message: str):
        print(f"[{time.monotonic() - start:7.1f}s] {message}", flush=True)

    stop = threading.Event()
    bot = BotContext(adbutils.adb.device(serial=SERIAL), stop, None, log)
    now = lambda: datetime.now().isoformat(timespec="seconds")
    done = {task: now() for task in DAILY_DONE}
    bot.is_daily_done = lambda task: task in done
    bot.mark_daily_done = lambda task: done.__setitem__(task, now())

    if args.shots:
        shots = Path(tempfile.gettempdir()) / "evonybot_real_run" / datetime.now().strftime("%Y%m%d-%H%M%S")
        shots.mkdir(parents=True, exist_ok=True)
        log(f"lưu ảnh vào {shots}")
        screenshot, count = bot.screenshot, [0]

        def saving_screenshot():
            image = screenshot()
            count[0] += 1
            cv2.imwrite(str(shots / f"{count[0]:04d}.png"), image)
            return image
        bot.screenshot = saving_screenshot

    log(f"chạy target() trên {SERIAL}")
    try:
        result = target(bot)
        log(f"return {result!r}")
    except KeyboardInterrupt:
        stop.set()
        log("Ctrl+C: dừng")
    except StopRequested:
        log("dừng")
    log(f"daily_done: {done}")



def test_crazy_eggs(bot):
    from bot.activities.event_center import crazy_eggs
    return crazy_eggs.run(bot, {})

if __name__ == "__main__":
    main()