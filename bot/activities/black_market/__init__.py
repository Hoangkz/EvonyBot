"""
black_market — "Black Market" activity (port of C# BlackMarket).

- run.py:           entry point, `run(bot, settings)`: Auction House mode
                    when "Is Buy" is ticked, else the Black Market
- market.py:        Market — buy on the Black Market, refresh, repeat
- auction_house.py: Auction House mode — bid on VIP 5000 lots
- constants.py:     Black Market image folders and limits
"""
from .run import run

__all__ = ["run"]
