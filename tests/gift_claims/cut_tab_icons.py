r"""Cắt ảnh icon tab (chỉ phần hình, KHÔNG có chữ tên tab) cho các event Valuable Event, từ máy thật.

Dải thông báo chạy chữ ("My Liege, ...") đè lên dòng tên tab (y ~98-112 trên màn 396x704), nên ảnh tab có chữ khớp kém khi
có thông báo. Script đi hết hàng tab, với mỗi event trong SPECS tìm thấy (bằng ảnh tab cũ) thì cắt phần hình bên trong icon:

- y ICON_Y (phía trên dòng tên tab);
- tâm icon lấy theo dải sáng của khung icon ở các hàng ICON_SPAN_Y (dưới chấm đỏ thông báo), không theo tâm ảnh chữ cũ
  (các ảnh "Acti", "Tomb", "heel of Dragon War" cắt lệch);
- rộng tâm +- ICON_HALF (bỏ khung cánh vàng hai bên — icon nào cũng có — và chấm đỏ góc trên phải).

Ra Images/GiftClaims/ValuableEvent/<Event>/tab_icon.png (ảnh cũ không đụng tới). Chỉ in ra stdout, không lưu log.

    venv\Scripts\python.exe -m tests.gift_claims.cut_tab_icons --serial 127.0.0.1:21923
"""
import argparse
import sys
import threading

import adbutils
import cv2
import numpy as np

from bot.activities.gift_claims.screens import GiftScreen, identify
from bot.activities.gift_claims.valuable_event import zone
from bot.activities.gift_claims.valuable_event.run import SPECS, _tab
from bot.context import BotContext
from bot.context.templates import TEMPLATE_DIR

ICON_Y = (60, 90)          # px trên màn 396x704: phần hình icon, phía trên dòng tên tab và dải thông báo chạy chữ (y 92-116)
ICON_SPAN_Y = (78, 90)     # hàng dùng đo bề ngang khung icon (dưới chấm đỏ thông báo, trên dải thông báo chạy chữ)
ICON_HALF = 16             # nửa bề rộng ảnh cắt quanh tâm icon
BRIGHT_V = 80              # điểm sáng hơn nền tab (~33)
MAX_SWIPES = 30


def icon_center(screen, x_guess: int) -> int:
    """Tâm icon gần `x_guess`: giữa dải cột sáng liền nhau (khung + hình icon) ở các hàng ICON_SPAN_Y."""
    rows = cv2.cvtColor(screen[ICON_SPAN_Y[0]:ICON_SPAN_Y[1]], cv2.COLOR_BGR2HSV)[..., 2]
    bright = (rows > BRIGHT_V).mean(axis=0) > 0.3
    x = min(max(int(x_guess), 0), len(bright) - 1)
    if not bright[x]:
        near = np.flatnonzero(bright)
        if near.size == 0:
            return int(x_guess)
        x = int(near[np.argmin(np.abs(near - x))])
    left = right = x
    while left > 0 and bright[left - 1]:
        left -= 1
    while right < len(bright) - 1 and bright[right + 1]:
        right += 1
    return (left + right) // 2


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--serial", required=True)
    args = parser.parse_args()
    bot = BotContext(adbutils.adb.device(serial=args.serial), threading.Event(), None, print)
    bot.record = print
    if bot.screenshot().shape[:2] != (704, 396):
        sys.exit("cần màn 396x704 (toạ độ cắt đo trên cỡ này)")
    if identify(bot, bot.screenshot()) != GiftScreen.VALUABLE_EVENT and not zone.open_valuable_event(bot):
        sys.exit("không mở được Valuable Event")
    title = zone.capture_title(bot)
    zone.swipe_to_left_edge(bot, title)

    cut: dict[str, tuple[int, float]] = {}
    for _ in range(MAX_SWIPES):
        screen = bot.screenshot()
        for spec in SPECS:
            folder = spec.tab.rsplit("/", 1)[0]
            if folder in cut or (pos := _tab(bot, spec, screen)) is None:
                continue
            center = icon_center(screen, pos[0])
            if not ICON_HALF <= center <= screen.shape[1] - ICON_HALF:
                continue          # icon sát mép màn, chờ cú kéo sau
            icon = screen[ICON_Y[0]:ICON_Y[1], center - ICON_HALF:center + ICON_HALF]
            path = TEMPLATE_DIR / "GiftClaims" / folder / "tab_icon.png"
            cv2.imwrite(str(path), icon)
            cut[folder] = (center, pos[0])
            print(f"cắt {folder}: tâm icon x={center} (ảnh chữ cũ ở x={pos[0]}) -> {path}")
        before = screen
        bot.swipe_percent(*zone.SHORT_SWIPE, duration=zone.SLOW_SWIPE_DURATION)
        bot.sleep(1)
        if float(cv2.absdiff(before[50:130], bot.screenshot()[50:130]).mean()) < 1:
            break

    missing = sorted({spec.tab.rsplit("/", 1)[0] for spec in SPECS} - set(cut))
    print(f"đã cắt {len(cut)} icon; chưa thấy trên máy: {', '.join(missing) or 'không'}")


if __name__ == "__main__":
    main()
