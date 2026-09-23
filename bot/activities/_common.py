"""
_common.py — helpers shared by several activities (ports of the C#
`Utils` class and the image folders every activity scans).
"""
from ..context import TEMPLATE_DIR

GAME_PACKAGE = "com.topgamesinc.evony"


def images_in(folder: str) -> list[str]:
    """Every .png in Images/<folder>, sorted, as paths relative to Images/."""
    return [f"{folder}/{p.name}" for p in sorted((TEMPLATE_DIR / folder).glob("*.png"))]


def exit_images() -> list[str]:
    """Images/exit — popups closed with the BACK key."""
    return images_in("exit")


def click_images() -> list[str]:
    """Images/click — buttons that are simply tapped when seen."""
    return images_in("click")


def delay(bot, seconds: float = 1.0):
    """Utils.delay(auto[, seconds])."""
    bot.sleep(seconds)


def _current_focus(bot) -> str:
    """The `mCurrentFocus` line of `dumpsys window`, lower-cased."""
    output = bot.shell("dumpsys window")
    return "\n".join(line for line in output.splitlines() if "mCurrentFocus" in line).lower()


def go_home(bot, screen):
    """Utils.Home(auto, screen) — called when nothing known is on screen:
    - on the Android launcher (game not open): launch the game, wait up to
      15 s for "Try again" and tap through the loading screen;
    - game shows a load error: force-stop it (next Home call relaunches);
    - otherwise: press BACK."""
    if "launcher" in _current_focus(bot):
        bot.log("Home: launching game")
        bot.shell(f"monkey -p {GAME_PACKAGE} -c android.intent.category.LAUNCHER 1")
        delay(bot, 1)
        for _ in range(15):
            pos = bot.find("en/tryagain.png")
            if pos is not None:
                bot.tap(*pos)
                bot.tap_percent(30, 59, count=15)
                return
            delay(bot)
    elif bot.find("en/errorload.png", threshold=0.7, screen=screen) is not None:
        bot.log("Home: load error, force-stopping game")
        bot.shell(f"am force-stop {GAME_PACKAGE}")
        delay(bot, 10)
    else:
        bot.back()
