"""
alliance_capacity.py — "Alliance Capacity" activity (port of C# ScienceNew).

Opens the alliance science screen and donates, paying gems up to the
tab's "Times" limit. Each loop takes one screenshot, finds the first
known image on it (checked in list order) and acts on it.
"""
from ._common import click_images, delay, exit_images, go_home

SCIENCE = "Science"
BOSS = "JoinBoss"

# What to do when each image is seen.
DONE = "done"               # buy-gems dialog: out of free donations -> finished
GEMS = "gems"               # donate with gems
DONATE = "donate"           # donate screen open -> long-press Donate
OUT_ALLIANCE = "out_alliance"
SCROLL = "scroll"           # war screen -> scroll up
TAP = "tap"
BACK = "back"

def run(bot, settings: dict):
    """`bot` is the device's BotContext; `settings` is the "Alliance Capacity" tab's config."""
    gems_limit = _gems_limit(settings.get("times", "No"))
    targets = _targets()
    gems_used = 0

    while True:
        screen = bot.screenshot()
        action, pos = _find_first(bot, screen, targets)

        if action == DONE:
            return
        if action == GEMS:
            if gems_limit != -1 and gems_used >= gems_limit:
                return
            bot.tap(*pos)
            gems_used += 1
            delay(bot, 3)
        elif action == DONATE:
            _donate(bot, screen)
        elif action == SCROLL:
            _scroll(bot)
        elif action == TAP:
            bot.tap(*pos)
            delay(bot, 2)
        elif action == BACK:
            bot.back()
            delay(bot, 3)
        elif action == OUT_ALLIANCE:
            _out_alliance(bot, pos)
        else:
            go_home(bot, screen)


def _gems_limit(times: str) -> int:
    """"Times" combo -> how many gem donations are allowed (-1 = no limit)."""
    if times == "ALL":
        return -1
    try:
        return int(times)
    except (TypeError, ValueError):     # "No"
        return 0


def _targets() -> list[tuple[str, str]]:
    return [
        (f"{SCIENCE}/buyKc.png", DONE),
        (f"{SCIENCE}/sciencekc.png", GEMS),
        (f"{SCIENCE}/1sciencekc.png", TAP),
        (f"{SCIENCE}/CheckDonate.png", DONATE),
        (f"{BOSS}/outLM.png", OUT_ALLIANCE),
        (f"{SCIENCE}/scienceclick.png", TAP),
        (f"{BOSS}/chientranh.png", SCROLL),
        *[(path, BACK) for path in exit_images()],
        *[(path, TAP) for path in click_images()],
        (f"{BOSS}/lienminh.png", TAP),
    ]


def _find_first(bot, screen, targets):
    """First (action, pos) in `targets` whose image is on screen, else (None, None)."""
    for path, action in targets:
        # outLM's tap is an offset from the image's top-left corner.
        pos = bot.find(path, screen=screen, center=action != OUT_ALLIANCE)
        if pos is not None:
            return action, pos
    return None, None


def _donate(bot, screen):
    buttons = sorted(bot.find_all(f"{SCIENCE}/donate.png", screen=screen), key=lambda p: p[1])
    if buttons:
        x, y = buttons[0]
        bot.swipe(x, y, x, y, duration=5.0)    # hold the top Donate button for 5 s
    delay(bot)


def _scroll(bot):
    for _ in range(2):
        bot.swipe_percent(50, 87, 50, 54, duration=1.0)
        delay(bot)


def _out_alliance(bot, pos):
    x, y = pos
    bot.tap(x + 40, y + 40)
    delay(bot, 2)
    bot.back()
    delay(bot, 3)


