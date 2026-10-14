"""Revelation of Horus is an explicit safe skip requested by the user."""
from ..screens import GiftScreen
from .policy import EventPolicy


POLICY = EventPolicy(
    "Revelation of Horus",
    screen=GiftScreen.REVELATION_OF_HORUS,
    skip_reason="không có quà nhận an toàn; bỏ qua và coi là DONE",
)
