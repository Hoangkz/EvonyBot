"""Open Super Value Weekly Card and claim its free reward list."""
from ...common import GiftTask, TEXT_CLAIM_CONTROLS
from ..named_flow import ExactFlow, run_carousel_exact
from ...screens import GiftScreen

KEY = "gift_super_value_weekly_card"
FLOW = ExactFlow(
    navigation=("Common/button_reward_chest",),
    # Continue and Go are unfinished row states, not completion markers.
    claims=TEXT_CLAIM_CONTROLS,
    claim_region=(4, 59, 96, 99),
    absence_done=True,
    fallback_tap=(45, 190),
    navigation_threshold=0.80,
    # Khung danh sách quà màu xanh dùng cùng hình học với Active Monthly Card.
    # Xác nhận cả đầu và cuối bằng hai ảnh dHash không đổi liên tiếp; không đặt
    # giới hạn số lần lướt cục bộ.
    scroll_claims=True,
    scroll_start=(50, 92),
    scroll_end=(50, 65),
    scroll_region=(4, 59, 96, 99),
    confirm_scroll_edges=True,
)


def run(bot):
    return run_carousel_exact(bot, GiftScreen.VALUABLE_EVENT,
                              "ValuableEvent/title",
                              "ValuableEvent/SuperValueWeeklyCard/tab", FLOW)


TASK = GiftTask(KEY, "Super Value Weekly Card", run)
