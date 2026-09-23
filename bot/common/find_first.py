"""
find_first.py — the first known image on a screenshot.
"""


def find_first(bot, screen, targets, top_left=()):
    """First (action, pos) in `targets` — a list of (image path, action)
    checked in order — whose image is on `screen`, else (None, None).
    `pos` is the image's center, or its top-left corner for the actions in
    `top_left` (those tap at an offset from that corner)."""
    for path, action in targets:
        pos = bot.find(path, screen=screen, center=action not in top_left)
        if pos is not None:
            return action, pos
    return None, None
