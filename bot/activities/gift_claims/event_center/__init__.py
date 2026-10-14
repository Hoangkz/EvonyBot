"""Gift claims that are opened from the city's Event Center."""
from . import run as _run
from .run import KEY, TASK, run, run_opened


def __getattr__(name):
    """Keep scanner helpers available to existing callers and tests."""
    return getattr(_run, name)


__all__ = ["KEY", "TASK", "run", "run_opened"]
