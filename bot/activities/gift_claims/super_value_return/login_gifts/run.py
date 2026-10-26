"""Claim Login Gifts and verify Congratulations or chest disappearance."""
from ...common import (REWARD_CHEST_TEMPLATE, REWARD_CHEST_THRESHOLD,
                       GiftTask, find, find_reward_chest, return_home,
                       select_carousel_tab)
from ...lobby import open_named
from ...screens import GiftScreen

KEY = "gift_login_gifts"
PAGE = "SuperValueReturn/LoginGifts/title"
CONGRATULATIONS = "SuperValueReturn/LoginGifts/congratulations"
REWARD_BUTTON = REWARD_CHEST_TEMPLATE
# Two independent 50-frame captures on emulator 21503 scored 0.8033..0.9455
# inside the user-marked fixed box; unrelated matches outside it stayed <=
# 0.3881. Keep enough animation margin without admitting the measured noise.
REWARD_THRESHOLD = REWARD_CHEST_THRESHOLD
REWARD_REGION = (2, 22, 18, 34)
POST_TAP_WAIT = 1.5
CONGRATULATIONS_ATTEMPTS = 6
ABSENCE_CONFIRMATIONS = 2


def _confirm_chest_absent(bot) -> bool:
    """Require two fresh Login Gifts frames without the reward chest."""
    absent = 0
    for attempt in range(ABSENCE_CONFIRMATIONS + 2):
        screen = bot.screenshot()
        page_open = find(bot, PAGE, screen, threshold=0.70,
                         region=(0, 15, 45, 25)) is not None
        chest = find_reward_chest(bot, screen, region=REWARD_REGION,
                                  threshold=REWARD_THRESHOLD)
        absent = absent + 1 if page_open and chest is None else 0
        if absent >= ABSENCE_CONFIRMATIONS:
            return True
        if attempt + 1 < ABSENCE_CONFIRMATIONS + 2:
            bot.sleep(1)
    return False


def _tap_reward(bot, pos) -> bool:
    """Wait for the result, then require the chest to remain absent."""
    bot.tap(*pos, delay=1)
    bot.record("Gift Claims: Login Gifts chờ popup phần thưởng tải")
    bot.sleep(POST_TAP_WAIT)
    saw_congratulations = False
    for attempt in range(CONGRATULATIONS_ATTEMPTS):
        screen = bot.screenshot()
        if find(bot, CONGRATULATIONS, screen, threshold=0.78,
                region=(0, 38, 100, 62)) is not None:
            saw_congratulations = True
            bot.record("Gift Claims: Login Gifts thấy Congratulations; đóng popup "
                       "rồi kiểm tra lại rương")
            bot.back(delay=1)
            break
        if attempt + 1 < CONGRATULATIONS_ATTEMPTS:
            bot.record(f"Gift Claims: Login Gifts chờ Congratulations "
                       f"({attempt + 1}/{CONGRATULATIONS_ATTEMPTS})")
            bot.sleep(1)

    if _confirm_chest_absent(bot):
        bot.record("Gift Claims: Login Gifts quét lại hai frame không còn "
                   "rương; DONE")
        return True
    detail = "đã thấy Congratulations nhưng " if saw_congratulations else ""
    bot.record(f"Gift Claims: Login Gifts {detail}chưa xác nhận rương biến mất; "
               "giữ PENDING")
    return False


def claim_opened(bot) -> bool:
    """Use only the image-identified chest; never tap a fixed fallback."""
    screen = bot.screenshot()
    if find(bot, PAGE, screen, threshold=0.70,
            region=(0, 15, 45, 25)) is None:
        bot.record("Gift Claims: Login Gifts chưa xác nhận được trang; giữ PENDING")
        return False
    target = find_reward_chest(bot, screen, region=REWARD_REGION,
                               threshold=REWARD_THRESHOLD)
    if target is None:
        bot.record("Gift Claims: Login Gifts không thấy ảnh nút quà; "
                   "chụp lại để xác nhận trạng thái đã nhận")
        if _confirm_chest_absent(bot):
            bot.record("Gift Claims: Login Gifts hai frame liên tiếp không còn "
                       "rương; DONE")
            return True
        bot.record("Gift Claims: Login Gifts chưa xác nhận được rương đã biến "
                   "mất; giữ PENDING")
        return False
    bot.record(f"Gift Claims: Login Gifts thấy nút quà tại {target}")
    return _tap_reward(bot, target)


def run(bot):
    if (not open_named(bot, GiftScreen.SUPER_VALUE_RETURN)
            or not select_carousel_tab(bot, "SuperValueReturn/title",
                                       "SuperValueReturn/LoginGifts/tab")):
        return False
    done = claim_opened(bot)
    return_home(bot)
    return done


TASK = GiftTask(KEY, "Login Gifts", run)
