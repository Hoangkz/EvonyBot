"""
go_home.py — Utils.Home.
"""
from .current_focus import current_focus
from .delay import delay

GAME_PACKAGE = "com.topgamesinc.evony"


def go_home(bot, screen):
    """Utils.Home(auto, screen) — called when nothing known is on screen:
    - on the Android launcher (game not open): launch the game, wait up to
      15 s for "Try again" and tap through the loading screen;
    - game shows a load error, or the "new game updates, Restart" popup:
      force-stop it (next Home call relaunches);
    - otherwise: press BACK."""
    if "launcher" in current_focus(bot):
        bot.record("Home: mở lại game")
        bot.shell(f"monkey -p {GAME_PACKAGE} -c android.intent.category.LAUNCHER 1")
        delay(bot, 1)
        for _ in range(15):
            pos = bot.find("en/tryagain.png")
            if pos is not None:
                bot.record("Home: game báo lỗi kết nối, bấm Try Again")
                bot.tap(*pos)
                bot.tap_percent(30, 59, count=15)
                return
            delay(bot)
    elif bot.find("en/errorload.png", threshold=0.7, screen=screen) is not None:
        bot.record("Home: load error, force-stopping game")
        bot.shell(f"am force-stop {GAME_PACKAGE}")
        delay(bot, 10)
    elif bot.find("en/restartgame.png", threshold=0.85, screen=screen) is not None:
        bot.record("Home: game báo có bản cập nhật cần Restart, tắt game mở lại")
        bot.shell(f"am force-stop {GAME_PACKAGE}")
        delay(bot, 10)
    else:
        bot.back()
