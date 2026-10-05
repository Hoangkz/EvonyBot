"""
run.py — Daily Activities "Alliance Donation": handler các action riêng của nhiệm vụ (Liên minh -> Donate).
Vòng lặp chung (mở Activity, dòng Go, cuộn, ảnh xong): ../common.py run_task.

Luồng mới (donate_free, gọi từ ../run.py theo giờ — ô chọn 0 / 1h / 2h / 3h / 4h ở tab UI):
1. Kiểm tra trước: mở danh sách Activity, xem dòng "Donate to the Alliance" (không bấm Go). Hết Go (Claim /
   tích V / thẻ Completed) -> đánh dấu xong hôm nay, thôi (../run.py không gọi lại trong ngày nữa).
2. Chưa xong -> giống King's Path Donate khi không làm Patrol: màn chính -> Liên minh -> cuộn -> Alliance
   Science (event/kings_path/donate/alliance.py _open_science).
3. Bấm "Donate" thẻ khoa học trên cùng tới khi hết lượt miễn phí (nút thành kim cương / hộp xác nhận kim
   cương -> Back). Không mua lượt bằng kim cương. Không donate được lần nào -> dừng (lần sau thử lại).
4. Có donate -> Back, kiểm tra dòng Activity lần nữa: xong -> đánh dấu xong hôm nay.
Lần thử nào cũng lưu TRIED_KEY (giờ thử) để ../run.py tính lúc làm lại.
"""
from ...event.kings_path.donate.alliance import _open_science
from ...event.kings_path.donate.constants import DONATE_WAIT, MAX_MISSES
from ...event.kings_path.donate.donating import read_screen
from ..common import Task
from ..hourly import try_task
from .constants import (
    ACTIONS,
    DONE_IMAGES,
    FOLDER,
    FOLDER_PATH,
    KEY,
    LABEL,
    MAX_FREE_DONATIONS,
    TRIED_KEY,
)


def handle(bot, action, pos, screen):
    if action == "donate":
        _, y = pos
        row_y = max(0, y)
        region = bot.crop(screen, 0, row_y, screen.shape[1], 390)
        donate = bot.find(f"{FOLDER_PATH}/Donate.png", screen=region)
        if donate is None:
            return True
        bot.tap(donate[0], donate[1] + row_y, delay=1)
    return False


def donate_free(bot) -> bool:
    """Một lần thử (../hourly.py try_task): kiểm tra dòng Activity; chưa xong thì donate hết lượt miễn phí rồi
    kiểm tra lại. True nếu nhiệm vụ đã xong hôm nay."""
    return try_task(bot, TASK, TRIED_KEY, _donate)


def _donate(bot) -> bool:
    """Liên minh -> Alliance Science -> donate hết lượt miễn phí -> Back. True nếu donate được ít nhất 1 lần."""
    if not _open_science(bot):
        return False
    donated = _donate_free_times(bot)
    bot.back(delay=1)   # đóng Alliance Science
    if not donated:
        bot.log(f"{LABEL}: no free donations now, try later")
        return False
    bot.record(f"{LABEL}: donated {donated} free time(s), checking Activity")
    return True


def _donate_free_times(bot) -> int:
    """Màn Alliance Science: bấm Donate thẻ trên cùng tới khi hết lượt miễn phí. Trả số lần đã donate."""
    donated = misses = 0
    while donated < MAX_FREE_DONATIONS:
        action, pos = read_screen(bot, bot.screenshot())
        if action is None:
            misses += 1
            if misses > MAX_MISSES:
                bot.record(f"{LABEL}: Alliance Science not recognised, stop ({donated} donated)")
                break
            bot.sleep(1)
            continue
        misses = 0
        if action == "donate":
            bot.tap(*pos, delay=DONATE_WAIT)
            donated += 1
            continue
        if action == "okay":
            bot.back(delay=1)   # hộp tiêu kim cương: không mua
        break                   # "gems": hết lượt miễn phí
    return donated


TASK = Task(LABEL, FOLDER, DONE_IMAGES, ACTIONS, handle, key=KEY)
