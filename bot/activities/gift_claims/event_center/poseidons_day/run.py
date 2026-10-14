"""Poseidon's Day uses the safe generic Event Center claim sequence."""
from ..policy import EventPolicy, run_opened_event


POLICY = EventPolicy("Poseidon's Day")


def run(bot):
    return run_opened_event(bot, POLICY)
