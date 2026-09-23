"""
black_market.py — "Black Market" activity (port of C# BlackMarket).

With Auction House "Is Buy" ticked, bids in the Auction House instead
(see _auction_house.py). Otherwise opens the Black Market, buys every
wanted item on it, then pays to Refresh and buys again, until the
Refresh / Quantity Buy limits are reached, gems run out, or (CheckGold)
gold drops under 2,000,000. Each loop takes one screenshot, finds the
first known image on it (checked in list order) and acts on it.
"""
from ..ocr import read_number
from ._auction_house import buy_auction_house
from ._common import click_images, delay, exit_images, go_home, images_in

BM = "Black Market"
BUY = f"{BM}/buy"

MIN_GOLD = 2_000_000
BUY_THRESHOLD = 0.85
GEMS_MIN_Y = 240            # gem price tags above this are not market slots
# (x, y, w, h) compared before/after Refresh to tell when the market changed.
MARKET_REGION = (45, 330, 120, 400)

# What to do when each image is seen.
OUT_OF_GEMS = "out_of_gems"     # buy-gems dialog -> close it and finish
CONFIRM = "confirm"             # purchase confirmation -> counts as one buy
REFRESH = "refresh"             # market open -> buy / refresh / scan
GOTO = "goto"
DAILY_LIST = "daily_list"       # daily activities list -> scroll to Black Market
TAP = "tap"
BACK = "back"


def run(bot, settings: dict):
    """`bot` is the device's BotContext; `settings` is the "Black Market" tab's config."""
    if settings.get("auction_is_buy"):
        price = _to_int(settings.get("auction_max_price"), 0)
        if price > 0:
            buy_auction_house(bot, price)
        return
    _Market(bot, settings).run()


def _to_int(text, default: int) -> int:
    try:
        return int(text)
    except (TypeError, ValueError):
        return default


def _limit(text) -> int:
    """Refresh / Quantity Buy combo -> count (-1 = "ALL", no limit)."""
    return _to_int(text, -1)


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


def _targets() -> list[tuple[str, str]]:
    return [
        (f"{BM}/buyKc.png", OUT_OF_GEMS),
        (f"{BM}/xacnhan.png", CONFIRM),
        (f"{BM}/Refresh.png", REFRESH),
        (f"{BM}/BlackMarketCheck.png", TAP),
        (f"{BM}/goto.png", GOTO),
        (f"{BM}/ResourcesTax.png", TAP),
        (f"{BM}/2ResourcesTax.png", TAP),
        (f"{BM}/ChoDen.png", TAP),
        (f"{BM}/DaiLyActivites.png", DAILY_LIST),
        *[(path, BACK) for path in exit_images()],
        *[(path, TAP) for path in click_images()],
        (f"{BM}/activites.png", TAP),
        (f"{BM}/chucnang.png", TAP),
    ]


def _find_first(bot, screen, targets):
    """First (action, pos) in `targets` whose image is on screen, else (None, None)."""
    for path, action in targets:
        pos = bot.find(path, screen=screen)
        if pos is not None:
            return action, pos
    return None, None


