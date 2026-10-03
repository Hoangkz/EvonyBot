"""Daily Activities automation ported from ``DailyActivities1234.cs``.

The C# source implements the same screenshot -> first matching template ->
action loop for every daily task. This module keeps that behaviour but uses
one shared state-machine runner. BotContext makes Stop interrupt immediately.
"""
from dataclasses import dataclass
from functools import lru_cache
from typing import Callable

from ...common import click_images, delay, exit_images, find_first, go_home
from .general import buy_all_hammers, buy_stamina

ROOT = "DailyActivites"
USE_ALL = f"{ROOT}/UseAllActivities"
DONE, BACK, TAP, SCROLL, OPEN = "done", "back", "tap", "scroll", "open"
OPEN_MONSTER_FIRST, OPEN_MONSTER_SECOND = "open_monster_first", "open_monster_second"
VERIFY_COLLECTING, OPEN_COLLECTING_HELPER = "verify_collecting", "open_collecting_helper"
ROW_OPENED, ROW_COMPLETE, ROW_MOVED = "opened", "complete", "moved"
ROW_ANCHORS = frozenset({OPEN, OPEN_MONSTER_FIRST, OPEN_MONSTER_SECOND,
                         VERIFY_COLLECTING, OPEN_COLLECTING_HELPER,
                         "claim", "donate", "crystal", "compose"})
REWARDS = "Activity Rewards"   # key trong daily_done cho bước nhận thưởng cuối
GENERAL = "General"
BUY_STAMINA = "General: Buy Stamina"
BUY_HAMMERS = "General: Buy All Hammers"


@dataclass(frozen=True)
class Task:
    label: str
    folder: str
    done: tuple[str, ...]
    actions: tuple[tuple[str, str], ...]
    handler: Callable
    after_open_tap: tuple[float, float] | None = (50, 50)


def run(bot, settings: dict):
    """Run enabled tasks in the exact order used by the C# implementation."""
    enabled = {name for name, value in settings.items()
               if name != GENERAL and isinstance(value, bool) and value}
    selected = [task for task in TASKS if task.label in enabled]
    unsupported = sorted(enabled - {task.label for task in TASKS})
    if unsupported:
        bot.log("Daily Activities not implemented by DailyActivities1234.cs: "
                + ", ".join(unsupported))

    _run_general(bot, settings.get(GENERAL, {}))

    if not selected:
        bot.log("Daily Activities: no implemented daily task selected")
        return

    if all(bot.is_daily_done(task.label) for task in selected) and bot.is_daily_done(REWARDS):
        bot.log("Daily Activities: all done today")
        return

    # DailyActivities1234.DailyActivities made five passes. Completed tasks
    # return immediately when their Finish template is found; a task whose
    # Finish template was seen since the last server reset is skipped.
    monster = next((task for task in selected if task.label == "Monster Killing"), None)
    completed_after_monster = 0
    for _ in range(5):
        monster_retried_this_pass = False
        for task in selected:
            if bot.is_daily_done(task.label):
                continue
            if (task.label == "Monster Killing"
                    and getattr(bot, "_daily_monster_deferred", False)):
                continue
            bot.check()
            bot.log(f"Daily Activities: {task.label}")
            finished = _run_task(bot, task)
            if finished:
                bot.mark_daily_done(task.label)
            if (task.label != "Monster Killing" and finished
                    and getattr(bot, "_daily_monster_deferred", False)):
                completed_after_monster += 1
                if completed_after_monster >= 5 and monster is not None:
                    bot.check()
                    bot.log("Daily Activities: returning to Monster Killing after 5 tasks")
                    if _run_task(bot, monster):
                        bot.mark_daily_done(monster.label)
                    completed_after_monster = 0
                    monster_retried_this_pass = True

        if (monster is not None and not bot.is_daily_done(monster.label)
                and getattr(bot, "_daily_monster_deferred", False)
                and not monster_retried_this_pass
                and (completed_after_monster >= 4
                     or all(t.label == "Monster Killing" or bot.is_daily_done(t.label)
                            for t in selected))):
            bot.check()
            bot.log("Daily Activities: returning to Monster Killing after 4 tasks")
            if _run_task(bot, monster):
                bot.mark_daily_done(monster.label)
            completed_after_monster = 0
    if not bot.is_daily_done(REWARDS):
        _collect_activity_rewards(bot)
        # Chỉ coi là nhận xong khi mọi task đã xong, để lần chạy sau trong ngày còn nhận tiếp.
        if all(bot.is_daily_done(task.label) for task in selected):
            bot.mark_daily_done(REWARDS)


