"""
current_focus.py — the focused Android window.
"""


def current_focus(bot) -> str:
    """The `mCurrentFocus` line of `dumpsys window`, lower-cased."""
    output = bot.shell("dumpsys window")
    return "\n".join(line for line in output.splitlines() if "mCurrentFocus" in line).lower()
