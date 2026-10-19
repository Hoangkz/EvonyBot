"""
run.py — Daily Activities "Ranger Knight Order": phần sau Go (màn Ranger Knight Order -> Claim -> Quick Dispatch -> Send).
Mở Quests -> Activity, tìm dòng, bấm Go: ../common.py open_task_or_finish. Ảnh / hằng số: constants.py.

Sau Go chờ màn Ranger Knight Order. Còn nút Claim thì bấm (chờ 5 giây). Hết Claim -> Quick Dispatch -> chờ bảng
Quick Dispatch -> Send (xám thì không bấm) -> báo xong hôm nay -> Back 3 lần liên tục.
"""
from ..common import Task, mark_task_done
from .constants import (
    BACKS_AFTER,
    CLAIM,
    CLAIM_MAX,
    CLAIM_WAIT,
    DISPATCH_TITLE,
    DISPATCH_WAIT,
    FOLDER,
    KEY,
    LABEL,
    QUICK_DISPATCH,
    SCREEN_WAIT,
    SEND,
    SEND_GRAY,
    SEND_THRESHOLD,
    SEND_WAIT,
    THRESHOLD,
    TITLE,
)


def after_go(bot) -> bool:
    """Sau khi open_task bấm Go. True (và báo xong hôm nay) khi đã bấm Send; False nếu không vào được màn Ranger
    Knight Order hoặc không mở được bảng Quick Dispatch / không thấy Send."""
    if bot.wait_for(TITLE, timeout=SCREEN_WAIT, threshold=THRESHOLD, interval=1) is None:
        bot.record(f"{LABEL}: Ranger Knight Order screen not shown")
        _leave(bot)
        return False
    for _ in range(CLAIM_MAX):
        claim = bot.find(CLAIM, threshold=THRESHOLD)
        if claim is None:
            break
        bot.record(f"{LABEL}: claim")
        bot.tap(*claim, delay=CLAIM_WAIT)
    quick = bot.find(QUICK_DISPATCH, threshold=THRESHOLD)
    if quick is None:
        bot.record(f"{LABEL}: Quick Dispatch button not found")
        _leave(bot)
        return False
    bot.tap(*quick, delay=0)
    if bot.wait_for(DISPATCH_TITLE, timeout=DISPATCH_WAIT, threshold=THRESHOLD, interval=1) is None:
        bot.record(f"{LABEL}: Quick Dispatch panel not shown")
        _leave(bot)
        return False
    screen = bot.screenshot()
    send = bot.find(SEND, screen=screen, threshold=SEND_THRESHOLD)
    if send is not None:
        bot.tap(*send, delay=SEND_WAIT)
        bot.record(f"{LABEL}: sent")
    elif bot.find(SEND_GRAY, screen=screen, threshold=SEND_THRESHOLD) is not None:
        bot.record(f"{LABEL}: Send is greyed out (no general available), done today")
    else:
        bot.record(f"{LABEL}: Send button not found")
        _leave(bot)
        return False
    mark_task_done(bot, TASK)
    _leave(bot)
    return True


def _leave(bot):
    """Back BACKS_AFTER lần liên tục (bảng Quick Dispatch -> màn Ranger Knight -> Activity -> thành)."""
    for _ in range(BACKS_AFTER):
        bot.back(delay=1)


TASK = Task(LABEL, FOLDER, key=KEY)
