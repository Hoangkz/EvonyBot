"""
battlefield_shop — "Battlefield Shop" activity (port of C# Battlefield).

- run.py:       entry point, `run(bot, settings)`: the shop, then Open Gift
                Box / Black Market when ticked
- shop.py:      Shop — buy in the Battlefield Shop, refresh, repeat
- constants.py: Battlefield Shop image folders and limits
"""
from .run import run

__all__ = ["run"]
