"""
go_home.py — Utils.Home.
"""
from .current_focus import current_focus
from .delay import delay

GAME_PACKAGE = "com.topgamesinc.evony"
TO_CITY = "CityMap/toCity.png"   # nút góc dưới phải khi đang ở bản đồ thế giới (hình toà thành): bấm để về thành
TO_CITY_REGION = (70, 80, 100, 100)   # % màn hình: góc dưới phải
TO_CITY_WAIT = 4             # giây chờ game chuyển về màn thành sau khi bấm
# Hộp "Are you sure you want to exit the game?" (Back ở màn thành sạch / có menu công trình mở ra hộp này): bấm Cancel, không Back
# (Back lúc đó tắt hộp rồi lại mở lại, lặp mãi).
EXIT_DIALOG = "en/exitGame.png"
EXIT_CANCEL = "en/exitCancel.png"
EXIT_THRESHOLD = 0.85
# Menu tròn của công trình (Train / Detail / Upgrade...): Back KHÔNG đóng được mà mở hộp thoát game. Nhận ra bằng icon "Detail"
# (có ở mọi công trình, vị trí cung tròn đổi theo công trình), đóng bằng cách bấm đất trống (lần lượt từng điểm, % màn hình).
RADIAL_MENU = "CityMap/radialDetail.png"
RADIAL_CLOSE_TAPS = ((50, 63), (30, 45), (70, 63))


def go_home(bot, screen):
    """Utils.Home(auto, screen) — called when nothing known is on screen:
    - on the Android launcher (game not open): launch the game, wait up to
      15 s for "Try again" and tap through the loading screen;
    - game shows a load error, or the "new game updates, Restart" popup:
      force-stop it (next Home call relaunches);
    - exit-game dialog: tap Cancel;
    - a building's round menu is open (Back cannot close it): tap empty ground;
    - on the world map (city button at the bottom right): tap it to return to
      the city (BACK on the world map does not leave it);
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
    elif (bot.find(EXIT_DIALOG, threshold=EXIT_THRESHOLD, screen=screen) is not None
          and (cancel := bot.find(EXIT_CANCEL, threshold=EXIT_THRESHOLD, screen=screen)) is not None):
        bot.log("Home: exit dialog, tap Cancel")
        bot.tap(*cancel, delay=1)
    elif bot.find(RADIAL_MENU, screen=screen) is not None:
        tried = getattr(bot, "_radial_close_tries", 0)
        x, y = RADIAL_CLOSE_TAPS[tried % len(RADIAL_CLOSE_TAPS)]
        bot._radial_close_tries = tried + 1
        bot.log("Home: building menu open, tap empty ground to close it")
        bot.tap_percent(x, y, delay=1)
    elif (to_city := bot.find(TO_CITY, screen=screen, region=TO_CITY_REGION)) is not None:
        bot.log("Home: on the world map, tap the city button")
        bot.tap(*to_city, delay=TO_CITY_WAIT)
    else:
        bot.back()
