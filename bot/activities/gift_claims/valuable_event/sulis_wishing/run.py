"""Open Sulis Wishing Pool when its named carousel tab is present.

The runner finds the task by its tab image and deliberately never taps Make a
Wish.
"""
from ...common import GiftTask, return_home, select_carousel_tab
from ...lobby import open_named
from ...screens import GiftScreen

KEY = "gift_sulis_wishing"


def run(bot):
    opened = (open_named(bot, GiftScreen.VALUABLE_EVENT)
              and select_carousel_tab(bot, "ValuableEvent/title", "SulisWishing/tab"))
    if opened:
        bot.log("Gift Claims: Sulis Wishing opened; no free claim control shown")
        return_home(bot)
    return opened


TASK = GiftTask(KEY, "Sulis Wishing Pool", run)
