"""Inspect Active Monthly Card without touching its paid button."""
from ...common import GiftTask
from ...screens import GiftScreen
from ..named_flow import ExactFlow, run_carousel_exact

KEY = "gift_active_monthly_card"
FLOW = ExactFlow(
    opened=("ActiveMonthlyCard/purchase_marker",),
    navigation=("Common/button_reward_chest",),
    done=("ActiveMonthlyCard/button_go", "ActiveMonthlyCard/button_continue"),
    fallback_tap=(45, 190),
    navigation_threshold=0.80,
)


def run(bot):
    return run_carousel_exact(bot, GiftScreen.VALUABLE_EVENT,
                              "ValuableEvent/title", "ActiveMonthlyCard/tab", FLOW)


TASK = GiftTask(KEY, "Active Monthly Card", run)
