"""Open Sulis Wishing Pool when its header dot is present.

Some rotations clear the dot without showing a claim control. Opening the tab is
therefore the only safe action; the runner deliberately never taps Make a Wish.
"""
from .common import GiftTask, return_home, select_carousel_tab
from .lobby import open_named
from .screens import GiftScreen

KEY = "gift_sulis_wishing"


def run(bot):
    opened = (open_named(bot, GiftScreen.VALUABLE_EVENT)
              and select_carousel_tab(bot, "ValuableEvent/title", "SulisWishing/tab"))
    if opened:
        bot.log("Gift Claims: Sulis Wishing opened; no free claim control shown")
        return_home(bot)
    return opened


TASK = GiftTask(KEY, "Sulis Wishing Pool", run)
