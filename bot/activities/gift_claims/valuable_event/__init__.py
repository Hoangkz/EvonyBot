"""Gift claims for the city-side Valuable Event area (outside Event Center)."""
from . import run as _run
from .run import KEYS, SPECS, run_opened


def __getattr__(name):
    """Keep scanner helpers available to existing callers and tests."""
    return getattr(_run, name)


__all__ = ["KEYS", "SPECS", "run_opened"]
