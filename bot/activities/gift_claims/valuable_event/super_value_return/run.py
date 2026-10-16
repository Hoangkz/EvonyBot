"""Process known red-dot tabs on the fixed Super Value Return screen."""
from dataclasses import dataclass

import cv2
import numpy as np

from .. import city_growth_plan, empire_depot, login_gifts, lucky_raffle
from ...common import (ClaimReport, TEXT_CLAIM_CONTROLS, back_if_close_x,
                     claim_fixed_controls, claim_sparkles, find, find_all,
                     mark_task_done, return_home)

PAGE = "SuperValueReturn/title"
DOT = "SuperValueReturn/notification_dot"
MAX_SWIPES = 8
LOWER_CONTENT = (0, 20, 100, 88)
COMMON_LOWER_CLAIMS = TEXT_CLAIM_CONTROLS


@dataclass(frozen=True)
class SuperValueSpec:
    task: object
    tab: str
    claims: tuple[str, ...] = ()
    requires_dot: bool = True


SPECS = (
    SuperValueSpec(empire_depot.TASK, "EmpireDepot/tab",
                   ("Common/button_claimable", "Common/button_claimable_alt",
                    "EmpireDepot/button_claimable")),
    SuperValueSpec(lucky_raffle.TASK, "LuckyRaffle/tab",
                   ("Common/button_claimable", "Common/button_claimable_alt",
                    "LuckyRaffle/button_claimable")),
    SuperValueSpec(city_growth_plan.TASK, "CityGrowthPlan/tab",
                   ("CityGrowthPlan/button_claim_all",)),
    # Login Gifts can contain a sparkling daily chest even after its tab dot
    # disappears, so it must be opened once on every daily scan.
    SuperValueSpec(login_gifts.TASK, "LoginGifts/tab", requires_dot=False),
)


def _near_tab(dot, tab) -> bool:
    return abs(dot[0] - tab[0]) <= 55 and abs(dot[1] - tab[1]) <= 40


def _owner_for_dot(dot, tabs):
    """Assign one marker to the nearest visible tab, never two neighbours."""
    candidates = [(spec, tab) for spec, tab in tabs
                  if tab is not None and abs(dot[1] - tab[1]) <= 40
                  and abs(dot[0] - tab[0]) <= 70]
    if not candidates:
        return None
    return min(candidates, key=lambda item:
               (dot[0] - item[1][0]) ** 2 + (dot[1] - item[1][1]) ** 2)


def _dots(bot, screen):
    # The dot changes brightness with the rotating artwork. 0.65 still gives
    # a single exact dot on the supplied variant while 0.80 misses it.
    return find_all(bot, DOT, screen, threshold=0.65, region=(0, 7, 100, 19))


def _tab_signature(screen, dot) -> bytes:
    """Position-independent fingerprint used to avoid reopening one red tab."""
    x, _ = dot
    left, right = max(0, x - 48), min(screen.shape[1], x + 24)
    patch = cv2.cvtColor(screen[42:125, left:right], cv2.COLOR_BGR2GRAY)
    tiny = cv2.resize(patch, (17, 8), interpolation=cv2.INTER_AREA)
    return np.packbits(tiny[:, 1:] > tiny[:, :-1]).tobytes()


def _signature_seen(signature: bytes, seen: set[bytes]) -> bool:
    """Allow a little animation noise while recognizing the same carousel tab."""
    for old in seen:
        if len(old) != len(signature):
            continue
        distance = sum((left ^ right).bit_count()
                       for left, right in zip(old, signature))
        if distance <= 12:
            return True
    return False


def _verify_clean(bot, ignored_keys=()) -> bool:
    """Verify that no red tab remains anywhere in the parent carousel."""
    for direction in (-1, 1):
        for step in range(MAX_SWIPES + 1):
            bot.check()
            screen = bot.screenshot()
            dots = _dots(bot, screen)
            tabs = [(spec, find(bot, spec.tab, screen, threshold=0.70,
                                region=(0, 7, 100, 20))) for spec in SPECS]
            for dot in dots:
                owner = _owner_for_dot(dot, tabs)
                if owner is None or owner[0].task.key not in ignored_keys:
                    return False
            if step < MAX_SWIPES:
                if direction < 0:
                    bot.swipe_percent(85, 14, 20, 14, duration=0.5, delay=1)
                else:
                    bot.swipe_percent(20, 14, 85, 14, duration=0.5, delay=1)
    return True


