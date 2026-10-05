"""
black_market — "Black Market" activity (port of C# BlackMarket).

- run.py:           entry point, `run(bot, settings)`: the Black Market
- market.py:        Market — buy on the Black Market, refresh, repeat
- constants.py:     Black Market image folders and limits
"""
from .run import run

__all__ = ["run"]
