"""Sealed Imperial Treasury is an explicit safe skip requested by the user."""
from ..screens import GiftScreen
from .policy import EventPolicy


POLICY = EventPolicy(
    "Sealed Imperial Treasury",
    screen=GiftScreen.SEALED_IMPERIAL_TREASURY,
    skip_reason="mở rương/Refresh có thể tiêu tài nguyên; bỏ qua và coi là DONE",
)
