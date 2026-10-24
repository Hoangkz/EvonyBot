"""Claim Login Gifts and verify Congratulations or chest disappearance."""
from ...common import GiftTask, find, return_home, select_carousel_tab
from ...lobby import open_named
from ...screens import GiftScreen

KEY = "gift_login_gifts"
PAGE = "LoginGifts/title"
CONGRATULATIONS = "LoginGifts/congratulations"
REWARD_BUTTON = "Common/button_reward_chest"
REWARD_THRESHOLD = 0.80
FALLBACK_REWARD_POS = (45, 190)


def _tap_reward(bot, pos) -> bool:
    """Tap reward; Congratulations or a vanished chest means DONE."""
    bot.tap(*pos, delay=1)
    for attempt in range(3):
        screen = bot.screenshot()
        if find(bot, CONGRATULATIONS, screen, threshold=0.78,
                region=(0, 38, 100, 62)) is not None:
            bot.record("Gift Claims: Login Gifts nhận được quà (Congratulations); DONE")
            bot.back(delay=1)
            return True
        page_open = find(bot, PAGE, screen, threshold=0.70,
                         region=(0, 15, 45, 25)) is not None
        chest = find(bot, REWARD_BUTTON, screen, threshold=REWARD_THRESHOLD,
                     region=(0, 18, 100, 98))
        if page_open and chest is None:
            bot.record("Gift Claims: Login Gifts chụp lại không còn hộp quà; DONE")
            return True
        if attempt < 2:
            bot.record(f"Gift Claims: Login Gifts chờ Congratulations "
                       f"({attempt + 1}/3)")
            bot.sleep(1)
    bot.record("Gift Claims: Login Gifts không thấy Congratulations; giữ PENDING")
    return False


def claim_opened(bot) -> bool:
    """Use the captured chest, falling back to the user-approved coordinate."""
    screen = bot.screenshot()
    if find(bot, PAGE, screen, threshold=0.70,
            region=(0, 15, 45, 25)) is None:
        bot.record("Gift Claims: Login Gifts chưa xác nhận được trang; giữ PENDING")
        return False
    target = find(bot, REWARD_BUTTON, screen, threshold=REWARD_THRESHOLD,
                  region=(0, 18, 100, 98))
    if target is None:
        target = FALLBACK_REWARD_POS
        bot.record("Gift Claims: Login Gifts không thấy ảnh nút quà; "
                   "tap dự phòng (45, 190)")
    else:
        bot.record(f"Gift Claims: Login Gifts thấy nút quà tại {target}")
    return _tap_reward(bot, target)


def run(bot):
    if (not open_named(bot, GiftScreen.SUPER_VALUE_RETURN)
            or not select_carousel_tab(bot, "SuperValueReturn/title",
                                       "LoginGifts/tab")):
        return False
    done = claim_opened(bot)
    return_home(bot)
    return done


TASK = GiftTask(KEY, "Login Gifts", run)
