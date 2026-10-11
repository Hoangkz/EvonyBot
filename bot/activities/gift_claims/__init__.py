"""Low-priority gift claims performed after Daily Activities is complete.

Chỉ có việc làm trong game (TASKS và các luồng con). Việc nào đến hạn, đã nhận hôm nay chưa, ghi kết quả: worker lo
(bot/worker/gifts.py).
"""
from . import (
    city_growth_plan,
    dragon_battle,
    empire_depot,
    event_center,
    grace_of_star_trail,
    limited_offer,
    lobby,
    login_gifts,
    lucky_raffle,
    speedup_sprint,
    successive_purchase_benefits,
    sulis_wishing,
    super_blazon_sale,
    super_value_return,
    super_value_weekly_card,
    valuable_event,
)

TASKS = (
    dragon_battle.TASK,
    grace_of_star_trail.TASK,
    limited_offer.TASK,
    speedup_sprint.TASK,
    super_blazon_sale.TASK,
    sulis_wishing.TASK,
    super_value_weekly_card.TASK,
    successive_purchase_benefits.TASK,
    empire_depot.TASK,
    lucky_raffle.TASK,
    city_growth_plan.TASK,
    login_gifts.TASK,
    event_center.TASK,
)


__all__ = ["TASKS"]
