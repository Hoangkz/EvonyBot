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
import sys
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))    # chạy được cả `py real_run.py` từ thư mục tests
sys.stdout.reconfigure(encoding="utf-8")                            # log tiếng Việt không lỗi trên console Windows

import adbutils
import cv2

from bot.context import BotContext, StopRequested

SERIAL = os.environ.get("EVONY_SERIAL", "127.0.0.1:21913")   # máy khác: đặt EVONY_SERIAL=127.0.0.1:21913

# Việc coi như đã xong hôm nay khi bắt đầu, VD {"crazy_eggs_lucky_hammer"} để không dùng búa vàng.
DAILY_DONE: set[str] = set()


def target(bot):
    """Hàm cần test — sửa ở đây."""
    # EVONY_TEST=redeem: chỉ đổi quà event 3 ngày (đang ở sẵn màn event); three_day: cả event 3 ngày;
    # mặc định chạy nhiệm vụ Daily Trade Carriage.
    # if os.environ.get("EVONY_TEST") == "redeem":
    #     return test_three_day_redeem(bot)
    # if os.environ.get("EVONY_TEST") == "three_day":
    #     return test_three_day(bot)
    # if os.environ.get("EVONY_TEST") == "city_vip":
    #     # Route tạm dựng từ FIXED của civ1 (không lưu DB) để thử flow nhận VIP khi máy chưa quét route.
    #     from bot.activities.daily_activities import city_vip
    #     from bot.city.civ1 import city_tour
    #     bot.civilization = 1
    #     bot.city_map = {"keep": [0, 0], **city_tour.FIXED}
    #     return city_vip.claim_vip(bot)
    # if os.environ.get("EVONY_TEST") == "alliance_vip":
    #     from bot.activities.daily_activities import alliance_vip
    #     return alliance_vip.buy_vip(bot, True, True)
    # if os.environ.get("EVONY_TEST") == "rewards":
    #     from bot.activities.daily_activities import common
    #     return common.collect_activity_rewards(bot)
    # if os.environ.get("EVONY_TEST") == "open_task":
    #     return test_open_task(bot)
    # if os.environ.get("EVONY_TEST") == "greet":
    #     return test_greet_champion(bot)
    # if os.environ.get("EVONY_TEST") == "recruit":
    #     return test_recruit_general(bot)
    # if os.environ.get("EVONY_TEST") == "recruit_tap":
    #     return test_recruit_tap(bot)
    # if os.environ.get("EVONY_TEST") == "recruit_buy":
    #     return test_recruit_buy(bot)
    # if os.environ.get("EVONY_TEST") == "arc":
    return test_arc_sweep(bot)
    # return test_trade_carriage(bot)


def test_trade_carriage(bot):
    """Daily Trade Carriage, phần sau Go: đang ở sẵn màn Trade Carriage -> Dispatch tối đa 4 lần.
    EVONY_FROM_MAIN=1: chạy cả từ màn chính (Quests -> Activity -> Go)."""
    from bot.activities.daily_activities import common, trade_carriage
    if not os.environ.get("EVONY_FROM_MAIN"):
        return trade_carriage.after_go(bot)
    job = common.daily_job(trade_carriage.TASK, after_go=trade_carriage.after_go)
    return job["run"](bot, {})


def test_open_task(bot):
    """Daily: mở Quests -> Activity -> Claim All (nếu xanh) -> tìm dòng nhiệm vụ, KHÔNG bấm Go (tap_go=False).
    EVONY_TASK=<tên module> (mặc định black_market). Bắt đầu từ màn chính."""
    from importlib import import_module
    from bot.activities.daily_activities import common
    name = os.environ.get("EVONY_TASK", "black_market")
    task = import_module(f"bot.activities.daily_activities.{name}").TASK
    result = common.open_task(bot, common.task_titles(task), common.task_cards(task),
                              done_cards=common.task_done_cards(task), tap_go=False)
    bot.log(f"open_task({name}, tap_go=False) -> {result}")
    return result


def _db_city_map() -> dict:
    """Route công trình của máy SERIAL đã lưu trong DB của app (chỉ đọc), {} nếu chưa có."""
    import json
    import sqlite3
    import database
    conn = sqlite3.connect(database.DB_PATH)
    try:
        row = conn.execute("SELECT city_map FROM devices WHERE serial = ?", (SERIAL,)).fetchone()
    finally:
        conn.close()
    return json.loads(row[0]) if row and row[0] else {}


def test_recruit_general(bot):
    """Activity Recruit General (chạy một mình): chưa có route thì quét (route chỉ giữ trong bộ nhớ của lần chạy, không lưu DB) ->
    Tavern -> Recruit General -> tích Historic / bỏ Epic -> Refresh liên tục... EVONY_BUY=Buy General Token đổi nút mua (mặc định
    Recruit General)."""
    from bot.activities import recruit_general
    bot.civilization = None
    bot.set_civilization = lambda civ: setattr(bot, "civilization", civ)
    bot.city_map = _db_city_map()   # route đã lưu trong DB (chưa có thì activity quét)
    bot.set_city_map = lambda city_map: setattr(bot, "city_map", city_map)
    return recruit_general.run(bot, {"buy_with": os.environ.get("EVONY_BUY", "Recruit General")})


