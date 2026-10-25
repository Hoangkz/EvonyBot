"""Inspect Active Monthly Card without touching its paid button."""
from ...common import GiftTask
from ...screens import GiftScreen
from ..named_flow import ExactFlow, run_carousel_exact

KEY = "gift_active_monthly_card"
FLOW = ExactFlow(
    opened=("ActiveMonthlyCard/purchase_marker",),
    navigation=("Common/button_reward_chest",),
    claims=("ActiveMonthlyCard/button_claim",),
    claim_region=(4, 59, 96, 99),
    absence_done=True,
    scroll_claims=True,
    # Khung nhiệm vụ màu xanh trên ảnh 396x704 nằm x=15..379,
    # y=420..691. Giữ cả cú lướt và phép so ảnh bên trong khung này.
    scroll_start=(50, 92),
    scroll_end=(50, 65),
    scroll_region=(4, 59, 96, 99),
    max_scroll_pages=12,
    # Hộp quà trên ảnh tham chiếu 396 px có tâm xấp xỉ (52, 326).
    fallback_tap=(52, 326),
    navigation_threshold=0.80,
)


def run(bot):
    return run_carousel_exact(bot, GiftScreen.VALUABLE_EVENT,
                              "ValuableEvent/title", "ActiveMonthlyCard/tab", FLOW)


TASK = GiftTask(KEY, "Active Monthly Card", run)
