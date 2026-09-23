"""
activities — one module per activity, each exposing `run(bot, settings)`,
where `bot` is the device's BotContext (tap / swipe / screenshot / find...).
Pressing Stop makes any BotContext call raise, which ends the activity.

ACTIVITIES maps the activity's display name (same as its tab title and
its Select Activity button) to that function.
"""
from . import alliance_capacity
from . import battlefield_shop
from . import black_market
from . import daily_activities
from . import event
from . import join_monster_war
from . import open_gift_box

ACTIVITIES = {
    "Join Monster War": join_monster_war.run,
    "Alliance Capacity": alliance_capacity.run,
    "Daily Activities": daily_activities.run,
    "Open Gift Box": open_gift_box.run,
    "Black Market": black_market.run,
    "Event": event.run,
    "Battlefield Shop": battlefield_shop.run,
}
