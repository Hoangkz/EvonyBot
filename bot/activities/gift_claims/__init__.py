"""Low-priority gift claims performed after Daily Activities is complete."""
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
from .common import return_home
from .screens import GiftScreen

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


def run(bot):
    """Run every due claim independently and remember each result for today."""
    task_keys = {task.key for task in TASKS}
    group_keys = (valuable_event.KEYS | super_value_return.KEYS) & task_keys
    due_valuable = {key for key in valuable_event.KEYS & task_keys
                    if not bot.is_daily_done(key)}
    due_super_value = {key for key in super_value_return.KEYS & task_keys
                       if not bot.is_daily_done(key)}
    group_results = {key: "no_dot" for key in due_valuable | due_super_value}

    # Lobby icons are intentionally unnamed and may change artwork. Open each
    # fixed slot, identify the fixed inner title, then dispatch that flow.
    opened_groups = set()
    # Finish every red dot in boundary 1 before moving to the potentially
    # longer right-hand boundary 2. Artwork and icon positions are irrelevant;
    # the opened fixed inner title decides which parent flow handles it.
    for boundary in lobby.BOUNDARIES:
        attempted = []
        for _ in range(lobby.MAX_OPENS_PER_BOUNDARY):
            screen_name = lobby.open_next(bot, boundary, attempted)
            if screen_name is None:
                break
            if (screen_name == GiftScreen.VALUABLE_EVENT
                    and due_valuable
                    and screen_name not in opened_groups):
                group_results.update(valuable_event.run_opened(bot, due_valuable))
                opened_groups.add(screen_name)
            elif (screen_name == GiftScreen.SUPER_VALUE_RETURN
                    and due_super_value
                    and screen_name not in opened_groups):
                group_results.update(super_value_return.run_opened(bot, due_super_value))
                opened_groups.add(screen_name)
            elif (screen_name == GiftScreen.EVENT_CENTER
                  and not bot.is_daily_done(event_center.KEY)):
                processed = event_center.run_opened(bot)
                bot.mark_daily_done(event_center.KEY)
                bot.record("Gift Claims: Event Center Limited - "
                           + ("đã xử lý" if processed else "không có quà"))
            else:
                return_home(bot)

    for task in TASKS:
        if bot.is_daily_done(task.key):
            continue
        if task.key in group_keys:
            bot.mark_daily_done(task.key)
            state = group_results.get(task.key, "no_dot")
            result = {
                "cleared": "đã xử lý và hết dấu đỏ",
                "remaining": "đã mở nhưng dấu đỏ vẫn còn",
                "claimed_remaining": "đã nhận, nhưng dấu đỏ vẫn còn",
                "processed": "đã kiểm tra/nhận quà ngày",
                "no_dot": "không có dấu đỏ",
            }[state]
            bot.record(f"Gift Claims: {task.label} - {result}")
            continue
        bot.check()
        bot.record(f"Gift Claims: bắt đầu {task.label}")
        claimed = task.run(bot)
        # A complete scan with no available/red-dot event is still today's result.
        bot.mark_daily_done(task.key)
        result = "đã xử lý" if claimed else "không có quà"
        bot.record(f"Gift Claims: {task.label} - {result}")


__all__ = ["TASKS", "run"]
