"""
run.py — Daily Activities "Monster Killing": handler các action riêng của nhiệm vụ (đánh quái: 2 lần (nhận dòng đầu, hoãn) rồi 3 lần nữa sau 4-5 nhiệm vụ khác (run.py)).
Vòng lặp chung (mở Activity, dòng Go, cuộn, ảnh xong): ../common.py run_task.
"""
from ....common import delay
from ..common import Task, open_daily_activity, replace_text
from .constants import ACTIONS, AFTER_OPEN_TAP, DONE_IMAGES, FOLDER, FOLDER_PATH, KEY, LABEL


def handle(bot, action, pos, screen):
    if action == "tap_monster":
        # Evony 5.25 opens Search on the Summon tab. The old C# code only
        # pressed the bottom button, which is inert until Monster is selected.
        bot.tap(*pos, delay=2)
        bot.tap(200, 670, delay=4)
        refreshed = bot.screenshot()
        # Current builds open a monster-details card with a wide green Attack
        # button. AttackMonster.png is the small sword used by older builds.
        # Handle the current card here so the outer scanner does not mistake
        # the still-visible Search drawer for a failed search and click it again.
        current_attack = bot.find(
            f"{FOLDER_PATH}/AttackButtonCurrent.png",
            threshold=0.72, screen=refreshed, region=(20, 55, 80, 82))
        if current_attack is not None:
            bot._daily_monster_search_misses = 0
            bot.tap(*current_attack, delay=3)
            return False

        attack = bot.find(f"{FOLDER_PATH}/AttackMonster.png", screen=refreshed)
        if attack is not None:
            bot._daily_monster_search_misses = 0
        else:
            misses = getattr(bot, "_daily_monster_search_misses", 0) + 1
            bot._daily_monster_search_misses = misses
            if misses >= 3:
                bot.log("Daily Activities: Monster search waiting for an available target")
                # Back opens Evony's Quit dialog on the current world-map UI;
                # leave the search drawer in place and retry after marches have
                # had time to return.
                delay(bot, 5)
                bot._daily_monster_search_misses = 0
    elif action == "monster":
        bot.tap(*pos, delay=2)
        bot.tap(200, 500, delay=2)
    elif action == "march":
        if not dispatch_march(bot, screen):
            # Stop this pass on the March screen. Continuing would make the
            # generic recovery press Back/Settings although no attack happened.
            return True
        marches = getattr(bot, "_daily_monster_marches", 0) + 1
        bot._daily_monster_marches = marches
        bot.log(f"Daily Activities: Monster march {marches}/5 confirmed")
        if marches in (2, 5):
            # Two sequential daily rows: 2 attacks, claim/check, then 3 more.
            if not open_daily_activity(bot, close_search=True):
                return True
    return False


def dispatch_march(bot, screen) -> bool:
    """Send one march and return True only after the March page disappears."""
    full_tiers = bot.find(f"{FOLDER_PATH}/FullTiersCurrent.png", threshold=0.72,
                          screen=screen, region=(5, 85, 60, 100))
    if full_tiers is not None:
        # Current Evony layout: the green Full Tiers preset fills/sends the
        # march. On some accounts it only fills it, so confirm with March below.
        bot.tap(*full_tiers, delay=3)
    else:
        # Legacy layout retained as a fallback for older emulator/game builds.
        bot.tap(320, 520, delay=3)
        replace_text(bot, "100", 8)
        delay(bot, 2)
        bot.tap(300, 660, delay=3)

    after = bot.screenshot()
    if bot.find(f"{FOLDER_PATH}/March.png", screen=after) is not None:
        # Full Tiers only filled the formation; press the verified bottom-right
        # March control once, then require an actual screen transition.
        march_button = bot.find(f"{FOLDER_PATH}/MarchButtonCurrent.png", threshold=0.72,
                                screen=after, region=(50, 85, 100, 100))
        if march_button is not None:
            bot.tap(*march_button, delay=3)
            after = bot.screenshot()

    sent = bot.find(f"{FOLDER_PATH}/March.png", screen=after) is None
    if not sent:
        bot.log("Daily Activities: Monster march was not sent; staying on March screen")
    return sent


TASK = Task(LABEL, FOLDER, DONE_IMAGES, ACTIONS, handle, AFTER_OPEN_TAP, key=KEY)
