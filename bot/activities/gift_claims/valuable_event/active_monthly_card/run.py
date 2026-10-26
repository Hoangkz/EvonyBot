"""Inspect Active Monthly Card without touching its paid button."""
from ...common import GiftTask
from ...screens import GiftScreen
from ..named_flow import ExactFlow, run_carousel_exact

KEY = "gift_active_monthly_card"
FLOW = ExactFlow(
    opened=("ValuableEvent/ActiveMonthlyCard/purchase_marker",),
    navigation=("Common/button_reward_chest",),
    claims=("ValuableEvent/ActiveMonthlyCard/button_claim",),
    # Vùng xanh trên ảnh tham chiếu 396x704: x xấp xỉ 16..380,
    # y xấp xỉ 415..697. Giữ cả tìm nút, lướt và dHash trong vùng này.
    claim_region=(4, 59, 96, 99),
    absence_done=True,
    scroll_claims=True,
    scroll_start=(50, 92),
    scroll_end=(50, 65),
    scroll_region=(4, 59, 96, 99),
    confirm_scroll_edges=True,
    # Hộp quà trên ảnh tham chiếu 396 px có tâm xấp xỉ (52, 326).
    fallback_tap=(52, 326),
    navigation_threshold=0.80,
)


def run(bot):
    return run_carousel_exact(bot, GiftScreen.VALUABLE_EVENT,
                              "ValuableEvent/title", "ValuableEvent/ActiveMonthlyCard/tab", FLOW)


TASK = GiftTask(KEY, "Active Monthly Card", run)
