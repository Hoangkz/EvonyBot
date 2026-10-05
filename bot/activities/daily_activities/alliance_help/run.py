"""
run.py — Daily Activities "Alliance Help": một lần thử theo giờ (gọi từ ../run.py _run_hourly):
1. Màn chính -> Liên minh -> dòng "Alliance Help" -> màn Alliance Help.
2. "No records" (không ai cần giúp) -> Back, sang nhiệm vụ khác: KHÔNG kiểm tra Activity, KHÔNG lưu gì vào DB.
3. Có "Help All" -> bấm -> Back -> lưu giờ thử (TRIED_KEY) -> kiểm tra dòng / thẻ Activity như Alliance Donation
   (../hourly.py check_done, không bấm Go): xong -> đánh dấu xong hôm nay (lưu DB), trong ngày không kiểm tra lại.
Đường tới Liên minh giống King's Path Donate (event/kings_path/donate/alliance.py _open_science), đích là dòng
"Alliance Help" (thấy ngay, không cần cuộn).
"""
from ....common import click_images, delay, exit_images, find_first, go_home
from ...event.kings_path.donate.constants import ALLIANCE_BUTTON, OUT_ALLIANCE
from ..common import Task
from ..hourly import check_done
from .constants import (
    ACTIONS,
    DONE_IMAGES,
    FOLDER,
    HELP_ALL,
    HELP_ROW,
    HELP_TITLE,
    HELP_WAIT,
    KEY,
    LABEL,
    LIST_WAIT,
    NAV_MAX_STEPS,
    NO_RECORDS,
    TRIED_KEY,
)

_ON_HELP, _TAP, _BACK, _OUT = "on_help", "tap", "back", "out_alliance"


def handle(bot, action, pos, screen):
    """Không có luồng C# cũ (ACTIONS rỗng)."""
    return False


def help_all(bot) -> bool:
    """Một lần thử: Help All; có giúp thì kiểm tra dòng Activity. True nếu nhiệm vụ đã xong hôm nay. Không ai cần
    giúp ("No records") -> False, không lưu gì."""
    if not _help(bot):
        return False
    bot.mark_daily_done(TRIED_KEY)
    if check_done(bot, TASK):
        return True
    bot.log(f"{LABEL}: Activity row not done yet, try later")
    return False


def _help(bot) -> bool:
    """Liên minh -> Alliance Help -> "Help All" -> Back. True nếu đã bấm Help All; "No records" / không thấy nút ->
    Back, False."""
    if not _open_help(bot):
        return False
    for _ in range(LIST_WAIT):
        screen = bot.screenshot()
        button = bot.find(HELP_ALL, screen=screen)
        if button is not None:
            bot.tap(*button, delay=1)
            # Giúp xong danh sách trống -> "No records": lúc này vẫn đi nhận quà (khác "No records" trước khi bấm).
            bot.wait_for(NO_RECORDS, timeout=HELP_WAIT)
            bot.record(f"{LABEL}: Help All, checking Activity")
            bot.back(delay=1)   # đóng màn Alliance Help
            return True
        # "No records" TRƯỚC khi bấm Help All = không ai cần giúp.
        if bot.find(NO_RECORDS, screen=screen) is not None:
            bot.log(f"{LABEL}: no help requests (No records), next task")
            break
        bot.sleep(1)
    else:
        bot.log(f"{LABEL}: Help All not found, next task")
    bot.back(delay=1)
    return False


def _open_help(bot) -> bool:
    """Đi tới màn Alliance Help: màn chính -> nút Liên minh -> dòng "Alliance Help". True nếu tới nơi."""
    targets = [
        (HELP_TITLE, _ON_HELP),
        (OUT_ALLIANCE, _OUT),
        (HELP_ROW, _TAP),
        *[(path, _BACK) for path in exit_images()],
        *[(path, _TAP) for path in click_images()],
        (ALLIANCE_BUTTON, _TAP),
    ]
    for _ in range(NAV_MAX_STEPS):
        screen = bot.screenshot()
        action, pos = find_first(bot, screen, targets, top_left={_OUT})
        if action == _ON_HELP:
            return True
        if action == _TAP:
            bot.tap(*pos)
            delay(bot, 2)
        elif action == _OUT:
            bot.tap(pos[0] + 40, pos[1] + 40)
            delay(bot, 2)
            bot.back()
            delay(bot, 3)
        elif action == _BACK:
            bot.back()
            delay(bot, 2)
        else:
            go_home(bot, screen)
            delay(bot, 2)
    bot.record(f"{LABEL}: Alliance Help screen not reached")
    return False


TASK = Task(LABEL, FOLDER, DONE_IMAGES, ACTIONS, handle, key=KEY)
