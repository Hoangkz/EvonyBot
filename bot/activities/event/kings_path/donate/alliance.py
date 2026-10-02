"""
alliance.py — Donate khi người dùng không làm Patrol (ô Patrol = 0): không vào King's Path mà
đi màn chính -> Liên minh -> cuộn xuống -> Alliance Science -> donate thẻ khoa học đầu tiên cho
đủ mục tiêu (như activity Alliance Capacity, dùng lại ảnh của nó). Không đọc được tiến độ ở dòng
Go nên tự lưu số lần đã donate hôm nay vào daily_done (alliance_key).
"""
from .....common import click_images, delay, exit_images, find_first, go_home
from .constants import (
    ALLIANCE_BUTTON,
    ALLIANCE_SCIENCE,
    ALLIANCE_SCROLL,
    KEY,
    NAV_MAX_STEPS,
    OUT_ALLIANCE,
    SCIENCE_TITLE,
)
from .donating import donate_times

NAME = "Donate"
_ON_SCIENCE, _TAP, _BACK, _SCROLL, _OUT = "on_science", "tap", "back", "scroll", "out_alliance"


def alliance_key(n: int) -> str:
    """Key daily_done: đã donate lần thứ `n` hôm nay (đường Liên minh)."""
    return f"{KEY}_alliance_{n}"


def donated_today(bot, target: int) -> int:
    """Số lần đã donate hôm nay theo đường Liên minh (đếm alliance_key 1, 2, ... liên tiếp)."""
    n = 0
    while n < target and bot.is_daily_done(alliance_key(n + 1)):
        n += 1
    return n


def run(bot, task: dict):
    """`task` là settings của nhiệm vụ Donate: {"value": int, "day": int}."""
    if bot.is_daily_done(KEY):
        bot.log(f"{NAME}: already done")
        return
    target = int(task.get("value") or 0)
    done = donated_today(bot, target)
    if done >= target:
        bot.log(f"{NAME}: donated {done} / {target} today (alliance), done")
        bot.mark_daily_done(KEY)
        return
    bot.log(f"{NAME}: Patrol off -> donate via Alliance Science ({done} / {target})")
    if not _open_science(bot):
        return
    donated = donate_times(bot, NAME, target - done,
                           on_donate=lambda i: bot.mark_daily_done(alliance_key(done + i)))
    if done + donated >= target:
        bot.log(f"{NAME}: donated {done + donated} / {target}, done")
        bot.back(delay=1)
        bot.mark_daily_done(KEY)


def _open_science(bot) -> bool:
    """Đi tới màn Alliance Science (như Alliance Capacity). True nếu tới nơi."""
    targets = [
        (SCIENCE_TITLE, _ON_SCIENCE),
        (OUT_ALLIANCE, _OUT),
        (ALLIANCE_SCIENCE, _TAP),
        (ALLIANCE_SCROLL, _SCROLL),
        *[(path, _BACK) for path in exit_images()],
        *[(path, _TAP) for path in click_images()],
        (ALLIANCE_BUTTON, _TAP),
    ]
    for _ in range(NAV_MAX_STEPS):
        screen = bot.screenshot()
        action, pos = find_first(bot, screen, targets, top_left={_OUT})
        if action == _ON_SCIENCE:
            return True
        if action == _TAP:
            bot.tap(*pos)
            delay(bot, 2)
        elif action == _SCROLL:
            for _ in range(2):
                bot.swipe_percent(50, 87, 50, 54, duration=1.0)
                delay(bot)
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
    bot.log(f"{NAME}: Alliance Science not reached")
    return False
