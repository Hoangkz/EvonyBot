"""Blessing of Pallas uses the safe generic Event Center claim sequence."""
from ..policy import EventPolicy, run_opened_event


POLICY = EventPolicy("Blessing of Pallas", key="gift_blessing_of_pallas")


def run(bot):
    return run_opened_event(bot, POLICY)
