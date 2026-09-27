"""Auxiliary JoinBossUpdate flows: shop, Crazy Eggs, Viking and speed march."""
import threading

from ...common import click_images, delay, exit_images, find_first, go_home


JB = "JoinBoss"
BUY = f"{JB}/Buy"
EGG = f"{JB}/CrazyEgg"
VIKING = "Viking"
SPEED = "SpeedMarchBoss"

_SPEED_LOCK = threading.Lock()


def buy_stamina(bot, quantity: int):
    """Port of Data.BuyStamina. Quantity is the UI's 10/16/20 value."""
    if quantity <= 0:
        return
    targets = [
        (f"{BUY}/buystamina.png", "buy"),
        (f"{BUY}/stamina.png", "stamina"),
        (f"{BUY}/checkWar.png", "war_list"),
        (f"{BUY}/war.png", "tap"),
        (f"{BUY}/item.png", "tap"),
        (f"{BUY}/special.png", "tap"),
        (f"{BUY}/chucnang.png", "features"),
        *[(path, "back") for path in exit_images()],
        *[(path, "tap") for path in click_images()],
    ]
    swipes = 0
    for _ in range(160):
        screen = bot.screenshot()
        action, pos = find_first(bot, screen, targets)
        if action == "features":
            bot.tap_percent(88.5, 5, delay=2)
        elif action == "war_list":
            bot.swipe_percent(50, 80, 50, 60, delay=2)
            swipes += 1
            if swipes > 4:
                bot.back(delay=2)
                swipes = 0
        elif action == "stamina":
            bot.tap(334, pos[1], delay=2)
        elif action == "buy":
            plus = bot.find(f"{BUY}/plus.png", screen=screen)
            if plus is None:
                bot.back(delay=2)
                continue
            for _ in range(max(0, quantity - 1)):
                bot.tap(*plus, delay=1)
            bot.tap(screen.shape[1] // 2, plus[1] + 110, delay=5)
            return
        elif action == "tap":
            bot.tap(*pos, delay=2)
        elif action == "back":
            bot.back(delay=2)
        else:
            go_home(bot, screen)
            delay(bot, 2)
    bot.log("Buy Stamina stopped: navigation limit reached")


def buy_hammer(bot):
    """Port of Data.BuyHammer."""
    targets = [
        (f"{BUY}/bua.png", "hammer"),
        (f"{BUY}/checkSpecial.png", "special_list"),
        (f"{BUY}/special.png", "tap"),
        (f"{BUY}/item.png", "tap"),
        (f"{BUY}/chucnang.png", "features"),
        *[(path, "back") for path in exit_images()],
        *[(path, "tap") for path in click_images()],
    ]
    special_clicks = 0
    for _ in range(120):
        screen = bot.screenshot()
        action, pos = find_first(bot, screen, targets)
        if action == "features":
            bot.tap_percent(88.5, 5, delay=2)
        elif action == "hammer":
            plus = bot.find(f"{BUY}/plus.png", screen=screen)
            if plus is None:
                bot.tap_percent(87.5, 35, delay=2)
                continue
            bot.tap(plus[0] - 20, plus[1] + 2, delay=1)
            bot.tap(screen.shape[1] // 2, plus[1] + 110, delay=5)
            return
        elif action == "special_list":
            bot.tap(*pos, delay=1)
            bot.tap_percent(87.5, 35, delay=2)
            special_clicks += 1
            if special_clicks > 5:
                return
        elif action == "tap":
            bot.tap(*pos, delay=2)
        elif action == "back":
            bot.back(delay=2)
        else:
            go_home(bot, screen)
            delay(bot, 2)
    bot.log("Buy Hammer stopped: navigation limit reached")


def crazy_eggs(bot) -> int | None:
    """Run one Crazy Eggs pass; return the next interval in hours, if inferred."""
    targets = [
        (f"{EGG}/1Success.png", "success"),
        (f"{EGG}/2Success.png", "success"),
        (f"{EGG}/TitleCrazyEgg.png", "eggs"),
        (f"{EGG}/EventCrazyEgg.png", "tap"),
        (f"{EGG}/EventCenter.png", "event_center"),
        (f"{EGG}/Event.png", "event"),
        *[(path, "back") for path in exit_images()],
        *[(path, "tap") for path in click_images()],
    ]
    egg_paths = tuple(f"{EGG}/{i}.png" for i in range(1, 5))
    egg_index = missing = center_swipes = 0
    interval = None
    for _ in range(180):
        screen = bot.screenshot()
        action, pos = find_first(bot, screen, targets)
        if action == "eggs":
            if egg_index >= len(egg_paths):
                return interval
            path = egg_paths[egg_index]
            if egg_index == 0:
                interval = 1
            elif egg_index == 1:
                interval = 4
            elif interval is None:
                interval = 2
            egg = bot.find(path, screen=screen)
            if egg is None:
                egg_index += 1
                missing += 1
                if missing > 3:
                    return None
                continue
            bot.tap(*egg, delay=5)
            confirm_screen = bot.screenshot()
            confirm = bot.find(f"{EGG}/Confirm.png", screen=confirm_screen)
            if confirm is not None:
                bot.tap(*confirm, delay=5)
                egg_index += 1
            elif bot.find(f"{EGG}/buyKc.png", screen=confirm_screen) is not None \
                    or bot.find(f"{EGG}/hetEgg.png", screen=confirm_screen) is not None:
                bot.back(delay=1)
                bot.back(delay=1)
                return None
            else:
                egg_index += 1
        elif action == "success":
            bot.tap_percent(50, 2, delay=10)
        elif action == "event_center":
            if center_swipes > 7:
                bot.back(delay=2)
                center_swipes = 0
            else:
                bot.swipe_percent(50, 80, 50, 60, duration=0.5, delay=3)
                center_swipes += 1
        elif action == "event":
            bot.tap(pos[0] + 15, pos[1] - 20, delay=5)
        elif action == "tap":
            bot.tap(*pos, delay=3)
        elif action == "back":
            bot.back(delay=3)
        else:
            go_home(bot, screen)
            delay(bot, 3)
    bot.log("Crazy Eggs stopped: navigation limit reached")
    return interval


def viking(bot):
    """Port of checkViking; summon/share/help until the event reports done."""
    targets = [
        (f"{VIKING}/doneshare.png", "done_share"),
        (f"{VIKING}/Share.png", "share"),
        (f"{VIKING}/askforhelp.png", "help"),
        (f"{VIKING}/attack.png", "tap"),
        (f"{VIKING}/guishare.png", "tap"),
        (f"{VIKING}/5summom.png", "open_world"),
        (f"{VIKING}/Summom.png", "open_world"),
        (f"{VIKING}/Go.png", "open_world"),
        (f"{VIKING}/DoneViking.png", "done"),
        (f"{VIKING}/Viking.png", "viking"),
        (f"{VIKING}/EventViking.png", "tap"),
        (f"{VIKING}/EventCenter.png", "event_center"),
        (f"{VIKING}/Event.png", "event"),
        *[(path, "back") for path in exit_images()],
        *[(path, "tap") for path in click_images()],
    ]
    swipes = 0
    for _ in range(220):
        screen = bot.screenshot()
        action, pos = find_first(bot, screen, targets)
        if action in ("done", "done_share"):
            if action == "done_share":
                bot.tap_percent(65, 58, delay=5)
            return
        if action == "open_world":
            bot.tap(*pos)
            for _ in range(5):
                world = bot.find(f"{VIKING}/world.png", threshold=0.88)
                if world is not None:
                    bot.tap_percent(49.8, 49.8)
                    break
                delay(bot)
            delay(bot, 3)
        elif action == "event":
            bot.tap(*pos, delay=10)
        elif action == "event_center":
            if swipes > 7:
                bot.back(delay=3)
                swipes = 0
            else:
                bot.swipe_percent(50, 80, 50, 60, duration=0.5, delay=3)
                swipes += 1
        elif action == "share":
            bot.tap_percent(69, 33, delay=3)
        elif action == "help":
            bot.tap(*pos, delay=3)
            confirm = bot.find(f"{VIKING}/confirm.png")
            if confirm is not None:
                bot.tap(*confirm, delay=5)
                bot.tap_percent(49.8, 49.8, delay=4)
        elif action == "viking":
            bot.tap(pos[0] + 30, pos[1] - 30, delay=3)
        elif action == "tap":
            bot.tap(*pos, delay=3)
        elif action == "back":
            bot.back(delay=3)
        else:
            go_home(bot, screen)
            delay(bot, 2)
    bot.log("Viking stopped: navigation limit reached")


def speed_marching(bot, target_seconds: int):
    """Serialize the active SpeedBoss flow across all device workers.

    ``SpeedBoss.cs`` currently overwrites its detected state with option 2,
    so its time/OCR/use-item branch is unreachable. We preserve the effective
    march-row flow here and retain the configured target for status/logging.
    """
    if not _SPEED_LOCK.acquire(blocking=False):
        return False
    try:
        bot.log(f"Speed Marching: target {target_seconds}s")
        targets = [
            (f"{SPEED}/CheckUseMarching.png", "done"),
            (f"{SPEED}/NgoaiThanh.png", "outside"),
            (f"{SPEED}/TrongThanh.png", "tap"),
            *[(path, "back") for path in exit_images()],
            *[(path, "tap") for path in click_images()],
        ]
        checks = 0
        while checks <= 5:
            screen = bot.screenshot()
            marching = bot.find_all(f"{SPEED}/MarchingBoss.png", threshold=0.8, screen=screen)
            if marching:
                # This is the effective behaviour of SpeedBoss.cs (option is
                # forcibly set to 2 there): open the first boss march row.
                bot.tap(200, marching[0][1] + 10, delay=2)
                checks += 1
                continue
            action, pos = find_first(bot, screen, targets)
            if action == "done":
                return True
            if action == "outside":
                checks += 1
                delay(bot, 1)
            elif action == "tap":
                bot.tap(*pos, delay=2)
            elif action == "back":
                bot.back(delay=2)
            else:
                go_home(bot, screen)
                delay(bot, 2)
                checks += 1
        return True
    finally:
        _SPEED_LOCK.release()
