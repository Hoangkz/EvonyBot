"""
activities — one module per activity, each exposing `run(bot, settings)`,
where `bot` is the device's BotContext (tap / swipe / screenshot / find...).
Pressing Stop makes any BotContext call raise, which ends the activity.

ACTIVITIES maps the activity's display name (same as its tab title and
its Select Activity button) to that function. Worker chạy theo từng nhiệm vụ
(bot/worker/priority.py), không theo activity; ACTIVITIES chỉ còn Join Monster War và các activity chỉ có một nhiệm vụ (Daily
Activities và Event không có hàm run của cả activity).
"""
from . import alliance_capacity
from . import black_market
from . import craft
from . import find_boss
from . import gather_resources
from . import join_monster_war
from . import open_gift_box
from . import recruit_general
from .constants import EXCLUSIVE_ACTIVITIES

ACTIVITIES = {
    "Join Monster War": join_monster_war.run,
    "Alliance Capacity": alliance_capacity.run,
    "Open Gift Box": open_gift_box.run,
    "Black Market": black_market.run,
    "Recruit General": recruit_general.run,
    "Find Boss": find_boss.run,
    "Craft": craft.run,
    "Gather Resources": gather_resources.run,
}
