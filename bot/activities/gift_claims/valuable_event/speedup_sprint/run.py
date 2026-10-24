"""Claim the free Sprint Package in Valuable Event."""
from ...common import GiftTask
from ...screens import GiftScreen
from ..named_flow import ExactFlow, run_carousel_exact

KEY = "gift_speedup_sprint"
FLOW = ExactFlow(
    navigation=("SpeedupSprint/subtab_package",),
    # Chỉ ảnh nút Free đầy đủ mới được phép bấm; không dùng Claim chung hay sparkle.
    claims=("SpeedupSprint/button_free",),
    # Ảnh gói 1,000 gems có cùng dòng Purchase Limit và khung nút vàng: ảnh
    # thật đo được 0.894 với template này, trong khi nút Free thật đạt 0.991.
    claim_threshold=0.95,
    # Không thấy Free chưa đủ kết luận. Chỉ Sold Out là trạng thái DONE của nhiệm vụ này.
    done=("SpeedupSprint/status_sold_out",),
)


def run(bot):
    return run_carousel_exact(
        bot,
        GiftScreen.VALUABLE_EVENT,
        "ValuableEvent/title",
        "SpeedupSprint/tab",
        FLOW,
    )


TASK = GiftTask(KEY, "Speedup Sprint", run)
