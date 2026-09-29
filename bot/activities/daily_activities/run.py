"""Daily Activities automation ported from ``DailyActivities1234.cs``.

The C# source implements the same screenshot -> first matching template ->
action loop for every daily task. This module keeps that behaviour but uses
one shared state-machine runner. BotContext makes Stop interrupt immediately.
"""
from dataclasses import dataclass
from typing import Callable

from ...common import click_images, delay, exit_images, find_first, go_home

ROOT = "DailyActivites"
USE_ALL = f"{ROOT}/UseAllActivities"
DONE, BACK, TAP, SCROLL, OPEN = "done", "back", "tap", "scroll", "open"
REWARDS = "Activity Rewards"   # key trong daily_done cho bước nhận thưởng cuối


@dataclass(frozen=True)
class Task:
    label: str
    folder: str
    done: tuple[str, ...]
    actions: tuple[tuple[str, str], ...]
    handler: Callable
    center_after_open: bool = True


def run(bot, settings: dict):
    """Run enabled tasks in the exact order used by the C# implementation."""
    enabled = {name for name, value in settings.items() if value}
    selected = [task for task in TASKS if task.label in enabled]
    unsupported = sorted(enabled - {task.label for task in TASKS})
    if unsupported:
        bot.log("Daily Activities not implemented by DailyActivities1234.cs: "
                + ", ".join(unsupported))

    if all(bot.is_daily_done(task.label) for task in selected) and bot.is_daily_done(REWARDS):
        bot.log("Daily Activities: all done today")
        return

    # DailyActivities1234.DailyActivities made five passes. Completed tasks
    # return immediately when their Finish template is found; a task whose
    # Finish template was seen since the last server reset is skipped.
    for _ in range(5):
        for task in selected:
            if bot.is_daily_done(task.label):
                continue
            bot.check()
            bot.log(f"Daily Activities: {task.label}")
            if _run_task(bot, task):
                bot.mark_daily_done(task.label)
    if not bot.is_daily_done(REWARDS):
        _collect_activity_rewards(bot)
        # Chỉ coi là nhận xong khi mọi task đã xong, để lần chạy sau trong ngày còn nhận tiếp.
        if all(bot.is_daily_done(task.label) for task in selected):
            bot.mark_daily_done(REWARDS)


def _run_task(bot, task: Task) -> bool:
    """True khi thấy ảnh Finish của task (đã hoàn thành trong ngày)."""
    targets = _targets(task)
    while True:
        screen = bot.screenshot()
        action, pos = find_first(bot, screen, targets)
        if action == DONE:
            return True
        if action == BACK:
            bot.back(delay=1)
        elif action == TAP:
            delay(bot, 2)
            bot.tap(*pos, delay=2)
        elif action == SCROLL:
            _scroll_up(bot)
        elif action == OPEN:
            if not _open_task_row(bot, screen, pos, task.center_after_open):
                return False
        elif action is None:
            go_home(bot, screen)
            delay(bot)
        elif task.handler(bot, action, pos, screen):
            return False


def _targets(task: Task) -> list[tuple[str, str]]:
    folder = f"{ROOT}/{task.folder}"
    result = [(f"{folder}/{name}", DONE) for name in task.done]
    result.extend((f"{folder}/{name}", action) for name, action in task.actions)
    result.extend((path, BACK) for path in exit_images())
    result.extend((path, TAP) for path in click_images())
    for name in ("Claim_All.png", "Click_Activities.png", "Click_Activities1.png",
                 "Click_Activities2.png"):
        result.append((f"{folder}/{name}", TAP))
    result.append((f"{folder}/Click_ActivitiesLight.png", SCROLL))
    result.append((f"{folder}/CheckAgain.png", BACK))
    return result


def _open_task_row(bot, screen, pos, tap_center: bool = True) -> bool:
    """Open a Daily Activities row via its Go button."""
    _, y = pos
    if y > 500:
        bot.swipe_percent(70, 70, 65, 65, duration=1.0, delay=2)
        return True
    height, width = screen.shape[:2]
    row_y = max(0, y - 5)
    row = bot.crop(screen, 0, row_y, width, 110)
    go = bot.find(f"{USE_ALL}/Go.png", screen=row)
    if go is not None:
        bot.tap(go[0], go[1] + row_y, delay=4)
        if tap_center:
            bot.tap_percent(50, 50, delay=1)
        return True
    bot.tap(width - 60, y + 48, delay=2)
    bot.back(delay=1)
    return False


