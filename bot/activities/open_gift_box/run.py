"""
run.py — "Open Gift Box" activity (port of C# OpenAllGiftBox).

Goes to Items, and on the gift box list opens every box whose image is in
one of the selected folders (Alliance / Boss / Resource / Gems / Gold /
Etc), scrolling down until the end-of-list image shows up. Each loop takes
one screenshot, finds the first known image on it (checked in list order)
and acts on it.
"""
from pathlib import Path

from ...common import click_images, delay, exit_images, find_first, go_home, images_in
from .constants import (ALL_BOXES, BACK, BOX_FOLDERS, BOX_LIST, BOX_THRESHOLD, CONFIRM, MAX,
                        MAX_BOX_Y, SETUP, TAP, USE)


def run(bot, settings: dict):
    """`bot` is the device's BotContext; `settings` is the "Open Gift Box" tab's config."""
    boxes = _box_images(settings.get("selection_gift_box", {}))
    if not boxes:
        return
    targets = _targets()
    end_of_list = images_in("OpenBox/CheckOpen")
    used = False    # C# checkUsed

    while True:
        screen = bot.screenshot()
        action, pos = find_first(bot, screen, targets)

        if action == CONFIRM:
            bot.tap(*pos)
            delay(bot, 2)
        elif action == BOX_LIST:
            used = False
            if _open_next_box(bot, screen, boxes, end_of_list):
                return
        elif action == MAX:
            _use_max(bot, screen, pos, used)
        elif action in (TAP, USE):
            used = action == USE
            bot.tap(*pos)
            delay(bot, 2)
        elif action == BACK:
            used = False
            bot.back()
            delay(bot, 2)
        else:
            go_home(bot, screen)
            delay(bot, 2)


def _box_images(selection: dict) -> list[str]:
    """Images of every selected box type, ordered by their numeric file name."""
    if selection.get(ALL_BOXES):
        folders = list(BOX_FOLDERS.values())
    else:
        folders = [folder for label, folder in BOX_FOLDERS.items() if selection.get(label)]
    images = [path for folder in folders for path in images_in(folder)]
    return sorted(images, key=lambda path: int(Path(path).stem))


def _targets() -> list[tuple[str, str]]:
    return [
        (f"{SETUP}/success.png", BACK),
        (f"{SETUP}/Max.png", MAX),
        (f"{SETUP}/Confirm.png", CONFIRM),
        (f"{SETUP}/Open.png", TAP),
        (f"{SETUP}/Use.png", USE),
        (f"{SETUP}/Common.png", BOX_LIST),
        (f"{SETUP}/2Common.png", BOX_LIST),
        *[(path, BACK) for path in exit_images()],
        *[(path, TAP) for path in click_images()],
        (f"{SETUP}/Items.png", TAP),
        (f"{SETUP}/chucnang.png", TAP),
    ]


def _any_found(bot, screen, images, threshold) -> bool:
    return any(bot.find(path, threshold=threshold, screen=screen) is not None for path in images)


def _open_next_box(bot, screen, boxes: list[str], end_of_list: list[str]) -> bool:
    """Gift box list: tap the next wanted box, or scroll down if none is
    visible. Returns True once the end of the list is reached."""
    if not _tap_box(bot, screen, boxes):
        if _any_found(bot, screen, end_of_list, BOX_THRESHOLD):
            return True
        bot.swipe_percent(50, 50, 50, 36, duration=1.0)
    delay(bot, 2)
    return False


def _tap_box(bot, screen, boxes: list[str]) -> bool:
    """Tap the first wanted box visible above the bottom bar. Boxes not on
    screen at all are moved to the end of `boxes` so the next pass checks
    the others first. Returns whether a box was tapped."""
    missing = []
    tapped = False
    for path in boxes:
        hits = sorted(bot.find_all(path, threshold=BOX_THRESHOLD, screen=screen, center=False),
                      key=lambda p: p[1])
        if not hits:
            missing.append(path)
            continue
        x, y = hits[0]
        if y < MAX_BOX_Y:
            w, h = bot.template_size(path)
            bot.tap(x + w // 2, y + h // 2)
            tapped = True
            break
    if missing:
        boxes[:] = [b for b in boxes if b not in missing] + missing
    return tapped


def _use_max(bot, screen, max_pos, used: bool):
    """Quantity dialog: tap Max, then Use; unless the box was opened via
    "Use", wait (5 screenshots) for the success popup and close it."""
    bot.tap(*max_pos)
    use_pos = bot.find(f"{SETUP}/Use2.png", screen=screen)
    if use_pos is None:
        return
    bot.tap(*use_pos)
    if used:
        delay(bot, 2)
        return
    for _ in range(5):
        if bot.find(f"{SETUP}/success.png") is not None:
            bot.back()
            delay(bot, 2)
            return