def test_arc_sweep(bot):
    """Đang ở bản đồ thế giới: quét cung quanh chỗ camera đang đứng (bot/common/arc_scan.py).
    EVONY_DEG="bắt đầu,kết thúc" (độ 0 .. 360, ngược chiều kim đồng hồ từ bắt đầu tới kết thúc; mặc định 345,15; 0,360 = cả vòng tròn), EVONY_R = bán kính km (mặc định 40).
    góc theo màn hình: 0° = ngang sang phải, 90° = thẳng lên. Chạy tay: tests/run_arc.py (không cần env)."""
    from bot.common.arc_sweep import arc_sweep
    start, end = (float(d) for d in os.environ.get("EVONY_DEG", "345,15").split(","))
    radius = float(os.environ.get("EVONY_R", 40))
    return arc_sweep(bot, start, end, radius)


def test_recruit_buy(bot):
    """Recruit General MUA THẬT, chạy liên tục tới khi mua đủ BUY_LIMIT (3) tướng: tướng nào có vương miện cũng coi là cần mua (không xét
    tên), mua bằng nút theo EVONY_BUY (mặc định Recruit General). EVONY_SHOT=<file.png>: lưu ảnh màn hình khi kết thúc. TỐN VÀNG."""
    import importlib
    module = importlib.import_module("bot.activities.recruit_general.run")
    module._wanted_general = lambda b: "ANY-CROWNED-GENERAL"
    bot.civilization = None
    bot.set_civilization = lambda civ: setattr(bot, "civilization", civ)
    bot.city_map = _db_city_map()
    bot.set_city_map = lambda city_map: setattr(bot, "city_map", city_map)
    try:
        return module.run(bot, {"buy_with": os.environ.get("EVONY_BUY", "Recruit General")})
    finally:
        shot = os.environ.get("EVONY_SHOT")
        if shot:
            cv2.imwrite(shot, bot.screenshot())


def test_recruit_tap(bot):
    """Recruit General tới bước BẤM VÀO TƯỚNG, KHÔNG mua: tướng xịn nào có vương miện cũng coi là "cần mua" (giả), bấm vào tướng, chờ màn
    chi tiết, ghi có thấy nút Recruit General / Buy General Token không, Back về danh sách rồi dừng. Không bấm nút mua."""
    import importlib
    from bot.activities.recruit_general.constants import (DETAIL_BUY_TOKEN, DETAIL_RECRUIT, DETAIL_THRESHOLD, DETAIL_WAIT,
                                                          GENERAL_ART, REFRESH, THRESHOLD)
    module = importlib.import_module("bot.activities.recruit_general.run")

    def fake_buy(b, name, buy_with="Recruit General"):
        b.record(f"TEST: tap the General ({name}), no buy")
        b.tap_percent(*GENERAL_ART)
        for waited in range(1, DETAIL_WAIT + 1):
            b.sleep(1)
            screen = b.screenshot()
            if b.find(REFRESH, screen=screen, threshold=THRESHOLD) is None:
                recruit = b.find(DETAIL_RECRUIT, screen=screen, threshold=DETAIL_THRESHOLD)
                token = b.find(DETAIL_BUY_TOKEN, screen=screen, threshold=DETAIL_THRESHOLD)
                b.record(f"TEST: detail screen after {waited}s: Recruit button {recruit}, Buy Token button {token}")
                break
        else:
            b.record(f"TEST: detail screen NOT shown after {DETAIL_WAIT}s")
        b.back(delay=1)
        raise StopRequested()

    module._wanted_general = lambda b: "TEST-GENERAL"
    module._buy = fake_buy
    bot.civilization = None
    bot.set_civilization = lambda civ: setattr(bot, "civilization", civ)
    bot.city_map = _db_city_map()   # route đã lưu trong DB (chưa có thì activity quét)
    bot.set_city_map = lambda city_map: setattr(bot, "city_map", city_map)
    bot.log(f"route từ DB: {len(bot.city_map)} công trình")
    return module.run(bot, {})


def test_greet_champion(bot):
    """Daily Greet Champion, phần sau Go: đang ở sẵn màn thành chính. EVONY_FROM_MAIN=1: chạy cả từ màn chính."""
    from bot.activities.daily_activities import common, greet_champion
    if not os.environ.get("EVONY_FROM_MAIN"):
        return greet_champion.after_go(bot)
    job = common.daily_job(greet_champion.TASK, after_go=greet_champion.after_go)
    return job["run"](bot, {})


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
    """Event 3 ngày: mốc đầy đủ (Alliance 60, Heal 30000), quà theo thứ tự ưu tiên trong event.py."""
    from bot.activities.event_center import three_day
    from ui.tabs.event import DATA
    group = next(g for g in DATA["groups"] if g.get("key") == "three_day")
    settings = {"three_day_alliance": {"value": 60}, "three_day_heal": {"value": 30000},
                "three_day_redeem": {"order": [i["id"] for i in group["redeem"]["items"]]}}
    bot.settings = {"Event": settings}
    return three_day.run(bot, settings)


def test_three_day_redeem(bot):
    """Chỉ phần đổi quà của event 3 ngày: đang ở sẵn màn event, bấm sang tab Redeem rồi đổi theo thứ tự ưu tiên trong
    event.py."""
    import importlib
    run_module = importlib.import_module("bot.activities.event_center.three_day.run")
    from ui.tabs.event import DATA
    group = next(g for g in DATA["groups"] if g.get("key") == "three_day")
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