def _run_general(bot, settings):
    if not isinstance(settings, dict):
        return
    if settings.get("buy_stamina") and not bot.is_daily_done(BUY_STAMINA):
        quantity = int(settings.get("stamina_quantity", 10))
        bot.log(f"Daily General: Buy Stamina x{quantity}")
        if buy_stamina(bot, quantity):
            bot.mark_daily_done(BUY_STAMINA)
    if settings.get("buy_all_hammers") and not bot.is_daily_done(BUY_HAMMERS):
        bot.log("Daily General: Buy All Hammers")
        if buy_all_hammers(bot):
            bot.mark_daily_done(BUY_HAMMERS)


def _run_task(bot, task: Task) -> bool:
    """True khi thấy ảnh Finish của task (đã hoàn thành trong ngày)."""
    targets = _targets(task)
    last_scroll_pos = None
    scroll_stalls = 0
    while True:
        screen = bot.screenshot()
        # OPEN needs the template's top-left Y, matching the C# FindOutPoint
        # contract. The row crop and fallback Go coordinate are relative to it.
        active_targets = (_monster_targets(targets, bot)
                          if task.label == "Monster Killing" else targets)
        action, pos = find_first(bot, screen, active_targets, top_left=ROW_ANCHORS,
                                 position_cache=_image_positions(bot), fallback_full=True)
        if action == DONE:
            return True
        if action == BACK:
            bot.back(delay=1)
        elif action == TAP:
            delay(bot, 2)
            bot.tap(*pos, delay=2)
        elif action == SCROLL:
            if (last_scroll_pos is not None and pos is not None
                    and abs(pos[0] - last_scroll_pos[0]) <= 3
                    and abs(pos[1] - last_scroll_pos[1]) <= 3):
                scroll_stalls += 1
            else:
                scroll_stalls = 0
            last_scroll_pos = pos
            if scroll_stalls >= 2:
                bot.log("Daily Activities: end of list reached; returning to top")
                _scroll_to_top(bot)
                last_scroll_pos = None
                scroll_stalls = 0
            else:
                _scroll_up(bot)
        elif action == OPEN:
            row_state = _open_task_row(bot, screen, pos, task.after_open_tap,
                                       task.folder)
            if row_state == ROW_COMPLETE:
                return True
        elif action in (OPEN_MONSTER_FIRST, OPEN_MONSTER_SECOND):
            if action == OPEN_MONSTER_SECOND:
                # Supports resuming after the first 2-kill task was already
                # claimed in an earlier run.
                bot._daily_monster_marches = max(
                    2, getattr(bot, "_daily_monster_marches", 0))
                bot._daily_monster_first_claimed = True
                bot._daily_monster_deferred = False
            row_state = _open_task_row(bot, screen, pos, None, task.folder)
            if row_state == ROW_COMPLETE:
                if action == OPEN_MONSTER_FIRST:
                    _claim_task_row(bot, screen, pos)
                    bot._daily_monster_marches = 2
                    bot._daily_monster_first_claimed = True
                    bot._daily_monster_deferred = True
                    bot.log("Daily Activities: Monster Killing deferred after 2 attacks")
                    delay(bot, 2)
                    return False
                return True
        elif action == VERIFY_COLLECTING:
            # ClaimCollecting is the real Resource Collecting task. The
            # Research technologies row is only a shortcut to Collection.
            row_state = _open_task_row(bot, screen, pos, None, task.folder,
                                       open_when_available=False)
            if row_state == ROW_COMPLETE:
                return True
            if row_state == ROW_OPENED:
                bot.log("Daily Activities: Resource Collecting still has Go")
                _scroll_to_top(bot)
        elif action == OPEN_COLLECTING_HELPER:
            # Indirect Research technologies row: use its Go button only to
            # reach Academy/Collection; never use this row as completion proof.
            row_state = _open_task_row(bot, screen, pos, task.after_open_tap,
                                       task.folder)
            if row_state == ROW_COMPLETE:
                _scroll_up(bot, 2)
        elif action is None:
            # A task's Go button often spends a few seconds transitioning to
            # the world/search screen. Pressing Android Back during that gap
            # opens Evony's Quit dialog and hides every Daily control.
            delay(bot, 1)
        elif task.handler(bot, action, pos, screen):
            return False


