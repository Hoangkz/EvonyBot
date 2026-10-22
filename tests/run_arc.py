"""
run_arc.py — chạy tay: quét hình quạt trên bản đồ thế giới của một giả lập, mọi thông số ghi thẳng ở dưới, không cần env.

    py run_arc.py        (chạy được từ bất cứ thư mục nào; máy phải đang ở bản đồ thế giới)

Ctrl+C để dừng. Test tự động / thử nhiều cấu hình: tests/real_run.py (đọc EVONY_* từ env).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bot.common.arc_sweep import arc_sweep
from tests import real_run

SERIAL = "127.0.0.1:21913"
START, END = 0, 90     # độ 0 .. 360, quạt đi NGƯỢC chiều kim đồng hồ từ START tới END (qua 0° được, VD 345, 15); 0, 360 = cả vòng tròn. góc theo màn hình: 0° = ngang sang phải, 90° = thẳng lên
RADIUS = 40               # km (1 km = 1 đơn vị toạ độ); 300 sẽ chạy hàng giờ


def target(bot):
    return arc_sweep(bot, START, END, RADIUS, on_step=lambda u, v: bot.log(f"arc: tới ({u:.0f}, {v:.0f})") or False)


if __name__ == "__main__":
    real_run.SERIAL = SERIAL
    real_run.target = target
    real_run.main()