def _scroll_up(bot, count: int = 1):
    for _ in range(count):
        bot.swipe_percent(70, 70, 55, 55, duration=1.0, delay=1)


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
        pos = None
        for path in templates:
            pos = bot.find(path, screen=screen)
            if pos is not None:
                break
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
        bot.tap(*pos, delay=2)
    elif action == "claim":
        _, y = pos
        row_y = max(0, y - 5)
        row = bot.crop(screen, 0, row_y, screen.shape[1], 110)
        claim = bot.find(f"{ROOT}/ActivitiesSourceCollecting/Claim.png", screen=row)
        if claim is not None:
            bot.tap(claim[0], claim[1] + row_y, delay=4)
        else:
            _scroll_up(bot, 2)
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
        bot.tap(280, 545, delay=3)
        bot.tap(105, 545, delay=3)
    elif action == "levy_one":
        bot.tap(300, 280)
    elif action == "levy_times":
        bot.tap(190, 300)
        _replace_text(bot, "5", 1)
        delay(bot, 2)
        bot.tap(200, 440, delay=4)
        bot.tap(195, 415, delay=2)
    return False


def _troop_train(bot, action, pos, screen):
    if action == "interface":
        bot.swipe_percent(30, 50, 80, 50, duration=0.3, delay=1)
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
        bot.swipe_percent(30, 50, 80, 50, duration=0.3)
    elif action == "build":
        bot.tap(336, 582)
        _replace_text(bot, "150", 3)
        delay(bot, 2)
        bot.tap(300, 660)
    elif action == "speed":
        bot.tap(*pos, delay=2)
        bot.tap(100, 670, delay=2)
    return False


def _donate(bot, action, pos, screen):
    if action == "donate":
        _, y = pos
        row_y = max(0, y - 5)
        region = bot.crop(screen, 0, row_y, screen.shape[1], 400)
        donate = bot.find(f"{ROOT}/ActivitiesDonateAlliance/Donate.png", screen=region)
        if donate is None:
            return True
        bot.tap(donate[0], donate[1] + row_y, delay=1)
    return False


def _attack_monster(bot, action, pos, screen):
    if action == "tap_monster":
        bot.tap(200, 670, delay=4)
    elif action == "monster":
        bot.tap(*pos, delay=2)
        bot.tap(200, 500, delay=2)
    elif action == "march":
        bot.tap(320, 520, delay=3)
        _replace_text(bot, "100", 8)
        delay(bot, 2)
        bot.tap(300, 660, delay=2)
    elif action == "next":
        bot.swipe_percent(70, 70, 65, 65, duration=1.0, delay=2)
        bot.swipe_percent(70, 70, 65, 65, duration=1.0)
    return False


def _black_market(bot, action, pos, screen):
    if action == "market":
        bot.tap(*pos, delay=2)
    elif action == "buy":
        base = f"{ROOT}/ActivitiesBuyMarket/Buy"
        templates = tuple(f"{base}/{name}" for name in
                          ("food1.png", "lumber1.png", "ore1.png", "stone1.png"))
        def confirm():
            bot.tap(190, 415, delay=4)
        def turn_page():
            bot.tap(190, 575, delay=4)
        _tap_first(bot, templates, 3, after=confirm, missing=turn_page)
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
        return True
    return False


def _wheel(bot, action, pos, screen):
    if action == "spin":
        template = f"{ROOT}/ActivitiesWheelofFortune/SpinOnce.png"
        if _tap_first(bot, (template,), 1):
            bot.tap(170, 550)
        return True
    return False


def _patrol(bot, action, pos, screen):
    if action == "patrol":
        template = f"{ROOT}/ActivitiesPatrol/TapPatrol.png"
        def confirm():
            delay(bot, 3)
            bot.tap(170, 550)
        _tap_first(bot, (template,), 3, after=confirm, delay_seconds=2)
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
        row_y = max(0, y - 5)
        region = bot.crop(screen, 0, row_y, screen.shape[1], 260)
        compose = bot.find(f"{ROOT}/ActivitiesComposeMaterials/Compose1.png", screen=region)
        if compose is not None:
            bot.tap(compose[0], compose[1] + row_y, delay=4)
    elif action == "compose":
        _, y = pos
        row_y = max(0, y - 5)
        region = bot.crop(screen, 0, row_y, screen.shape[1], 670)
        lv3 = bot.find(f"{ROOT}/ActivitiesComposeMaterials/Lv3Crystal.png", screen=region)
        if lv3 is not None:
            bot.tap(lv3[0], lv3[1] + row_y, delay=2)
            for _ in range(3):
                bot.tap(100, 670, delay=2)
        return True
    return False