@lru_cache(maxsize=None)
def _targets(task: Task) -> tuple[tuple[str, str], ...]:
    folder = f"{ROOT}/{task.folder}"
    result = [(f"{folder}/{name}", DONE) for name in task.done]
    result.extend((f"{folder}/{name}", action) for name, action in task.actions)
    # Initial Daily start can begin on either city/world layout. These are the
    # actual Quests/Daily buttons (including the exact crop supplied by the
    # user); without them the generic recovery path runs before a task has
    # opened the Activity list.
    result.extend((f"{USE_ALL}/{name}", TAP) for name in (
        "QuestButtonDaily.png", "QuestButtonCurrent.png", "QuestButtonCity.png"))
    result.extend((path, BACK) for path in exit_images())
    result.extend((path, TAP) for path in click_images())
    # On the selected Activity tab, Click_Activities1 (the word "Activity")
    # and Click_ActivitiesLight (a task reward star) are both visible. Check
    # the star first so the list advances instead of tapping the selected tab
    # forever. Task labels stay ahead of this entry and therefore still open
    # immediately when their row is visible.
    result.append((f"{folder}/Click_ActivitiesLight.png", SCROLL))
    # Claim All belongs to the final reward phase. Tapping it while checking an
    # individual task can remove that completed row before its no-Go state is
    # observed, leaving the task runner unable to prove completion.
    for name in ("Click_Activities.png", "Click_Activities1.png", "Click_Activities2.png"):
        result.append((f"{folder}/{name}", TAP))
    result.append((f"{folder}/CheckAgain.png", BACK))
    return tuple(result)


def _image_positions(bot) -> dict[str, tuple[int, int]]:
    """Per-worker image positions used by adaptive region matching."""
    cache = getattr(bot, "_daily_image_positions", None)
    if cache is None:
        cache = {}
        bot._daily_image_positions = cache
    return cache


def _monster_targets(targets, bot):
    """Hide the first monster row after its 2-kill reward was processed."""
    if not getattr(bot, "_daily_monster_first_claimed", False):
        return targets
    first = f"{ROOT}/ActivitiesAttackMonster/ActivitiesAttackMonster.png"
    return tuple((path, action) for path, action in targets if path != first)


def _open_task_row(bot, screen, pos, after_open_tap=(50, 50), task_folder=None,
                   open_when_available: bool = True) -> str:
    """Open a task row, or confirm completion when its ``Go`` is gone.

    A completed task keeps its label but replaces ``Go`` with ``Claim``. The
    old coordinate fallback therefore clicked Claim and re-ran finished work.
    The label is our row anchor; once the complete row is visible, absence of
    Go is the server/UI completion signal.
    """
    _, y = pos
    if y > 500:
        bot.swipe_percent(70, 70, 65, 65, duration=1.0, delay=2)
        return ROW_MOVED
    _, width = screen.shape[:2]
    # `pos` is the top-left of the task label (as in the C# implementation),
    # so the whole 100 px row — including the tiny 20x15 Go image — is kept.
    row_y = max(0, y)
    row = bot.crop(screen, 0, row_y, width, 100)
    go_templates = []
    if task_folder:
        go_templates.append(f"{ROOT}/{task_folder}/Go.png")
    go_templates.append(f"{USE_ALL}/Go.png")
    go = next((match for path in go_templates
               if (match := bot.find(path, screen=row)) is not None), None)
    if go is None:
        bot.log("Daily Activities: task row has no Go button; completed")
        return ROW_COMPLETE
    if not open_when_available:
        return ROW_OPENED
    bot.tap(go[0], go[1] + row_y, delay=4)
    if after_open_tap is not None:
        bot.tap_percent(*after_open_tap, delay=1)
    return ROW_OPENED


def _claim_task_row(bot, screen, pos) -> bool:
    """Claim one completed row so Evony can reveal its follow-up task."""
    _, y = pos
    row_y = max(0, y)
    row = bot.crop(screen, 0, row_y, screen.shape[1], 100)
    claim = bot.find(f"{ROOT}/ActivitiesSourceCollecting/Claim.png", screen=row)
    if claim is None:
        return False
    bot.tap(claim[0], claim[1] + row_y, delay=3)
    return True


