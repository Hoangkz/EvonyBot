"""General daily purchases shared by the Daily Activities tab.

This is a direct, bounded port of ``Data.BuyStamina`` and
``Data.BuyHammer`` from the C# project.  Both flows use the existing
``Images/JoinBoss/Buy`` templates; adaptive position caching makes repeated
matches use a small region while retaining a full-screen fallback.
"""
from ...common import click_images, delay, exit_images, find_first, go_home

BUY = "JoinBoss/Buy"
OPEN_FEATURES = "open_features"
TAP = "tap"
BACK = "back"
MAX_STEPS = 100


def _positions(bot):
    cache = getattr(bot, "_daily_image_positions", None)
    if cache is None:
        cache = {}
        bot._daily_image_positions = cache
    return cache


def _find(bot, screen, targets):
    return find_first(bot, screen, targets, position_cache=_positions(bot), fallback_full=True)


def _common_targets():
    return ([(path, BACK) for path in exit_images()]
            + [(path, TAP) for path in click_images()])


def buy_stamina(bot, quantity: int) -> bool:
    """Buy one stamina bundle with the requested 10/20/30 quantity."""
    quantity = max(1, int(quantity))
    targets = [
        (f"{BUY}/buystamina.png", "buy"),
        (f"{BUY}/stamina.png", "stamina"),
        (f"{BUY}/checkWar.png", "war_selected"),
        (f"{BUY}/war.png", TAP),
        (f"{BUY}/item.png", TAP),
        *_common_targets(),
        (f"{BUY}/chucnang.png", OPEN_FEATURES),
    ]
    war_scrolls = 0

    for _ in range(MAX_STEPS):
        bot.check()
        screen = bot.screenshot()
        action, pos = _find(bot, screen, targets)

        if action == "buy":
            plus_path = f"{BUY}/plus.png"
            plus = bot.find(plus_path, screen=screen)
            if plus is None:
                delay(bot)
                continue
            _positions(bot)[plus_path] = plus
            for _ in range(quantity - 1):
                bot.tap(*plus)
                delay(bot)
            bot.tap(screen.shape[1] // 2, plus[1] + 110, delay=5)
            return True
        if action == "stamina":
            bot.tap(334, pos[1], delay=2)
        elif action == "war_selected":
            bot.swipe_percent(50, 80, 50, 60, delay=2)
            war_scrolls += 1
            if war_scrolls > 4:
                bot.back(delay=2)
                war_scrolls = 0
        elif action == OPEN_FEATURES:
            bot.tap_percent(88.5, 5, delay=2)
        elif action == TAP:
            bot.tap(*pos, delay=2)
        elif action == BACK:
            bot.back(delay=2)
        else:
            go_home(bot, screen)
            delay(bot, 2)

    bot.log("Daily General: Buy Stamina stopped after too many unrecognized steps")
    return False


def buy_all_hammers(bot) -> bool:
    """Buy the hammer offer found in the Special section."""
    targets = [
        (f"{BUY}/bua.png", "hammer"),
        (f"{BUY}/checkSpecial.png", "special_selected"),
        (f"{BUY}/special.png", TAP),
        (f"{BUY}/item.png", TAP),
        *_common_targets(),
        (f"{BUY}/chucnang.png", OPEN_FEATURES),
    ]
    special_checks = 0

    for _ in range(MAX_STEPS):
        bot.check()
        screen = bot.screenshot()
        action, pos = _find(bot, screen, targets)

        if action == "hammer":
            plus_path = f"{BUY}/plus.png"
            plus = bot.find(plus_path, screen=screen)
            if plus is None:
                bot.tap_percent(87.5, 35, delay=2)
                continue
            _positions(bot)[plus_path] = plus
            # C# taps left of Plus to choose the maximum/all quantity.
            bot.tap(plus[0] - 20, plus[1] + 2)
            bot.tap(screen.shape[1] // 2, plus[1] + 110, delay=5)
            return True
        if action == "special_selected":
            bot.tap(*pos)
            special_checks += 1
            bot.tap_percent(87.5, 35, delay=2)
            if special_checks > 5:
                bot.log("Daily General: hammer offer not found")
                return False
        elif action == OPEN_FEATURES:
            bot.tap_percent(88.5, 5, delay=2)
        elif action == TAP:
            bot.tap(*pos, delay=2)
        elif action == BACK:
            bot.back(delay=2)
        else:
            go_home(bot, screen)
            delay(bot, 2)

    bot.log("Daily General: Buy All Hammers stopped after too many unrecognized steps")
    return False