TASKS = (
    Task("Monster Killing", "ActivitiesAttackMonster",
         ("AttackMonsterFinish.png", "AttackMonsterFinish1.png", "PowerFirst.png"),
         (("ActivitiesAttackMonster.png", OPEN), ("FindMonster.png", TAP),
          ("TapMonster.png", "tap_monster"),
          ("AttackMonster.png", "monster"), ("March.png", "march"),
          ("ActivitiesAttackMonsterNext.png", "next")), _attack_monster, False),
    Task("Resource Collecting", "ActivitiesSourceCollecting", ("Finish.png", "Finish1.png"),
         (("Collection.png", "collection"), ("ActivitiesSourceCollecting.png", OPEN),
          ("ClaimCollecting.png", "claim")), _collecting),
    Task("Offering", "ActivitiesOffer", ("Offerdone.png", "Offerdone1.png"),
         (("Offer.png", OPEN), ("Offer1.png", "offer"), ("OfferGems.png", "offer_gems"),
          ("Offer2.png", TAP), ("Offerfins.png", "finish_offer")), _offering),
    Task("Resource Tax", "ActivitiesTaxResource",
         ("TaxFinish.png", "TaxFinish1.png", "TaxFinish2.png"),
         (("ActivitiesTaxResource.png", OPEN), ("Tax.png", "tax"),
          ("TaxRevenue.png", "revenue"), ("TapTax1.png", "tax_amount")), _resource_tax),
    Task("Gold Levy", "ActivitiesLevyGold", ("LevyGoldFinish.png", "LevyGoldFinish1.png"),
         (("LevyGoldActivity1.png", OPEN), ("Levy.png", "levy"),
          ("Levy1.png", "levy_one"), ("GemsLevyTimes.png", "levy_times")), _gold_levy),
    Task("Troop Training", "ActivitiesTroopTrain", ("TroopFinish.png", "TroopFinish1.png"),
         (("Train.png", TAP), ("TrainTroop.png", OPEN), ("TrainInterface.png", "interface"),
          ("TrainSoldier1.png", "soldier"), ("TroopSpeed.png", "speed")), _troop_train),
    Task("Troop Heading", "ActivitiesTroopHeal", ("HealFinish.png", "HealFinish1.png"),
         (("Heal.png", TAP), ("HealActivity.png", OPEN), ("HealFinishAll.png", "heal_all"),
          ("HealSelect.png", "select"), ("Heal-i.png", "heal_info")), _troop_heal),
    Task("Trap Buiding", "ActivitiesBuildTrap", ("TrapFinish.png", "TrapFinish1.png"),
         (("ActivitiesBuildTrap1.png", OPEN), ("BuildInterface.png", "interface"),
          ("Build.png", TAP), ("Trap-i.png", "build"),
          ("TrapSpeed.png", "speed")), _trap),
    Task("Alliance Donation", "ActivitiesDonateAlliance",
         ("AllianceDonateFinish.png", "AllianceDonateFinish1.png", "AllianceDonateFinish2.png"),
         (("ActivitiesDonateAlliance1.png", OPEN),
          ("AllianceCapacity.png", "donate")), _donate),
    Task("Black Market", "ActivitiesBuyMarket", ("BlackMarketFinish.png",),
         (("ActivitiesBlackMarket.png", OPEN), ("Market.png", "buy"),
          ("Market1.png", "buy"), ("BuyMarket.png", "market"),
          ("Confirm.png", TAP)), _black_market),
    Task("General Enhancing", "ActivitiesGeneralEnhancing", ("CultivateFinish.png",),
         (("ActivitiesGeneralEnhancing.png", OPEN), ("Cultivate.png", "cultivate"),
          ("Cultivate1.png", "cultivate_loop")), _enhance_general, False),
    Task("Wheel of Fortune", "ActivitiesWheelofFortune", ("SpinFinish.png",),
         (("ActivitiesWheelofFortune.png", OPEN), ("WheelofFortune.png", "spin")), _wheel, False),
    Task("Patrol", "ActivitiesPatrol", ("PatrolFinish.png",),
         (("ActivitiesPatrol.png", OPEN), ("Patrol1.png", "patrol"),
          ("Patrol.png", "patrol_button")), _patrol),
    Task("Material Composing", "ActivitiesComposeMaterials", ("ComposeMaterialsFinish.png",),
         (("ActivitiesComposeMaterials.png", OPEN), ("Lv1Crystal.png", "level_one"),
          ("Crystal.png", "crystal"), ("Compose.png", "compose")), _compose, False),
)


def _collect_activity_rewards(bot):
    folder = f"{ROOT}/CollectionActivities"
    targets = [
        (f"{folder}/Finish.png", DONE),
        (f"{folder}/80.png", "claim_and_done"),
        (f"{folder}/20.png", TAP), (f"{folder}/50.png", TAP),
        (f"{folder}/110.png", TAP), (f"{folder}/Claim_All.png", TAP),
        (f"{folder}/Click_Activities2.png", TAP),
        (f"{folder}/Click_Activities1.png", TAP),
        (f"{folder}/Click_Activities.png", TAP),
        *[(path, BACK) for path in exit_images()],
        *[(path, TAP) for path in click_images()],
    ]
    while True:
        screen = bot.screenshot()
        action, pos = find_first(bot, screen, targets)
        if action == DONE:
            return
        if action == BACK:
            bot.back(delay=1)
        elif action == TAP:
            delay(bot, 2)
            bot.tap(*pos, delay=2)
        elif action == "claim_and_done":
            bot.tap(*pos, delay=2)
            return
        else:
            go_home(bot, screen)
            delay(bot)