def _open_daily_activity(bot, attempts: int = 6, close_search: bool = False) -> bool:
    """Open Quests by image, select Activity, and verify the list is ready.

    The bottom-left control moves between the city and world layouts. A fixed
    8%,88% tap can therefore hit Settings. Never guess its coordinate.
    """
    activity_tab = f"{USE_ALL}/Click_Activities1.png"
    activity_marker = f"{USE_ALL}/Click_ActivitiesLight.png"
    quest_buttons = (f"{USE_ALL}/QuestButtonDaily.png",
                     f"{USE_ALL}/QuestButtonCurrent.png",
                     f"{USE_ALL}/QuestButtonCity.png",
                     f"{USE_ALL}/Click_Activities.png")
    search_closed = False
    for _ in range(attempts):
        screen = bot.screenshot()
        if bot.find(activity_marker, screen=screen) is not None:
            return True
        tab = bot.find(activity_tab, screen=screen)
        if tab is not None:
            bot.tap(*tab, delay=2)
            continue
        quest = next((match for path in quest_buttons
                      if (match := bot.find(path, threshold=0.72, screen=screen,
                                            region=(0, 70, 25, 100))) is not None), None)
        if quest is not None:
            bot.tap(*quest, delay=3)
            continue
        if close_search and not search_closed:
            # Current Evony leaves the bottom Search drawer over Quests.
            # Android Back opens the Quit dialog, so return to the city using
            # the verified world-map control instead.
            territory = bot.find(
                f"{ROOT}/ActivitiesAttackMonster/BackToTerritoryCurrent.png",
                threshold=0.72, screen=screen, region=(70, 10, 100, 35))
            if territory is not None:
                bot.tap(*territory, delay=4)
            else:
                delay(bot, 1)
            search_closed = True
            continue
        delay(bot, 1)
    bot.log("Daily Activities: Quests/Activity button was not found")
    return False


def _scroll_up(bot, count: int = 1):
    for _ in range(count):
        bot.swipe_percent(70, 70, 55, 55, duration=1.0, delay=1)


def _scroll_to_top(bot, count: int = 12):
    for _ in range(count):
        bot.swipe_percent(55, 55, 70, 70, duration=0.35, delay=0.15)


def _replace_text(bot, text: str, deletes: int = 8):
    for _ in range(deletes):
        bot.shell("input keyevent KEYCODE_DEL")
    bot.shell(f"input text {text}")
    bot.shell("input keyevent KEYCODE_ENTER")


def _tap_first(bot, templates: tuple[str, ...], attempts: int, after=None,
               missing=None, delay_seconds: float = 2) -> bool:
    """Bounded equivalent of the C# inner template-tapping loops."""
    hits = idle = 0
    while hits < attempts and idle < 8:
        screen = bot.screenshot()
        _, pos = find_first(bot, screen, [(path, "match") for path in templates],
                            position_cache=_image_positions(bot), fallback_full=True)
        if pos is None:
            idle += 1
            if missing:
                missing()
            delay(bot)
            continue
        bot.tap(*pos, delay=delay_seconds)
        hits += 1
        idle = 0
        if after:
            after()
    return hits >= attempts


# ---- task-specific handlers -----------------------------------------
def _collecting(bot, action, pos, screen):
    if action == "collection":
        bot.tap(*pos, delay=4)
        # Collection is the indirect action. Return explicitly and let
        # VERIFY_COLLECTING check the real ClaimCollecting row's Go button.
        _open_daily_activity(bot)
    return False


def _gather_city(bot, action, pos, _screen):
    """Collect all ready city resources using the floating hand shortcut."""
    if action == "hand":
        bot.tap(*pos, delay=3)
        # Go opened the city from the task strip. Re-open and verify Activity
        # by image so a layout change cannot turn this into a Settings tap.
        _open_daily_activity(bot)
    return False


def _offering(bot, action, pos, screen):
    if action in ("offer", "offer_gems"):
        bot.tap(*pos, delay=4)
    elif action == "finish_offer":
        plus = bot.find(f"{ROOT}/ActivitiesOffer/Offer+.png", screen=screen)
        if plus is None:
            bot.back(delay=2)
        else:
            bot.tap(*plus, delay=1)
            bot.tap(*plus, delay=1)
            bot.tap(*pos, delay=4)
    return False


