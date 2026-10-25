"""Claim the rotating Strategic Stockpile free chest."""
from ...common import GiftTask
from ...lobby import open_named
from ...screens import GiftScreen
from ..named_flow import ExactFlow, run_carousel_exact

KEY = "gift_strategic_stockpile"
FLOW = ExactFlow(
    opened=("ValuableEvent/StrategicStockpile/title",),
    claims=("ValuableEvent/StrategicStockpile/button_free_text",),
    done=("ValuableEvent/StrategicStockpile/chest_claimed",),
    # Check that Free is really present, then tap ten pixels to its right and
    # ten pixels above as measured on the current Strategic Stockpile layout.
    claim_offset=(10, -10),
)


def run(bot):
    return run_carousel_exact(bot, GiftScreen.VALUABLE_EVENT,
                              "ValuableEvent/title",
                              "ValuableEvent/StrategicStockpile/tab_current", FLOW)


TASK = GiftTask(KEY, "Strategic Stockpile", run)
