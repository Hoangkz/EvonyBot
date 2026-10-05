"""
market.py — Market: opens the Black Market, buys every wanted item on it,
then pays to Refresh and buys again, until the Refresh / Quantity Buy
limits are reached, gems run out, or (CheckGold) gold drops under
2,000,000.

Each loop takes one screenshot, finds the first image of `_targets()` on
it (checked in list order) and calls the handler next to that image.
While on the market it alternates: scan the page for wanted items, buy
them one by one, Refresh, scan again...
"""
from ...common import click_images, delay, exit_images, find_first, go_home, images_in
from ...ocr import MarketBalance, read_market_balance
from .constants import (BALANCE_RETRIES, BM, BUY, BUY_THRESHOLD, GEM_ICONS,
                        GEM_ICON_THRESHOLD, GOLD_ICONS, GOLD_ICON_THRESHOLD, MARKET_REGION,
                        MARKET_SLOTS, MIN_GOLD, PRICE_HALF)


class Market:
    def __init__(self, bot, settings: dict):
        self.bot = bot
        items = settings.get("black_market_items", {})
        self.buy_with_gems = bool(items.get("Resources Gem"))
        self.check_gold = bool(items.get("CheckGold"))
        self.event = bool(items.get("Event"))
        self.buy_images = _buy_images(items)
        self.refresh_limit = _limit(settings.get("refresh"))
        self.buy_limit = _limit(settings.get("quantity_buy"))

        self.done = False
        self.points: list[tuple[int, int]] = []     # slots still to buy on this page
        # True: scan the market page next; False: it was just scanned, so
        # once its items are bought, Refresh next.
        self.need_scan = True
        self.refreshes = 0
        self.bought = 0
        self.balance_misses = 0     # C# goldTemp, now covers both wallet values
        self.balance = MarketBalance(None, None)
        self.pending: str | None = None   # "buy" / "refresh"; confirmations are not equivalent

    def run(self):
        targets = self._targets()
        while not self.done:
            screen = self.bot.screenshot()
            handler, pos = find_first(self.bot, screen, targets)
            (handler or self.on_unknown)(screen, pos)

    def _targets(self):
        """(image, handler) checked in this order each loop."""
        return [
            (f"{BM}/buyKc.png", self.on_out_of_gems),
            (f"{BM}/xacnhan.png", self.on_confirm),
            (f"{BM}/Refresh.png", self.on_market),
            (f"{BM}/BlackMarketCheck.png", self.on_tap),
            (f"{BM}/goto.png", self.on_goto),
            (f"{BM}/ResourcesTax.png", self.on_tap),
            (f"{BM}/2ResourcesTax.png", self.on_tap),
            (f"{BM}/ChoDen.png", self.on_tap),
            (f"{BM}/DaiLyActivites.png", self.on_daily_list),
            *[(path, self.on_back) for path in exit_images()],
            *[(path, self.on_tap) for path in click_images()],
            (f"{BM}/activites.png", self.on_tap),
            (f"{BM}/chucnang.png", self.on_tap),
        ]


    # ---- handlers: on the market -------------------------------------
    def on_out_of_gems(self, screen, pos):
        """Buy-gems dialog: close it and finish."""
        self.bot.back()
        self.bot.back()
        self.done = True

    def on_confirm(self, screen, pos):
        """Confirm an item purchase. Refresh confirmations are handled in
        ``_refresh`` so they can never increment the purchase counter."""
        if self.pending != "buy":
            self.bot.record("Black Market: unexpected confirmation, closing")
            self.bot.back()
            self.pending = None
            delay(self.bot, 2)
            return
        self.bot.tap(*pos)
        self.bought += 1
        self.pending = None
        delay(self.bot, 3)

    def on_market(self, screen, refresh_pos):
        """Market is open: buy the next wanted slot, else scan or refresh."""
        if self.points:
            self.bot.tap(*self.points.pop(0))
            self.pending = "buy"
            delay(self.bot, 2)
        elif self.need_scan:
            self._scan(screen)
        else:
            self._refresh(screen, refresh_pos)

    # ---- handlers: getting to the market ------------------------------
    # Leaving the market page means it has to be scanned again.
    def on_goto(self, screen, pos):
        self.need_scan = True
        self.bot.tap(*pos)
        delay(self.bot, 6)
        self.bot.tap_percent(50, 49)
        delay(self.bot)

    def on_daily_list(self, screen, pos):
        """Daily activities list: scroll to the Black Market, or finish if it's
        not there (the "khoangden" end of the list is showing)."""
        self.need_scan = True
        if self.bot.find("DailyActivites/khoangden.png", screen=screen) is not None:
            self.bot.back()
            self.done = True
            return
        self.bot.swipe_percent(50, 50, 50, 32, duration=1.0)
        delay(self.bot)

    def on_back(self, screen, pos):
        self.need_scan = True
        self.bot.back()
        delay(self.bot, 3)

    def on_tap(self, screen, pos):
        self.need_scan = True
        self.bot.tap(*pos)
        delay(self.bot, 3)

    def on_unknown(self, screen, pos):
        go_home(self.bot, screen)

    # ---- scan ----------------------------------------------------------
    def _scan(self, screen):
        """Collect the slots of every wanted item on this market page."""
        bot = self.bot
        self._read_balance(screen)
        gem_slots = _currency_slots(bot, screen, GEM_ICONS, GEM_ICON_THRESHOLD)
        found = []
        for path in self.buy_images:
            slots = [_cell(p) for p in
                     bot.find_all(path, threshold=BUY_THRESHOLD, screen=screen, center=False)]
            if slots and "Chips" not in path and "Stamina" not in path:
                slots = self._drop_paid_slots(screen, slots, gem_slots)
            found += slots
        points = list(dict.fromkeys(found))
        # When gem purchases are enabled, an OCR value of zero is definitive:
        # do not open a purchase popup that cannot succeed.  ``None`` remains
        # compatible with the C# retry behaviour instead of assuming zero.
        if self.balance.gems == 0:
            points = [point for point in points if point not in gem_slots]
        self.points = points
        self.need_scan = False

    def _drop_paid_slots(self, screen, slots, gem_slots):
        """Resources priced in gems (unless "Resources Gem") and, without
        "Event", resources priced in gold are skipped."""
        if gem_slots and not self.buy_with_gems:
            slots = [s for s in slots if s not in gem_slots]
        if slots and not self.event:
            gold_slots = _currency_slots(self.bot, screen, GOLD_ICONS, GOLD_ICON_THRESHOLD)
            slots = [s for s in slots if s not in gold_slots]
        return slots

    # ---- refresh -------------------------------------------------------
    def _refresh(self, screen, refresh_pos):
        """Pay to refresh the market, unless a limit is reached or gold is low."""
        bot = self.bot
        if self._limits_reached():
            self.done = True
            return
        if self.check_gold:
            too_low = self._gold_too_low(screen)
            if too_low is None:
                return
            if too_low:
                self.done = True
                return

        self.balance_misses = 0
        self.refreshes += 1
        before = bot.crop(screen, *MARKET_REGION)
        bot.tap(*refresh_pos)
        self.pending = "refresh"
        delay(bot, 2)
        # Wait (up to 10 s) until the market slots change.
        for _ in range(10):
            current = bot.screenshot()
            confirm = bot.find(f"{BM}/xacnhan.png", screen=current)
            if confirm is not None:
                balance = self._read_balance(current)
                if balance.gems is None or balance.gems <= 0:
                    bot.record("Black Market: cannot verify gems for paid refresh, stopping")
                    bot.back()
                    self.done = True
                    self.pending = None
                    return
                bot.tap(*confirm)
                bot.record(f"Black Market: confirmed paid refresh ({balance.gems} gems available)")
                delay(bot, 2)
                continue
            if bot.find(before, screen=current) is None:
                break
            delay(bot)
        self.pending = None
        self.need_scan = True

    def _limits_reached(self) -> bool:
        return ((self.buy_limit != -1 and self.bought >= self.buy_limit)
                or (self.refresh_limit != -1 and self.refreshes >= self.refresh_limit))

    def _gold_too_low(self, screen) -> bool | None:
        """CheckGold using OCR of the Black Market wallet row.

        As in C#, two unreadable frames are tolerated before the check is
        skipped for this refresh.  A real zero is never treated as an OCR
        failure.
        """
        balance = self._read_balance(screen)
        if balance.gold is not None:
            self.balance_misses = 0
            return balance.gold < MIN_GOLD
        if self.balance_misses == BALANCE_RETRIES:
            self.balance_misses = 0
            return False
        self.balance_misses += 1
        delay(self.bot)
        return None

    def _read_balance(self, screen) -> MarketBalance:
        balance = read_market_balance(screen)
        self.balance = balance
        if balance != MarketBalance(None, None):
            self.bot.log(f"Black Market: wallet gold={balance.gold}, gems={balance.gems}")
        return balance