def _resource_tax(bot, action, pos, screen):
    if action == "tax":
        bot.tap(*pos, delay=4)
    elif action == "revenue":
        bot.tap(300, 280)
    elif action == "tax_amount":
        bot.tap(200, 300, delay=1)
        _replace_text(bot, "0", 1)
        delay(bot, 2)
        bot.tap(200, 440, delay=4)
        bot.tap(195, 415, delay=4)
        return True
    return False


def _gold_levy(bot, action, pos, screen):
    if action == "levy":
        # The current city UI opens a radial building menu first. Select Levy
        # before using the two legacy button coordinates inside its dialog.
        bot.tap(*pos, delay=3)
        bot.tap(280, 545, delay=3)
        bot.tap(105, 545, delay=3)
    elif action == "levy_one":
        # Levy1 is the dialog artwork in the current build; its old C# tap at
        # (300, 280) only hit the picture. Use the actual Free Levy buttons.
        bot.tap(280, 545, delay=3)
        bot.tap(105, 545, delay=3)
    elif action == "levy_times":
        bot.tap(190, 300)
        _replace_text(bot, "5", 1)
        delay(bot, 2)
        bot.tap(200, 440, delay=4)
        bot.tap(195, 415, delay=2)
    return False


def _troop_train(bot, action, pos, screen):
    if action == "interface":
        bot.swipe_percent(30, 65, 80, 65, duration=0.3, delay=1)
    elif action == "soldier":
        bot.tap(336, 582)
        _replace_text(bot, "500", 3)
        delay(bot, 5)
        bot.tap(300, 660)
    elif action == "speed":
        bot.tap(*pos, delay=4)
        bot.tap(100, 670)
    return False


def _troop_heal(bot, action, pos, screen):
    if action == "heal_all":
        bot.tap(*pos, delay=4)
    elif action == "select":
        bot.tap(*pos, delay=2)
        _replace_text(bot, "150", 1)
        delay(bot, 2)
        bot.tap(330, 670, delay=4)
        bot.tap(330, 670, delay=2)
    elif action == "heal_info":
        bot.tap(*pos, delay=2)
        bot.swipe_percent(65, 70, 65, 60, duration=1.0, delay=1)
        bot.swipe_percent(65, 70, 65, 60, duration=1.0, delay=1)
    return False


def _trap(bot, action, pos, screen):
    if action == "interface":
        # In 5.25 the four trap types are fixed buttons, not a troop carousel.
        # Pick the visible tier-I trap and submit the requested amount directly.
        bot.tap(95, 453, delay=1)
        bot.tap(336, 582)
        _replace_text(bot, "150", 3)
        delay(bot, 2)
        bot.tap(300, 660)
    elif action == "build":
        bot.tap(336, 582)
        _replace_text(bot, "150", 3)
        delay(bot, 2)
        bot.tap(300, 660)
    elif action == "speed":
        bot.tap(*pos, delay=2)
        bot.tap(100, 670, delay=2)
        bot.back(delay=2)
    return False


def _donate(bot, action, pos, screen):
    if action == "donate":
        _, y = pos
        row_y = max(0, y)
        region = bot.crop(screen, 0, row_y, screen.shape[1], 390)
        donate = bot.find(f"{ROOT}/ActivitiesDonateAlliance/Donate.png", screen=region)
        if donate is None:
            return True
        bot.tap(donate[0], donate[1] + row_y, delay=1)
    return False


