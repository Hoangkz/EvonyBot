"""
shop.py — Shop (port of C# BattlefieldShop): opens the Battlefield Shop
from Daily Activities, buys every item whose image is in
BattlefieldShop/buy, then pays to Refresh and buys again, until the
"Quantity To Refresh" limit is reached, medals drop under 310 or gems run
out.

Each loop takes one screenshot, finds the first image of `_targets()` on
it (checked in list order) and calls the handler next to that image.
"""
from ...common import click_images, delay, exit_images, find_first, go_home, images_in
from ...ocr import read_number
from .constants import BM, BS, BUY, BUY_THRESHOLD, MEDALS_WIDTH, MIN_MEDALS, SHOP_REGION
# TODO: cần làm lại.


class Shop:
    def __init__(self, bot, refresh_limit: int):
        self.bot = bot
        self.buy_images = images_in(BUY)
        self.refresh_limit = refresh_limit      # -1 = "ALL", no limit

        self.done = False
        self.points: list[tuple[int, int]] = []     # slots still to buy on this page
        # True: scan the shop page next; False: it was just scanned, so once
        # its items are bought, Refresh next (C# !(checkTemp && refresmarket)).
        self.need_scan = True
        self.refreshes = 0
        # Last button tapped by on_tap: like the C# code (option kept from the
        # previous loop), it is tapped again when nothing known is on screen.
        # TODO: check lại — stuck on an unknown screen = tap forever, never go_home.
        self.last_tap = None

    def run(self):
        targets = self._targets()
        while not self.done:
            screen = self.bot.screenshot()
            handler, pos = find_first(self.bot, screen, targets)
            (handler or self.on_unknown)(screen, pos)

    def _targets(self):
        """(image, handler) checked in this order each loop."""
        # TODO: check lại — C# used the {language} folder for buyKc / xacnhan /
        # Refresh / goto / DaiLyActivites / activites; here the Black Market copies.
        return [
            (f"{BM}/buyKc.png", self.on_out_of_gems),
            (f"{BM}/xacnhan.png", self.on_confirm),
            (f"{BM}/Refresh.png", self.on_shop),
            (f"{BS}/vaoshop.png", self.on_tap),
            (f"{BS}/openshop.png", self.on_tap),
            (f"{BM}/goto.png", self.on_tap),
            # TODO: check lại — C# Items/{language}/success.png is not in Images/.
            ("en/success.png", self.on_back),
            (f"{BS}/rss.png", self.on_tap),
            ("DailyActivites/itemDone.png", self.on_tap),
            (f"{BM}/DaiLyActivites.png", self.on_daily_list),
            *[(path, self.on_back) for path in exit_images()],
            *[(path, self.on_tap) for path in click_images()],
            (f"{BM}/activites.png", self.on_tap),
            (f"{BM}/chucnang.png", self.on_tap),
        ]

    # ---- handlers: in the shop -----------------------------------------
    def on_out_of_gems(self, screen, pos):
        """Buy-gems dialog: close it and finish."""
        self.bot.back()
        self.bot.back()
        self.done = True

    def on_confirm(self, screen, pos):
        self.last_tap = None
        self.bot.tap(*pos)
        delay(self.bot, 3)

    def on_shop(self, screen, refresh_pos):
        """Shop is open: buy the next wanted slot, else scan or refresh."""
        self.last_tap = None
        if self.points:
            self.bot.tap(*self.points.pop(0))
            delay(self.bot, 3)
        elif self.need_scan:
            self._scan(screen)
        else:
            self._refresh(screen, refresh_pos)

    # ---- handlers: getting to the shop ---------------------------------
    # Leaving the shop page means it has to be scanned again.
    def on_daily_list(self, screen, pos):
        """Daily activities list: scroll to the Battlefield Shop, or finish if
        it's not there (the "khoangden" end of the list is showing)."""
        self.need_scan = True
        self.last_tap = None
        if self.bot.find("DailyActivites/khoangden.png", screen=screen) is not None:
            self.bot.back()
            self.done = True
            return
        self.bot.swipe_percent(50, 50, 50, 32, duration=1.0)
        delay(self.bot)

    def on_back(self, screen, pos):
        self.need_scan = True
        self.last_tap = None
        self.bot.back()
        delay(self.bot, 3)

    def on_tap(self, screen, pos):
        self.need_scan = True
        self.last_tap = pos
        self.bot.tap(*pos)
        delay(self.bot, 4)

    def on_unknown(self, screen, pos):
        if self.last_tap is not None:
            self.bot.tap(*self.last_tap)
            delay(self.bot, 4)
            return
        self.need_scan = True
        go_home(self.bot, screen)

    # ---- scan ----------------------------------------------------------
    def _scan(self, screen):
        """Collect the slots of every wanted item on this shop page."""
        found = []
        for path in self.buy_images:
            found += [_cell(p) for p in self.bot.find_all(
                path, threshold=BUY_THRESHOLD, screen=screen, center=False)]
        self.points = list(dict.fromkeys(found))
        self.need_scan = False

    # ---- refresh -------------------------------------------------------
    def _refresh(self, screen, refresh_pos):
        """Pay to refresh the shop, unless the limit is reached or medals are low."""
        bot = self.bot
        if self.refresh_limit != -1 and self.refreshes >= self.refresh_limit:
            self.done = True
            return
        pos = bot.find(f"{BS}/tien2.png", screen=screen, center=False)
        if pos is None:
            bot.back()
            delay(bot, 2)
            return
        w, h = bot.template_size(f"{BS}/tien2.png")
        # TODO: check lại — C# read this with KAutoHelper Get_Text, not read_number.
        if read_number(bot.crop(screen, pos[0] + w, pos[1], MEDALS_WIDTH, h)) < MIN_MEDALS:
            self.done = True
            return

        before = bot.crop(screen, *SHOP_REGION)
        bot.tap(*refresh_pos)
        delay(bot, 2)
        # Wait (up to 10 s) until the shop slots change.
        for _ in range(10):
            if bot.find(before) is None:
                break
            delay(bot)
        self.refreshes += 1
        self.need_scan = True


def _cell(point: tuple[int, int]) -> tuple[int, int]:
    """Snap a match (top-left corner) to the tap point of its shop slot
    (3 columns x 2 rows), exactly as the C# code did."""
    x, y = point
    if x < 200:
        x = 120
    elif 200 < x < 350:
        x = 270
    elif x > 350:
        x = 440
    if y < 500:
        y = 540
    elif y > 500:
        y = 750
    return x, y
