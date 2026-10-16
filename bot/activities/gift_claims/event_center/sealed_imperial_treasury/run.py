"""Sealed Imperial Treasury is an explicit safe skip requested by the user."""
from ...screens import GiftScreen
from ..policy import EventPolicy, run_opened_event


POLICY = EventPolicy(
    "Sealed Imperial Treasury",
    key="gift_sealed_imperial_treasury",
    screen=GiftScreen.SEALED_IMPERIAL_TREASURY,
    skip_reason="mở rương/Refresh có thể tiêu tài nguyên; bỏ qua và coi là DONE",
)


def run(bot):
    return run_opened_event(bot, POLICY)