def _attack_monster(bot, action, pos, screen):
    if action == "tap_monster":
        # Evony 5.25 opens Search on the Summon tab. The old C# code only
        # pressed the bottom button, which is inert until Monster is selected.
        bot.tap(*pos, delay=2)
        bot.tap(200, 670, delay=4)
        refreshed = bot.screenshot()
        # Current builds open a monster-details card with a wide green Attack
        # button. AttackMonster.png is the small sword used by older builds.
        # Handle the current card here so the outer scanner does not mistake
        # the still-visible Search drawer for a failed search and click it again.
        current_attack = bot.find(
            f"{ROOT}/ActivitiesAttackMonster/AttackButtonCurrent.png",
            threshold=0.72, screen=refreshed, region=(20, 55, 80, 82))
        if current_attack is not None:
            bot._daily_monster_search_misses = 0
            bot.tap(*current_attack, delay=3)
            return False

        attack = bot.find(f"{ROOT}/ActivitiesAttackMonster/AttackMonster.png",
                          screen=refreshed)
        if attack is not None:
            bot._daily_monster_search_misses = 0
        else:
            misses = getattr(bot, "_daily_monster_search_misses", 0) + 1
            bot._daily_monster_search_misses = misses
            if misses >= 3:
                bot.log("Daily Activities: Monster search waiting for an available target")
                # Back opens Evony's Quit dialog on the current world-map UI;
                # leave the search drawer in place and retry after marches have
                # had time to return.
                delay(bot, 5)
                bot._daily_monster_search_misses = 0
    elif action == "monster":
        bot.tap(*pos, delay=2)
        bot.tap(200, 500, delay=2)
    elif action == "march":
        if not _dispatch_monster_march(bot, screen):
            # Stop this pass on the March screen. Continuing would make the
            # generic recovery press Back/Settings although no attack happened.
            return True
        marches = getattr(bot, "_daily_monster_marches", 0) + 1
        bot._daily_monster_marches = marches
        bot.log(f"Daily Activities: Monster march {marches}/5 confirmed")
        if marches in (2, 5):
            # Two sequential daily rows: 2 attacks, claim/check, then 3 more.
            if not _open_daily_activity(bot, close_search=True):
                return True
    return False


def _dispatch_monster_march(bot, screen) -> bool:
    """Send one march and return True only after the March page disappears."""
    folder = f"{ROOT}/ActivitiesAttackMonster"
    full_tiers = bot.find(f"{folder}/FullTiersCurrent.png", threshold=0.72,
                          screen=screen, region=(5, 85, 60, 100))
    if full_tiers is not None:
        # Current Evony layout: the green Full Tiers preset fills/sends the
        # march. On some accounts it only fills it, so confirm with March below.
        bot.tap(*full_tiers, delay=3)
    else:
        # Legacy layout retained as a fallback for older emulator/game builds.
        bot.tap(320, 520, delay=3)
        _replace_text(bot, "100", 8)
        delay(bot, 2)
        bot.tap(300, 660, delay=3)

    after = bot.screenshot()
    if bot.find(f"{folder}/March.png", screen=after) is not None:
        # Full Tiers only filled the formation; press the verified bottom-right
        # March control once, then require an actual screen transition.
        march_button = bot.find(f"{folder}/MarchButtonCurrent.png", threshold=0.72,
                                screen=after, region=(50, 85, 100, 100))
        if march_button is not None:
            bot.tap(*march_button, delay=3)
            after = bot.screenshot()

    sent = bot.find(f"{folder}/March.png", screen=after) is None
    if not sent:
        bot.log("Daily Activities: Monster march was not sent; staying on March screen")
    return sent


def _black_market(bot, action, pos, screen):
    if action == "market":
        bot.tap(*pos, delay=2)
    elif action == "buy":
        base = f"{ROOT}/ActivitiesBuyMarket/Buy"
        templates = tuple(f"{base}/{name}" for name in
                          ("food1.png", "lumber1.png", "ore1.png", "stone1.png"))
        def confirm():
            bot.tap(190, 415, delay=4)
        # (190, 575) used to change page in the C# era. In Evony 5.25 it is
        # "Instant Refresh" and costs gems, so never use it as a fallback.
        _tap_first(bot, templates, 3, after=confirm)
        bot.back(delay=2)
        return True
    return False


def _enhance_general(bot, action, pos, screen):
    if action == "cultivate":
        bot.tap(*pos, delay=3)
    elif action == "cultivate_loop":
        base = f"{ROOT}/ActivitiesGeneralEnhancing/TapEnhancing"
        templates = (f"{base}/Agree.png", f"{base}/Disagree.png")
        if _tap_first(bot, templates, 5):
            bot.tap(110, 666)
            bot.back(delay=2)
        return True
    return False


def _wheel(bot, action, pos, screen):
    if action == "spin":
        template = f"{ROOT}/ActivitiesWheelofFortune/SpinOnce.png"
        if _tap_first(bot, (template,), 1):
            bot.tap(170, 550)
            bot.back(delay=2)
        return True
    return False


