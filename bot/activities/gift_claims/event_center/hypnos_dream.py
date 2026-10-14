"""Hypnos' Dream: open its exact Rewards control before claims."""
from ..screens import GiftScreen
from .policy import EventPolicy


POLICY = EventPolicy(
    "Hypnos' Dream",
    screen=GiftScreen.HYPNOS_DREAM,
    navigation=("Rewards", "HypnosDream/button_rewards"),
)
