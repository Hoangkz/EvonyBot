"""
auction_house.py — Black Market's Auction House mode (port of C#
BuyActionHouse): opens Event Center -> Auction House and keeps bidding on
VIP 5000 lots while the current bid + 5000 stays within the Max Price.
Like the C# code it never finishes on its own; it runs until Stop.
"""
from ...ocr import read_number
from ...common import click_images, delay, exit_images, find_first, go_home

AH = "Black Market/AuctionHouse"
BID_STEP = 5000
LOT_HEIGHT = 100            # screen band below a "VIP 5000" tag holding its bid row
BID_RIGHT_MARGIN = 103      # width cut off the right of the current-bid value

# What to do when each image is seen.
CONFIRM = "confirm"
BOUGHT = "bought"           # "Buy" result -> close twice
NOT_BUY = "not_buy"
LOT = "lot"                 # VIP 5000 lot -> read its bid, bid if cheap enough
LOT_LIST = "lot_list"       # rare goods list -> scroll it
EVENT_CENTER = "event_center"
OPEN_MENU = "open_menu"     # main menu -> find and tap Event
TAP = "tap"
BACK = "back"


class _AuctionHouse:
    def __init__(self, bot, max_price: int):
        self.bot = bot
        self.max_price = max_price
        self.event_scrolls = 0      # C# checkScroll
        self.list_scrolls = 0       # C# scrollAuctionHouse

    def run(self):
        bot = self.bot
        targets = _targets()
        while True:
            screen = bot.screenshot()
            # A lot's bid row is measured from the top of its VIP tag.
            action, pos = find_first(bot, screen, targets, top_left={LOT})
            if action is None:
                go_home(bot, screen)
            else:
                self._handle(action, pos, screen)

    def _handle(self, action, pos, screen):
        bot = self.bot
        if action == LOT:
            self._bid(screen, pos[1])
        elif action == LOT_LIST:
            self._scroll_list()
        elif action == EVENT_CENTER:
            self._scroll_event_center()
        elif action == OPEN_MENU:
            self._open_event(screen)
        elif action == BOUGHT:
            bot.back()
            bot.back()
            delay(bot, 3)
        elif action == NOT_BUY:
            bot.tap_percent(50, 10)
            bot.back()
            delay(bot, 3)
        elif action == BACK:
            bot.back()
            delay(bot, 3)
        else:   # CONFIRM, TAP
            bot.tap(*pos)
            delay(bot, 3)

    def _bid(self, screen, top: int):
        bot = self.bot
        height, width = screen.shape[:2]
        band = bot.crop(screen, 0, top, width, min(LOT_HEIGHT, height - top))
        current = bot.find(f"{AH}/currentBid.png", screen=band, center=False)
        if current is None:
            self._scroll_list()
            return
        w, h = bot.template_size(f"{AH}/currentBid.png")
        value = bot.crop(band, current[0] + w, current[1],
                         width - BID_RIGHT_MARGIN - current[0] - w, h)
        if read_number(value) + BID_STEP > self.max_price:
            delay(bot, 3)
            return
        bid = bot.find(f"{AH}/bid.png", screen=band)
        if bid is not None:
            bot.tap(bid[0], bid[1] + top)
        delay(bot, 3)

    def _scroll_list(self):
        """Scroll the lot list down 6 times, then back up 6 times, and repeat."""
        bot = self.bot
        if self.list_scrolls < 6:
            bot.swipe_percent(10, 90, 10, 70, duration=1.0)
        else:
            bot.swipe_percent(10, 70, 10, 90, duration=1.0)
        delay(bot, 2)
        self.list_scrolls = (self.list_scrolls + 1) % 12

    def _scroll_event_center(self):
        """Look for the Auction House in Event Center; after 10 scrolls, back out."""
        bot = self.bot
        if self.event_scrolls == 10:
            self.event_scrolls = 0
            bot.back()
            delay(bot, 5)
            return
        self.event_scrolls += 1
        bot.swipe_percent(70, 70, 50, 50, duration=1.0)
        delay(bot, 2)

    def _open_event(self, screen):
        """Main menu: tap Event (retrying up to 10 fresh screenshots)."""
        bot = self.bot
        pos = bot.find(f"{AH}/Event.png", threshold=0.8, screen=screen)
        for _ in range(10):
            if pos is not None:
                break
            pos = bot.find(f"{AH}/Event.png")
        if pos is not None:
            bot.tap(*pos)
            delay(bot, 8)

def buy_auction_house(bot, max_price: int):
    _AuctionHouse(bot, max_price).run()


def _targets() -> list[tuple[str, str]]:
    return [
        (f"{AH}/comfirm.png", CONFIRM),
        (f"{AH}/buildlogexit.png", BACK),
        (f"{AH}/Buy.png", BOUGHT),
        (f"{AH}/notBuyOk.png", NOT_BUY),
        (f"{AH}/vip5000.png", LOT),
        (f"{AH}/ragegoods.png", LOT_LIST),
        (f"{AH}/ragegoodsTemp.png", TAP),
        (f"{AH}/daugia.png", TAP),
        (f"{AH}/eventcenter.png", EVENT_CENTER),
        *[(path, BACK) for path in exit_images()],
        *[(path, TAP) for path in click_images()],
        ("Black Market/chucnang.png", OPEN_MENU),
    ]

