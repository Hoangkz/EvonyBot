"""
run.py — entry point of the "Black Market" activity.
"""
from .market import Market


def run(bot, settings: dict):
    """`bot` is the device's BotContext; `settings` is the "Black Market" tab's config. Cấu hình cũ còn
    `auction_is_buy` / `auction_max_price` (chế độ Auction House đã xoá) thì bỏ qua."""
    Market(bot, settings).run()