def to_int(text, default: int) -> int:
    try:
        return int(text)
    except (TypeError, ValueError):
        return default


def _limit(text) -> int:
    """Refresh / Quantity Buy combo -> count (-1 = "ALL", no limit)."""
    return to_int(text, -1)


def _buy_images(items: dict) -> list[str]:
    """Images of the items to buy, from the "Select Black Market" checkboxes."""
    images = []
    if items.get("Resources"):
        images += images_in(f"{BUY}/Resources")
    if items.get("Stamina"):
        images.append(f"{BUY}/Stamina.png")
    if items.get("Chips"):
        images.append(f"{BUY}/Chips.png")
    if items.get("Event"):
        images += [f"{BUY}/Chips.png", *images_in(f"{BUY}/Resources"), *images_in(f"{BUY}/Event")]
    return list(dict.fromkeys(images))     # drop duplicates, keep order


def _cell(point: tuple[int, int]) -> tuple[int, int]:
    """Snap a match (top-left corner) to the tap point of its market slot
    (3 columns x 2 rows), exactly as the C# code did."""
    x, y = point
    if x < 140:
        x = 80
    elif 140 < x < 250:
        x = 200
    elif x > 250:
        x = 320
    if y < 400:
        y = 365
    elif y > 400:
        y = 522
    return x, y


def _currency_slots(bot, screen, icons: tuple[str, ...], threshold: float) -> list[tuple[int, int]]:
    """Market slots whose price button contains one of ``icons``.

    Looking only in the six price buttons avoids false positives from the
    wallet row and from gold/gem artwork inside the item cards.
    """
    hw, hh = PRICE_HALF
    found = []
    for point in MARKET_SLOTS:
        x, y = point
        area = bot.crop(screen, x - hw, y - hh, 2 * hw, 2 * hh)
        if any(bot.find(icon, threshold=threshold, screen=area) is not None for icon in icons):
            found.append(point)
    return found
