"""Open Ancient Dynasty Treasury's Daily Free panel and claim its rewards."""
from ...common import GiftTask
from ...screens import GiftScreen
from ..named_flow import run_carousel_claim

KEY = "gift_ancient_dynasty_treasury"


def run(bot):
    return run_carousel_claim(
        bot,
        GiftScreen.VALUABLE_EVENT,
        "ValuableEvent/title",
        "AncientDynastyTreasury/tab",
        (),
        navigation=("AncientDynastyTreasury/button_daily_free",),
    )


TASK = GiftTask(KEY, "Ancient Dynasty Treasury", run)