def _patrol(bot, action, pos, screen):
    if action == "patrol":
        for attempt in range(3):
            if attempt:
                bot.tap(108, 668, delay=3)  # Refresh rewards (gold)
            bot.tap(169, 607, delay=1)      # Select All
            bot.tap(286, 668, delay=3)      # Patrol
        bot.back(delay=2)
        return True
    if action == "patrol_button":
        bot.tap(*pos, delay=2)
    return False


def _compose(bot, action, pos, screen):
    if action == "level_one":
        delay(bot, 4)
        bot.tap(*pos, delay=2)
    elif action == "crystal":
        _, y = pos
        row_y = max(0, y)
        region = bot.crop(screen, 0, row_y, screen.shape[1], 250)
        compose = bot.find(f"{ROOT}/ActivitiesComposeMaterials/Compose1.png", screen=region)
        if compose is not None:
            bot.tap(compose[0], compose[1] + row_y, delay=4)
    elif action == "compose":
        _, y = pos
        row_y = max(0, y)
        region = bot.crop(screen, 0, row_y, screen.shape[1], 666)
        lv3 = bot.find(f"{ROOT}/ActivitiesComposeMaterials/Lv3Crystal.png", screen=region)
        if lv3 is not None:
            bot.tap(lv3[0], lv3[1] + row_y, delay=2)
            for _ in range(3):
                bot.tap(100, 670, delay=2)
            bot.back(delay=2)
        return True
    return False


TASKS = (
    Task("Monster Killing", "ActivitiesAttackMonster",
         (),
         (("March.png", "march"), ("AttackMonster.png", "monster"),
          ("TapMonster.png", "tap_monster"), ("FindMonster.png", TAP),
          ("ActivitiesAttackMonsterNext.png", OPEN_MONSTER_SECOND),
          ("ActivitiesAttackMonster.png", OPEN_MONSTER_FIRST)), _attack_monster, None),
    # Finish1.png is the Academy's "Skill Book Shop" icon on the current
    # client. Treating it as DONE exits before Collection.png is pressed.
    # Completion is verified from the Activity row when its Go button is gone.
    Task("Resource Collecting", "ActivitiesSourceCollecting", (),
         (("Collection.png", "collection"),
          ("ClaimCollecting.png", VERIFY_COLLECTING),
          ("ActivitiesSourceCollecting.png", OPEN_COLLECTING_HELPER)), _collecting),
    Task("Offering", "ActivitiesOffer", ("Offerdone.png", "Offerdone1.png"),
         (("Offerfins.png", "finish_offer"), ("OfferGems.png", "offer_gems"),
          ("Offer1.png", "offer"), ("Offer.png", OPEN), ("Offer2.png", TAP)), _offering),
    # This must follow Offering: both actions return to the city, then the
    # floating hand collects every ready resource field in one tap.
    Task("Resource Gathering", "ActivitiesSourceGathering", (),
         (("HandCurrent.png", "hand"), ("GatherCityCurrent.png", OPEN)), _gather_city, None),
    Task("Resource Tax", "ActivitiesTaxResource",
         ("TaxFinish2.png", "TaxFinish.png", "TaxFinish1.png"),
         (("TapTax1.png", "tax_amount"), ("TaxRevenue.png", "revenue"),
          ("Tax.png", "tax"), ("ActivitiesTaxResource.png", OPEN)), _resource_tax),
    Task("Gold Levy", "ActivitiesLevyGold", ("LevyGoldFinish.png", "LevyGoldFinish1.png"),
         (("GemsLevyTimes.png", "levy_times"), ("Levy1.png", "levy_one"),
          ("Levy.png", "levy"), ("LevyGoldActivityCurrent.png", OPEN),
          ("LevyGoldActivity1.png", OPEN)), _gold_levy),
    Task("Troop Training", "ActivitiesTroopTrain", ("TroopFinish.png", "TroopFinish1.png"),
         (("TroopSpeed.png", "speed"),
          ("TrainSoldierSelectedCurrent.png", "soldier"),
          ("TrainSoldierCurrent.png", "soldier"),
          ("TrainSoldier1.png", "soldier"),
          ("TrainInterface.png", "interface"), ("Train.png", TAP),
          ("TrainTroop.png", OPEN)), _troop_train),
    Task("Troop Heading", "ActivitiesTroopHeal", ("HealFinish1.png", "HealFinish.png"),
         (("HealFinishAll.png", "heal_all"), ("HealSelect.png", "select"),
          ("Heal-i.png", "heal_info"), ("Heal.png", TAP),
          ("HealActivity.png", OPEN)), _troop_heal),
    Task("Trap Buiding", "ActivitiesBuildTrap", ("TrapFinish1.png", "TrapFinish.png"),
         (("TrapSpeed.png", "speed"), ("Trap-i.png", "build"),
          ("BuildInterface.png", "interface"), ("Build.png", TAP),
          ("ActivitiesBuildTrap1.png", OPEN)), _trap),
    Task("Alliance Donation", "ActivitiesDonateAlliance",
         ("AllianceDonateFinish1.png", "AllianceDonateFinish.png"),
         (("AllianceCapacity.png", "donate"),
          ("ActivitiesDonateAlliance1.png", OPEN)), _donate),
    Task("Black Market", "ActivitiesBuyMarket",
         ("BlackMarketFinishCurrent.png", "BlackMarketFinish.png"),
         (("Confirm.png", TAP), ("Market.png", "buy"), ("Market1.png", "buy"),
          ("BuyMarket.png", "market"), ("ActivitiesBlackMarket.png", OPEN)), _black_market),
    Task("General Enhancing", "ActivitiesGeneralEnhancing",
         ("CultivateFinishCurrent.png", "CultivateFinish.png"),
         (("Cultivate1.png", "cultivate_loop"), ("Cultivate.png", "cultivate"),
          ("ActivitiesGeneralEnhancing.png", OPEN)), _enhance_general, (30, 50)),
    Task("Wheel of Fortune", "ActivitiesWheelofFortune",
          ("SpinFinishCurrent.png", "SpinFinish.png"),
          (("WheelofFortune.png", "spin"), ("ActivitiesWheelofFortune.png", OPEN)), _wheel, None),
    Task("Patrol", "ActivitiesPatrol",
         ("PatrolFinishCurrent.png", "PatrolFinish.png"),
         (("Patrol1.png", "patrol"), ("Patrol.png", "patrol_button"),
          ("ActivitiesPatrol.png", OPEN)), _patrol),
    Task("Material Composing", "ActivitiesComposeMaterials",
         ("ComposeMaterialsFinishCurrent.png", "ComposeMaterialsFinish.png"),
         (("Compose.png", "compose"), ("Crystal.png", "crystal"),
          ("Lv1Crystal.png", "level_one"),
          ("ActivitiesComposeMaterials.png", OPEN)), _compose, None),
)


