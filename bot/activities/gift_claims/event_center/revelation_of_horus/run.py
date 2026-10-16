"""Revelation of Horus is an explicit safe skip requested by the user."""
from ...screens import GiftScreen
from ..policy import EventPolicy, run_opened_event


POLICY = EventPolicy(
    "Revelation of Horus",
    key="gift_revelation_of_horus",
    screen=GiftScreen.REVELATION_OF_HORUS,
    skip_reason="không có quà nhận an toàn; bỏ qua và coi là DONE",
)


def run(bot):
    return run_opened_event(bot, POLICY)
