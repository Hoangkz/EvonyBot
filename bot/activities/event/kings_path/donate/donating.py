"""
donating.py — vòng donate ở màn Alliance Science, dùng chung cho hai đường vào (qua nút Go của
King's Path — run.py, hoặc qua Liên minh khi không làm Patrol — alliance.py).

Mỗi bước chụp 1 ảnh: hộp "Spend N Gems on clearing the Cooldown?" -> Okay; nút "Donate" của thẻ
khoa học trên cùng -> bấm (+1), bấm tiếp tới khi hết lượt miễn phí (nút kim cương), kể cả khi đã đủ số cần; chưa đủ
mà hết lượt -> mua lại lượt, tối đa MAX_GEM_BUYS lần.
"""
from .constants import (
    DONATE_BUTTONS,
    DONATE_WAIT,
    GEMS_BUTTON,
    GEMS_WAIT,
    MAX_DONATES,
    MAX_GEM_BUYS,
    MAX_MISSES,
    OKAY,
    SCIENCE_TITLE,
)


def donate_times(bot, name: str, need: int, on_donate=None) -> int:
    """Donate ở màn Alliance Science tới khi HẾT LƯỢT MIỄN PHÍ (nút Donate chuyển thành nút kim cương), kể cả
    khi đã đủ `need` lần (người dùng chốt: không dừng trước khi ra nút kim cương). Mới đủ `need` thì không mua
    thêm lượt bằng kim cương; chưa đủ mà hết lượt miễn phí thì mua lại (tối đa MAX_GEM_BUYS lần). `on_donate(i)`
    gọi sau lần donate thứ i (VD lưu tiến độ). Trả số lần đã donate (< need nếu hết lượt mua / không nhận ra màn)."""
    donated = gem_buys = misses = 0
    while donated < MAX_DONATES:
        action, pos = read_screen(bot, bot.screenshot())
        if action is None:
            misses += 1
            if misses > MAX_MISSES:
                bot.record(f"{name}: screen not recognised, stop ({donated}/{need})")
                return donated
            bot.sleep(1)
            continue
        misses = 0
        if action == "okay":
            if donated >= need:
                bot.back(delay=1)   # hộp tiêu kim cương khi đã đủ: không mua
                break
            bot.tap(*pos, delay=GEMS_WAIT)
        elif action == "donate":
            bot.tap(*pos, delay=DONATE_WAIT)
            donated += 1
            if on_donate is not None:
                on_donate(donated)
        else:
            if donated >= need:
                bot.log(f"{name}: free donations used up ({donated}), gems button shown")
                break
            if gem_buys >= MAX_GEM_BUYS:
                bot.record(f"{name}: bought donations {MAX_GEM_BUYS} times, stop ({donated}/{need})")
                return donated
            gem_buys += 1
            bot.record(f"{name}: out of donations, buy with gems ({gem_buys}/{MAX_GEM_BUYS})")
            bot.tap(*pos, delay=GEMS_WAIT)
    return donated


def read_screen(bot, screen):
    """(action, vị trí) trên màn Alliance Science: "okay" (hộp xác nhận), "donate" /
    "gems" (nút của thẻ khoa học trên cùng); (None, None) nếu không phải màn đó."""
    if bot.find(SCIENCE_TITLE, screen=screen) is None:
        return None, None
    okay = bot.find(OKAY, screen=screen)
    if okay is not None:
        return "okay", okay
    for action, templates in (("donate", DONATE_BUTTONS), ("gems", (GEMS_BUTTON,))):
        points = [p for template in templates for p in bot.find_all(template, screen=screen)]
        if points:
            return action, min(points, key=lambda p: p[1])
    return None, None
