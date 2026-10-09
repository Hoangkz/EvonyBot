"""Open the red-dot Scores panel of Super Value Weekly Card."""
from .common import GiftTask
from .named_flow import run_carousel_claim
from .screens import GiftScreen

KEY = "gift_super_value_weekly_card"


def run(bot):
    return run_carousel_claim(bot, GiftScreen.VALUABLE_EVENT, "ValuableEvent/title",
                              "SuperValueWeeklyCard/tab", (),
                              navigation=("SuperValueWeeklyCard/button_scores",))


TASK = GiftTask(KEY, "Super Value Weekly Card", run)
