"""Inspect Active Monthly Card without touching its paid button."""
from ...common import GiftTask
from ...screens import GiftScreen
from ..named_flow import ExactFlow, run_carousel_exact

KEY = "gift_active_monthly_card"
FLOW = ExactFlow(
    opened=("ValuableEvent/ActiveMonthlyCard/purchase_marker",),
    navigation=("ValuableEvent/ActiveMonthlyCard/button_reward_chest_median",),
    navigation_first_match=True,
    # User-marked green chest frame on the 396x704 reference screenshot.
    navigation_region=(2, 17, 27, 41),
    # Sixty live frames on emulator 21503 measured 0.7869..0.9816 for the
    # dedicated 40x40 median crop; the highest match outside this frame was
    # only 0.2579.  Keep animation margin without admitting unrelated art.
    navigation_threshold=0.72,
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
)


def run(bot):
    return run_carousel_exact(bot, GiftScreen.VALUABLE_EVENT,
                              "ValuableEvent/title", "ValuableEvent/ActiveMonthlyCard/tab_icon", FLOW)


TASK = GiftTask(KEY, "Active Monthly Card", run)
