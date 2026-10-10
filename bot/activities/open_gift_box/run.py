"""
run.py — "Open Gift Box" activity (port of C# OpenAllGiftBox).

Goes to Items ("..." -> Items), and on the gift box list opens every box whose image
is in one of the selected folders (Resource / Gems / Gold /
Etc), reading the 4-column grid row by row, left to right, scrolling down until a
"done" image shows up. That pass is repeated once more from the top (tap Common): when
the second pass also ends at "done", every box is opened and the task is marked done
for today. Each loop takes one screenshot, finds the first
known image on it (checked in list order) and acts on it.
"""
import math

from ...common import click_images, delay, exit_images, find_first, go_home, images_in
from .constants import (ALL_BOXES, BACK, BOX_FOLDERS, BOX_LIST, BOX_BOTTOM, BOX_THRESHOLD, BUTTON_EXTRA_WAITS, CONFIRM, DONE, FRAGMENT, FRAGMENT_NEAR, ITEMS, KEY,
                        FRAGMENT_PREFIX, LIST_SWIPE, ROW_TOLERANCE, SETUP, TAB_HALF_HEIGHT, TAB_REGIONS, TAP)


def run(bot, settings: dict):
    """`bot` is the device's BotContext; `settings` is the "Open Gift Box" tab's config."""
    boxes = _box_images(settings.get("selection_gift_box", {}))
    if not boxes:
        return
    targets = _targets()
    thresholds = dict.fromkeys((path for path, _ in targets), BOX_THRESHOLD)
    done_images = images_in(DONE)
    at_top = False          # list sent back to the top (Common tab tapped) since reaching it
    passes_done = 0         # lists scanned down to "done"; the 2nd one (from the top) finishes

    while True:
        screen = bot.screenshot()
        action, pos = find_first(bot, screen, targets, regions=TAB_REGIONS, thresholds=thresholds)

        if action == CONFIRM:
            bot.tap(*pos)
            delay(bot, 2)
        elif action == BOX_LIST and not at_top:
            bot.tap(*pos)           # Common tab (selected or not): the list jumps back to the top
            delay(bot, 2)
            at_top = True
        elif action == BOX_LIST:
            if _open_next_box(bot, screen, boxes, done_images, pos):
                passes_done += 1
                if passes_done == 2:
                    bot.mark_daily_done(KEY)
                    return
                bot.tap(*pos)       # Common tab: the list jumps back to the top
                delay(bot, 2)
        elif action == TAP:
            bot.tap(*pos)
            delay(bot, 2)
        elif action == BACK:
            bot.back()
            delay(bot, 2)
        else:
            go_home(bot, screen)
            delay(bot, 2)


def _box_images(selection: dict) -> list[str]:
    """Images of every selected box type."""
    if selection.get(ALL_BOXES):
        folders = list(BOX_FOLDERS.values())
    else:
        folders = [folder for label, folder in BOX_FOLDERS.items() if selection.get(label)]
    return [path for folder in folders for path in images_in(folder)]


OPEN_BUTTONS = [f"{SETUP}/Open.png", f"{SETUP}/Use.png"]


def _targets() -> list[tuple[str, str]]:
    return [
        (f"{SETUP}/success.png", BACK),
        (f"{SETUP}/Confirm.png", CONFIRM),
        (f"{SETUP}/Use2.png", TAP),               # quantity popup (already on max): Use; before Open, which
                                                    # shows through the dimmed list under the popup
        (f"{SETUP}/Open.png", TAP),
        (f"{SETUP}/Use.png", TAP),
        (f"{ITEMS}/CommonTab.png", BOX_LIST),     # Items list, first tab (Common) selected
        (f"{ITEMS}/CommonIcon.png", BOX_LIST),    # Items list, another tab selected: Common shows as an icon
        (f"{SETUP}/Common.png", BOX_LIST),
        (f"{SETUP}/2Common.png", BOX_LIST),
        *[(path, BACK) for path in exit_images()],
        *[(path, TAP) for path in click_images()],
        (f"{SETUP}/Items.png", TAP),
        (f"{SETUP}/chucnang.png", TAP),
    ]


def _any_found(bot, screen, images, threshold) -> bool:
    return any(bot.find(path, threshold=threshold, screen=screen) is not None for path in images)


def _open_next_box(bot, screen, boxes: list[str], done_images: list[str], tab_pos) -> bool:
    """Gift box list: tap the next wanted box, or scroll down if none is visible.
    Returns True once a "done" image shows (end of the list)."""
    pos = _tap_box(bot, screen, boxes, tab_pos)
    if pos is not None:
        # The Open / Use button shows up about 1s after the tap; if it still is not there after
        # BUTTON_EXTRA_WAITS more seconds the tap did not register: tap the box again.
        for _ in range(1 + BUTTON_EXTRA_WAITS):
            delay(bot, 1)
            if _any_found(bot, bot.screenshot(), OPEN_BUTTONS, BOX_THRESHOLD):
                return False
        bot.tap(*pos)
        return False
    if _seen_done(bot, screen, done_images):
        return True
    bot.swipe_percent(*LIST_SWIPE, duration=1.0)
    delay(bot, 2)
    return False


def _seen_done(bot, screen, done_images: list[str]) -> bool:
    """Whether a "done" image is on screen. Those named FRAGMENT_PREFIX* only count with the hero
    fragment's puzzle piece right next to them."""
    for path in done_images:
        pos = bot.find(path, threshold=BOX_THRESHOLD, screen=screen, center=False)
        if pos is None:
            continue
        if not path.rsplit("/", 1)[-1].startswith(FRAGMENT_PREFIX):
            return True
        limit = screen.shape[0] * FRAGMENT_NEAR / 100
        pieces = bot.find_all(FRAGMENT, threshold=BOX_THRESHOLD, screen=screen, center=False)
        if any(math.hypot(x - pos[0], y - pos[1]) <= limit for x, y in pieces):
            return True
    return False


def _tap_box(bot, screen, boxes: list[str], tab_pos) -> bool:
    """Tap the first wanted box in reading order (top row first, then left to
    right) among those between the Common tab (`tab_pos`, its centre) and
    BOX_BOTTOM. Returns the tapped position, or None if there was no box."""
    top_pct = tab_pos[1] / screen.shape[0] * 100 + TAB_HALF_HEIGHT
    region = (0, top_pct, 100, BOX_BOTTOM)
    hits = []       # (centre x, centre y)
    for path in boxes:
        w, h = bot.template_size(path)
        for x, y in bot.find_all(path, threshold=BOX_THRESHOLD, screen=screen, center=False, region=region):
            hits.append((x + w // 2, y + h // 2))
    if not hits:
        return None
    tolerance = screen.shape[0] * ROW_TOLERANCE / 100
    top = min(cy for _, cy in hits)
    x, y = min((h for h in hits if h[1] - top < tolerance), key=lambda h: h[0])
    bot.tap(x, y)
    return x, y
