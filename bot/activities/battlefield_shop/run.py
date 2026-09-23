"""
run.py — entry point of the "Battlefield Shop" activity (port of C#
Battlefield): the shop, then Open Gift Box and/or the Black Market when
"OpenBox" / "Black Market" are ticked, each with its own tab's settings.
"""
from ...common import delay
from .. import open_gift_box
from ..black_market.market import Market, to_int
from .shop import Shop
# TODO: cần làm lại.


def run(bot, settings: dict):
    """`bot` is the device's BotContext; `settings` is the "Battlefield Shop" tab's config."""
    Shop(bot, to_int(settings.get("quantity_to_refresh"), -1)).run()

    if settings.get("open_box"):
        open_gift_box.run(bot, bot.settings.get("Open Gift Box", {}))
    if settings.get("black_market"):
        for _ in range(3):
            bot.back()
            delay(bot)
        Market(bot, bot.settings.get("Black Market", {})).run()
