"""
run.py — entry point of the "Black Market" activity.
"""
from .auction_house import buy_auction_house
from .market import Market, to_int


def run(bot, settings: dict):
    """`bot` is the device's BotContext; `settings` is the "Black Market" tab's config."""
    if settings.get("auction_is_buy"):
        price = to_int(settings.get("auction_max_price"), 0)
        if price > 0:
            buy_auction_house(bot, price)
        return
    Market(bot, settings).run()
