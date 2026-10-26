"""Claim Ancient Dynasty Treasury and require its opened-chest state."""
from ...common import GiftTask, TEXT_CLAIM_CONTROLS
from ...screens import GiftScreen
from ..named_flow import ExactFlow, run_carousel_exact

KEY = "gift_ancient_dynasty_treasury"
FLOW = ExactFlow(
    navigation=("ValuableEvent/AncientDynastyTreasury/label_daily_free",
                "ValuableEvent/AncientDynastyTreasury/button_daily_free"),
    # The new capture contains only the text. The chest centre is 24 px above
    # its centre at the 396 px reference width. The legacy full crop is tapped
    # at its own centre as a fallback.
    navigation_offsets=((0, -24), (0, 0)),
    navigation_first_match=True,
    claims=TEXT_CLAIM_CONTROLS,
    done=("ValuableEvent/AncientDynastyTreasury/status_done",),
)


def run(bot):
    return run_carousel_exact(
        bot,
        GiftScreen.VALUABLE_EVENT,
        "ValuableEvent/title",
        "ValuableEvent/AncientDynastyTreasury/tab",
        FLOW,
    )


TASK = GiftTask(KEY, "Ancient Dynasty Treasury", run)