class _Market:
    def __init__(self, bot, settings: dict):
        self.bot = bot
        items = settings.get("black_market_items", {})
        self.buy_with_gems = bool(items.get("Resources Gem"))
        self.check_gold = bool(items.get("CheckGold"))
        self.event = bool(items.get("Event"))
        self.buy_images = _buy_images(items)
        self.refresh_limit = _limit(settings.get("refresh"))
        self.buy_limit = _limit(settings.get("quantity_buy"))

        self.points: list[tuple[int, int]] = []     # slots still to buy on this market
        self.scanned = False        # C# checkTemp: this market page was scanned
        self.can_refresh = False    # C# refresmarket: scanned since the last refresh
        self.refreshes = 0
        self.bought = 0
        self.gold_misses = 0        # C# goldTemp

    def run(self):
        bot = self.bot
        targets = _targets()
        while True:
            screen = bot.screenshot()
            action, pos = _find_first(bot, screen, targets)

            if action == OUT_OF_GEMS:
                bot.back()
                bot.back()
                return
            if action == REFRESH:
                if self._on_market(screen, pos):
                    return
            elif action == CONFIRM:
                bot.tap(*pos)
                self.bought += 1
                delay(bot, 3)
            elif action is None:
                go_home(bot, screen)
            else:
                self.scanned = False
                if self._navigate(action, pos, screen):
                    return

    def _on_market(self, screen, refresh_pos) -> bool:
        """Market is open. Returns True when the activity is finished."""
        if self.points:
            self.bot.tap(*self.points.pop(0))
            delay(self.bot, 2)
        elif self.scanned and self.can_refresh:
            return self._refresh(screen, refresh_pos)
        else:
            self._scan(screen)
        return False

    def _navigate(self, action, pos, screen) -> bool:
        """Getting to the market. Returns True when the activity is finished."""
        bot = self.bot
        if action == GOTO:
            bot.tap(*pos)
            delay(bot, 6)
            bot.tap_percent(50, 49)
            delay(bot)
        elif action == DAILY_LIST:
            if bot.find("DailyActivites/khoangden.png", screen=screen) is not None:
                bot.back()
                return True
            bot.swipe_percent(50, 50, 50, 32, duration=1.0)
            delay(bot)
        elif action == BACK:
            bot.back()
            delay(bot, 3)
        else:   # TAP
            bot.tap(*pos)
            delay(bot, 3)
        return False

    def _limits_reached(self) -> bool:
        return ((self.buy_limit != -1 and self.bought >= self.buy_limit)
                or (self.refresh_limit != -1 and self.refreshes >= self.refresh_limit))

    def _gold_too_low(self, screen) -> bool | None:
        """CheckGold: True if gold < MIN_GOLD, False if enough (or check
        skipped), None if the gold counter isn't visible yet."""
        if self.gold_misses == 2:
            self.gold_misses = 0
            return False
        bot = self.bot
        pos = bot.find(f"{BM}/goldCheck.png", screen=screen, center=False)
        if pos is None:
            self.gold_misses += 1
            delay(bot)
            return None
        w, h = bot.template_size(f"{BM}/goldCheck.png")
        gold = read_number(bot.crop(screen, pos[0] + w + 5, pos[1], 120, h))
        return gold < MIN_GOLD

    def _refresh(self, screen, refresh_pos) -> bool:
        """Pay to refresh the market. Returns True when the activity is finished."""
        bot = self.bot
        if self._limits_reached():
            return True
        if self.check_gold:
            too_low = self._gold_too_low(screen)
            if too_low is None:
                return False
            if too_low:
                return True

        self.gold_misses = 0
        self.refreshes += 1
        before = bot.crop(screen, *MARKET_REGION)
        bot.tap(*refresh_pos)
        delay(bot, 2)
        # Wait (up to 10 s) until the market slots change.
        for _ in range(10):
            if bot.find(before) is None:
                break
            delay(bot)
        self.scanned = True
        self.can_refresh = False
        return False

    def _scan(self, screen):
        """Collect the slots of every wanted item on this market page."""
        bot = self.bot
        self.scanned = True
        gem_slots = [_cell(p) for p in bot.find_all(f"{BM}/gems.png", screen=screen, center=False)
                     if p[1] > GEMS_MIN_Y]
        found = []
        for path in self.buy_images:
            slots = [_cell(p) for p in
                     bot.find_all(path, threshold=BUY_THRESHOLD, screen=screen, center=False)]
            if slots and "Chips" not in path and "Stamina" not in path:
                slots = self._drop_paid_slots(screen, slots, gem_slots)
            found += slots
        self.points = list(dict.fromkeys(found))
        self.can_refresh = True

    def _drop_paid_slots(self, screen, slots, gem_slots):
        """Resources priced in gems (unless "Resources Gem") and, without
        "Event", resources priced in gold are skipped."""
        if gem_slots and not self.buy_with_gems:
            slots = [s for s in slots if s not in gem_slots]
        if slots and not self.event:
            gold_slots = [_cell(p) for p in
                          self.bot.find_all(f"{BM}/buyVang.png", screen=screen, center=False)]
            slots = [s for s in slots if s not in gold_slots]
        return slots
