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
import os
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path

import adbutils
import cv2

from bot.context import BotContext, StopRequested

SERIAL = os.environ.get("EVONY_SERIAL", "127.0.0.1:21923")   # máy khác: đặt EVONY_SERIAL=127.0.0.1:21913

# Việc coi như đã xong hôm nay khi bắt đầu, VD {"crazy_eggs_lucky_hammer"} để không dùng búa vàng.
DAILY_DONE: set[str] = set()


def target(bot):
    """Hàm cần test — sửa ở đây."""
    # EVONY_TEST=redeem: chỉ đổi quà event 3 ngày (đang ở sẵn màn event); mặc định chạy cả event 3 ngày.
    if os.environ.get("EVONY_TEST") == "redeem":
        return test_three_day_redeem(bot)
    return test_three_day(bot)


def main():
    parser = argparse.ArgumentParser(description=f"Chạy thật target() trên {SERIAL}.")
    parser.add_argument("--shots", action="store_true", help="lưu mọi ảnh bot chụp vào thư mục tạm")
    args = parser.parse_args()

    start = time.monotonic()

    def log(message: str):
        print(f"[{time.monotonic() - start:7.1f}s] {message}", flush=True)

    stop = threading.Event()
    try:
        log(f"adb connect {SERIAL}: {adbutils.adb.connect(SERIAL, timeout=5)}")
    except Exception as e:   # giả lập chưa mở / đã nối sẵn: vẫn thử lấy thiết bị bên dưới
        log(f"adb connect {SERIAL} lỗi: {e}")
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

def test_three_day(bot):
    """Event 3 ngày: mốc đầy đủ (Alliance 60, Heal 30000), quà theo thứ tự ưu tiên trong event.json."""
    import json
    from pathlib import Path
    from bot.activities.event_center import three_day
    data = json.loads((Path(__file__).parents[1] / "ui/tabs/event.json").read_text(encoding="utf-8-sig"))
    group = next(g for g in data["groups"] if g.get("key") == "three_day")
    settings = {"three_day_alliance": {"value": 60}, "three_day_heal": {"value": 30000},
                "three_day_redeem": {"order": [i["id"] for i in group["redeem"]["items"]]}}
    bot.settings = {"Event": settings}
    return three_day.run(bot, settings)


def test_three_day_redeem(bot):
    """Chỉ phần đổi quà của event 3 ngày: đang ở sẵn màn event, bấm sang tab Redeem rồi đổi theo thứ tự ưu tiên trong
    event.json."""
    import importlib
    import json
    from pathlib import Path
    run_module = importlib.import_module("bot.activities.event_center.three_day.run")
    data = json.loads((Path(__file__).parents[1] / "ui/tabs/event.json").read_text(encoding="utf-8-sig"))
    group = next(g for g in data["groups"] if g.get("key") == "three_day")
    return run_module._claim_and_redeem(bot, [i["id"] for i in group["redeem"]["items"]])


def test_heal_from_hospital(bot):
    """Đang ở sẵn màn Hospital (nhiệm vụ Heal 30000 của event 3 ngày): chạy phần Heal từ Reset tới Finish All."""
    import importlib
    hr = importlib.import_module("bot.activities.event.kings_path.heal.run")
    from bot.activities.event.kings_path.heal.constants import HEAL_ATTEMPTS, SPEED_UP
    for attempt in range(1, HEAL_ATTEMPTS + 1):
        hr._reset_and_scroll(bot)
        result = hr._heal_rows(bot, 30000)
        if result != hr._RETRY:
            break
        bot.log(f"nút Heal chưa sáng, làm lại ({attempt})")
    bot.log(f"_heal_rows -> {result!r}")
    if result is True:
        speed_up = bot.wait_for(SPEED_UP, timeout=10)
        bot.log(f"Speed Up: {speed_up}")
        if speed_up is not None:
            bot.tap(*speed_up, delay=hr.EXTRA_WAIT)
            bot.log(f"_finish_all -> {hr._finish_all(bot)}")


if __name__ == "__main__":
    main()
