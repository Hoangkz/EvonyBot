"""Open the shared glowing reward chest on Super Value Weekly Card."""
from ...common import GiftTask
from ..named_flow import ExactFlow, run_carousel_exact
from ...screens import GiftScreen

KEY = "gift_super_value_weekly_card"
FLOW = ExactFlow(
    navigation=("Common/button_reward_chest",),
    done=("ValuableEvent/SuperValueWeeklyCard/button_continue",
          "ValuableEvent/SuperValueWeeklyCard/button_go"),
    fallback_tap=(45, 190),
    navigation_threshold=0.80,
)


def run(bot):
    return run_carousel_exact(bot, GiftScreen.VALUABLE_EVENT,
                              "ValuableEvent/title",
                              "ValuableEvent/SuperValueWeeklyCard/tab_icon", FLOW)


TASK = GiftTask(KEY, "Super Value Weekly Card", run)
