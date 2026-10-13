"""
run_route.py — chạy THẬT một route vuốt trong thành trên giả lập rồi in vị trí các công trình nhận ra được (không phải unit test:
tên file không bắt đầu bằng "test"). Dùng để đo / chỉnh ROUTES trong bot/city/civ<N>/city_tour.py.

    .\\venv\\Scripts\\python.exe -m tests.city.run_route

Sửa các biến ngay dưới (ROUTE, SERIAL, ...) rồi chạy. Đứng sẵn ở công trình xuất phát (VD Thành chính ở giữa màn). Mỗi cú đi qua
city_map.swipe (vuốt chậm đối xứng quanh SWIPE_CENTER, vuốt lại khi điểm đầu trúng icon), rồi chờ thêm SETTLE giây cho camera dừng
hẳn trước khi chụp (chụp sớm thì ảnh lệch). Chỉ in ra màn hình, không lưu file.
"""
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))     # chạy thẳng `py run_route.py` từ thư mục nào cũng được

import adbutils

from bot.city import city_map
from bot.context import BotContext


# Quy tắc theo vị trí của công trình

# Công trình đang nằm	Chỉnh
# lệch phải giữa màn	giảm dx
# lệch trái giữa màn	tăng dx
# lệch dưới giữa màn	giảm dy
# lệch trên giữa màn	tăng dy


# ---- sửa ở đây -----------------------------------------------------------------------------------------------------
ROUTE = [(-177, 23)] * 5      # Tháp canh -> Research Factory: civ1 (-177, 41) làm RF ở dưới giữa màn ~92 px -> giảm dy 18 mỗi cú
DIRECTION = -1             # -1: vuốt đúng ROUTE như đã ghi; đổi thành 1: vuốt chiều ngược lại (đảo dấu mọi cú của ROUTE)
SERIAL = "127.0.0.1:21933"
CIV = 7                         # nền văn minh của máy (chọn ảnh mẫu công trình)
SETTLE = 1.0                    # giây chờ thêm sau mỗi cú cho camera dừng hẳn
EACH = False                    # True: in vị trí công trình sau từng cú
WATCH = ()                      # chỉ in các công trình này, VD ("walls", "keep"); () = mọi công trình nhận ra được
# --------------------------------------------------------------------------------------------------------------------


def report(bot, names, label):
    """Chụp màn hình, nhận ra các công trình trong `names` (hoặc mọi công trình nếu names=()) rồi in ra vị trí lệch giữa."""
    # screen = city_map.city_screen(bot)
    # found = city_map.visible(bot, screen, names)
    # print(f"{label}:", flush=True)
    # if not found:
    #     print("   không thấy công trình nào trong danh sách", flush=True)
    # for name, pos in found.items():
    #     score, _ = city_map.locate(bot, screen, name)
    #     print(f"   {name:18s} ({pos[0]:3d}, {pos[1]:3d})  lệch giữa ({pos[0] - city_map.CENTER[0]:+d}, {pos[1] - city_map.CENTER[1]:+d})  khớp {score:.3f}",
    #           flush=True)


def main():
    total = (sum(-DIRECTION * m[0] for m in ROUTE), sum(-DIRECTION * m[1] for m in ROUTE))
    names = tuple(WATCH) if WATCH else city_map.BUILDINGS
    print(f"route {len(ROUTE)} cú, tổng ngón tay {total}, civ {CIV}, {SERIAL}", flush=True)

    start = time.monotonic()
    bot = BotContext(adbutils.adb.device(serial=SERIAL), threading.Event(), None,
                     lambda message: print(f"   [{time.monotonic() - start:6.1f}s] {message}", flush=True))
    bot.civilization = CIV

    report(bot, names, "TRƯỚC khi vuốt")
    for i, (dx, dy) in enumerate(ROUTE, 1):
        finger = (-DIRECTION * dx, -DIRECTION * dy)
        city_map.swipe(bot, finger)
        time.sleep(SETTLE)
        print(f"cú {i}/{len(ROUTE)}: ngón tay {finger}", flush=True)
        if EACH and i < len(ROUTE):
            report(bot, names, f"   sau cú {i}")
    report(bot, names, f"SAU {len(ROUTE)} cú (tổng {total})")


if __name__ == "__main__":
    main()
