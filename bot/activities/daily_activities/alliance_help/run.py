"""
run.py — Daily Activities "Alliance Help": một lần thử theo giờ (worker gọi, bot/worker/tasks.py):
1. Màn chính -> Liên minh -> dòng "Alliance Help" -> màn Alliance Help.
2. "No records" (không ai cần giúp) -> Back, sang nhiệm vụ khác: KHÔNG kiểm tra Activity, chưa xong.
3. Có "Help All" -> bấm -> Back -> kiểm tra dòng / thẻ Activity như Alliance Donation
   (../common.py check_done, không bấm Go): xong -> TaskResult(done=True), trong ngày không kiểm tra lại.
Đường tới Liên minh giống King's Path Donate (event/kings_path/donate/alliance.py _open_science), đích là dòng
"Alliance Help" (thấy ngay, không cần cuộn).
"""
from ....common import no_alliance
from ....common import click_images, delay, exit_images, find_first, go_home
from ...event.kings_path.donate.constants import ALLIANCE_BUTTON, OUT_ALLIANCE
from ...result import NOT_DONE, TaskResult
from ..common import Task, check_done
from .constants import (
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
)

_ON_HELP, _TAP, _BACK, _OUT, _OPEN = "on_help", "tap", "back", "out_alliance", "open_alliance"


def help_all(bot) -> TaskResult:
    """Một lần thử: Help All; có giúp thì kiểm tra dòng Activity. done=True nếu nhiệm vụ đã xong hôm nay. Không ai cần
    giúp ("No records") -> chưa xong."""
    if not _help(bot):
        return NOT_DONE
    if check_done(bot, TASK):
        return TaskResult(done=True, reached=0)
    bot.log(f"{LABEL}: Activity row not done yet, try later")
    return NOT_DONE


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
        (ALLIANCE_BUTTON, _OPEN),
    ]
    for _ in range(NAV_MAX_STEPS):
        screen = bot.screenshot()
        if no_alliance.check(bot, screen):
            return False
        action, pos = find_first(bot, screen, targets, top_left={_OUT})
        if action == _ON_HELP:
            return True
        if action == _TAP:
            bot.tap(*pos)
            delay(bot, 2)
        elif action == _OPEN:
            bot.tap(*pos)
            if no_alliance.wait_menu(bot):
                return False
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


TASK = Task(LABEL, FOLDER, key=KEY)
