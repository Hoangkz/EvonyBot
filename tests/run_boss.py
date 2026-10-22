"""
run_boss.py — chạy tay cả luồng tìm boss + chia sẻ liên minh trên một giả lập đang ở bản đồ thế giới (quét hình quạt, nhận boss, chia sẻ boss đang tích chưa chia sẻ).

    py tests/run_boss.py 127.0.0.1:21913 [SERVER] [BÁN_KÍNH] [GÓC_ĐẦU] [GÓC_CUỐI]      (mặc định server 1835, bán kính 100, 0 -> 360 = cả vòng)

Thật sự gửi tin vào chat liên minh. Ctrl+C để dừng. Ảnh chụp lúc có lỗi / thấy boss lưu vào thư mục tạm (không vào test-results).
"""
import sys
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import adbutils
import cv2

from bot.common import boss_scan
from bot.context import BotContext


def main():
    serial = sys.argv[1]
    server = sys.argv[2] if len(sys.argv) > 2 else "1835"
    radius = float(sys.argv[3]) if len(sys.argv) > 3 else 100
    start_deg = float(sys.argv[4]) if len(sys.argv) > 4 else 0
    end_deg = float(sys.argv[5]) if len(sys.argv) > 5 else 360
    shots = Path(tempfile.gettempdir()) / "evonybot_boss_run" / serial.replace(":", "_") / datetime.now().strftime("%Y%m%d-%H%M%S")
    shots.mkdir(parents=True, exist_ok=True)
    began = time.monotonic()
    tag = serial[-5:]

    def log(message: str):
        print(f"[{tag} {time.monotonic() - began:7.1f}s] {message}", flush=True)

    try:
        adbutils.adb.connect(serial, timeout=5)
    except Exception as e:
        log(f"adb connect lỗi: {e}")
    bot = BotContext(adbutils.adb.device(serial=serial), threading.Event(), None, log)
    bot.server = server
    log(f"server {server}, bán kính {radius}, góc {start_deg} -> {end_deg}, ảnh lưu ở {shots}")

    count = [0]

    def save(label: str, screen=None):
        count[0] += 1
        cv2.imwrite(str(shots / f"{count[0]:04d}_{label}.png"), screen if screen is not None else bot.screenshot())

    original_log = bot.log

    def watch(message: str):
        original_log(message)
        if "không thấy" in message or "bỏ qua" in message or "không đọc được" in message:
            save("loi")
    bot.log = watch

    original_find = boss_scan.find_bosses

    def traced(screen):
        found = original_find(screen)
        if found:
            log("find_bosses: " + "; ".join(f"{b['text'] or '?'} lv{b['level']} {'MỘT PHẦN' if b.get('partial') else ''}{'*' if b['active'] else ''} @{b['pos']}" for b in found))
            save("boss", screen)
        return found
    boss_scan.find_bosses = traced

    original_centre = boss_scan.centre_boss

    def traced_centre(bot_, pos):
        moved = original_centre(bot_, pos)
        save("keo")
        return moved
    boss_scan.centre_boss = traced_centre

    original_popup = boss_scan.read_popup

    def traced_popup(screen):
        info = original_popup(screen)
        log(f"read_popup: {info}")
        save("popup", screen)
        return info
    boss_scan.read_popup = traced_popup

    if not boss_scan.ensure_map(bot):
        log("không về được bản đồ sạch, dừng")
        return
    result = boss_scan.scan_bosses(bot, start_deg, end_deg, radius)
    log(f"XONG: {len(result)} boss")
    for boss in result:
        log(str(boss))


if __name__ == "__main__":
    main()