def run_opened(bot, due_keys: set[str], *, handled: set[str] | None = None
               ) -> tuple[dict[str, str], bool]:
    """Sweep an opened carousel, clicking each red tab in encountered order."""
    results = {key: "no_dot" for key in due_keys}
    screen = bot.screenshot()
    if find(bot, PAGE, screen, threshold=0.72, region=(0, 0, 100, 13)) is None:
        return results, False

    handled = handled if handled is not None else set()
    attempted_this_run = set(handled)
    unknown_tabs: set[bytes] = set()
    if (login_gifts.KEY in due_keys
            and find(bot, login_gifts.PAGE, screen, threshold=0.70,
                     region=(0, 15, 45, 25)) is not None):
        login_gifts.claim_opened(bot)
        handled.add(login_gifts.KEY)
        mark_task_done(bot, login_gifts.KEY)
        results[login_gifts.KEY] = "processed"

    for direction in (-1, 1):
        for step in range(MAX_SWIPES + 1):
            bot.check()
            screen = bot.screenshot()
            if login_gifts.KEY in due_keys and login_gifts.KEY not in handled:
                login_tab = find(bot, "LoginGifts/tab", screen, threshold=0.70,
                                 region=(0, 7, 100, 20))
                if login_tab is not None:
                    bot.record("Gift Claims: Super Value Return mở Login Gifts "
                               "(kiểm tra quà ngày)")
                    bot.tap(*login_tab, delay=1)
                    claimed = bool(login_gifts.claim_opened(bot))
                    results[login_gifts.KEY] = "processed" if claimed else "checked"
                    handled.add(login_gifts.KEY)
                    mark_task_done(bot, login_gifts.KEY)
                    screen = bot.screenshot()
            dots = _dots(bot, screen)
            tabs = [(spec, find(bot, spec.tab, screen, threshold=0.70,
                                region=(0, 7, 100, 20))) for spec in SPECS]
            for dot in dots:
                match = _owner_for_dot(dot, tabs)
                if match is None:
                    signature = _tab_signature(screen, dot)
                    if _signature_seen(signature, unknown_tabs):
                        continue
                    unknown_tabs.add(signature)
                    bot.tap(max(0, dot[0] - 25), min(screen.shape[0] - 1, dot[1] + 16),
                            delay=1)
                    report = claim_fixed_controls(
                        bot, COMMON_LOWER_CLAIMS, max_taps=16,
                        region=LOWER_CONTENT)
                    if not back_if_close_x(bot):
                        claim_sparkles(bot, region=LOWER_CONTENT, attempts=4)
                    bot.log("Gift Claims: Super Value Return đã xử lý phần dưới "
                            "của tab đỏ chưa nhận diện")
                    continue
                spec, tab = match
                key = spec.task.key
                if key not in due_keys or key in attempted_this_run:
                    continue
                has_dot = True
                marker = "có dấu đỏ" if has_dot else "kiểm tra quà ngày"
                bot.record(f"Gift Claims: Super Value Return mở {spec.task.label} ({marker})")
                bot.tap(*tab, delay=1)
                if key == login_gifts.KEY:
                    count = login_gifts.claim_opened(bot)
                    report = ClaimReport(count, count)
                elif key == city_growth_plan.KEY:
                    claimed = int(bool(city_growth_plan.claim_opened(bot)))
                    report = ClaimReport(claimed, claimed)
                else:
                    fixed = claim_fixed_controls(
                        bot, COMMON_LOWER_CLAIMS, max_taps=16,
                        region=LOWER_CONTENT)
                    if back_if_close_x(bot):
                        report = fixed
                    else:
                        sparkle = claim_sparkles(bot, region=LOWER_CONTENT,
                                                 attempts=4)
                        report = ClaimReport(
                            fixed.attempted + sparkle.attempted,
                            fixed.verified + sparkle.verified)

                after = bot.screenshot()
                after_dots = _dots(bot, after)
                after_tabs = [(candidate, find(
                    bot, candidate.tab, after, threshold=0.70,
                    region=(0, 7, 100, 20))) for candidate in SPECS]
                cleared = not any(
                    (owner := _owner_for_dot(red_dot, after_tabs)) is not None
                    and owner[0].task.key == key for red_dot in after_dots)
                results[key] = ("cleared" if cleared else
                                "claimed_remaining" if report.claimed else
                                "visited_remaining" if report.acted else "remaining")
                attempted_this_run.add(key)
                if (cleared or not spec.requires_dot
                        or key not in (login_gifts.KEY, city_growth_plan.KEY)):
                    handled.add(key)
                    mark_task_done(bot, key)
                bot.log(f"Gift Claims: {spec.task.label} - dấu đỏ "
                        f"{'đã mất' if cleared else 'vẫn còn'} sau xử lý")

            if step == MAX_SWIPES:
                break
            if direction < 0:
                bot.swipe_percent(85, 14, 20, 14, duration=0.5, delay=1)
            else:
                bot.swipe_percent(20, 14, 85, 14, duration=0.5, delay=1)

    clean = _verify_clean(bot, handled)
    if clean and due_keys - handled:
        # The region-1 coordinator owns the daily checkpoints.  Once this
        # complete two-direction scan sees no red tab, it marks every
        # remaining child in this parent DONE instead of reopening tabs that
        # no longer advertise a claimable reward.
        bot.record("Gift Claims: Super Value Return hết badge nhưng vẫn còn "
                   "task DB chưa được mở; bộ điều phối sẽ coi cả nhóm DONE")
    bot.record("Gift Claims: Super Value Return - "
               + ("DONE, phần trên đã hết dấu đỏ" if clean
                  else "chưa DONE, phần trên vẫn còn dấu đỏ"))
    return_home(bot)
    return results, clean


KEYS = {spec.task.key for spec in SPECS}
