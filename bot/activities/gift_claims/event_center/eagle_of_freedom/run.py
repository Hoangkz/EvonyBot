"""Eagle of Freedom policy in Event Center > Limited."""
from ...screens import GiftScreen
from ..policy import EventPolicy, run_opened_event

KEY = "gift_eagle_of_freedom"
POLICY = EventPolicy(
    "Eagle of Freedom",
    key=KEY,
    screen=GiftScreen.EAGLE_OF_FREEDOM,
)


def run(bot):
    return run_opened_event(bot, POLICY)