def _collect_activity_rewards(bot):
    folder = f"{ROOT}/CollectionActivities"
    targets = [
        (f"{folder}/Click_ActivitiesLight.png", DONE),
        (f"{folder}/Click_Activities2.png", TAP),
        (f"{folder}/Click_Activities1.png", TAP),
        (f"{folder}/Click_Activities.png", TAP),
        *[(path, BACK) for path in exit_images()],
        *[(path, TAP) for path in click_images()],
    ]
    while True:
        screen = bot.screenshot()
        reward_popup = bot.find(f"{folder}/CongratulationsCurrent.png", screen=screen)
        if reward_popup is not None:
            bot.back(delay=2)
            continue
        # Claim task rows first because their activity points can unlock an
        # additional chest in the same pass.
        claim_all = bot.find(f"{folder}/Claim_All.png", screen=screen)
        if claim_all is not None:
            bot.tap(*claim_all, delay=2)
            continue
        # All claimable chests share the same open/glowing body. Restricting
        # the search to the chest row avoids confusing a claimed chest with a
        # different number and automatically supports the new 145 chest.
        chests = bot.find_all(f"{folder}/OpenChestCurrent.png", threshold=0.72,
                              screen=screen, region=(8, 37, 92, 47))
        if chests:
            # One chest per fresh screenshot: each tap opens a reward popup,
            # so stale coordinates for the remaining chests are not reusable.
            bot.tap(*sorted(chests)[0], delay=2)
            continue
        action, pos = find_first(bot, screen, targets,
                                 position_cache=_image_positions(bot), fallback_full=True)
        if action == DONE:
            return
        if action == BACK:
            bot.back(delay=1)
        elif action == TAP:
            delay(bot, 2)
            bot.tap(*pos, delay=2)
        else:
            go_home(bot, screen)
            delay(bot)
