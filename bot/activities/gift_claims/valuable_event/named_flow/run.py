"""Shared Valuable Event processing for scanner and standalone DB flows."""
from ...common import (ClaimReport, TEXT_CLAIM_CONTROLS, back_if_close_x,
                       claim_fixed_controls, claim_sparkles, return_home,
                       select_carousel_tab, tap_claims)
from ...lobby import open_named

LOWER_CONTENT = (0, 20, 100, 88)
QUIET_ROUNDS = 3


def process_lower(bot, navigation: tuple[str, ...],
                  claims: tuple[str, ...]) -> tuple[ClaimReport, int]:
    """Claim known controls first and re-check them after each glow probe."""
    navigated = (tap_claims(bot, navigation, max_taps=len(navigation),
                            initial_wait_attempts=2, region=LOWER_CONTENT)
                 if navigation else 0)
    controls = tuple(dict.fromkeys((*claims, *TEXT_CLAIM_CONTROLS)))
    total = ClaimReport()
    empty_rounds = 0
    rounds = 0
    while empty_rounds < QUIET_ROUNDS and rounds < 12:
        rounds += 1
        fixed = claim_fixed_controls(
            bot, controls, max_taps=16,
            initial_wait_attempts=2 if rounds == 1 else 0,
            region=LOWER_CONTENT,
        )
        total = ClaimReport(total.attempted + fixed.attempted,
                            total.verified + fixed.verified)

        # A known launcher may reveal a detail layer. Close a supplied X and
        # continue from the parent instead of ending before glow inspection.
        back_if_close_x(bot)
        sparkle = claim_sparkles(bot, region=LOWER_CONTENT, attempts=1)
        total = ClaimReport(total.attempted + sparkle.attempted,
                            total.verified + sparkle.verified)
        if fixed.claimed or sparkle.claimed:
            empty_rounds = 0
        else:
            empty_rounds += 1
        bot.log("Gift Claims: Valuable Event vòng kiểm tra "
                f"{rounds}, không phản hồi {empty_rounds}/{QUIET_ROUNDS}")

    if empty_rounds >= QUIET_ROUNDS:
        bot.record("Gift Claims: Valuable Event không còn quà xác minh sau "
                   f"{QUIET_ROUNDS} vòng; bỏ qua phần lấp lánh/trả phí và "
                   "coi mục đã xét xong")
    return total, navigated


def run_carousel_claim(bot, screen_name, page: str, tab: str,
                       claims: tuple[str, ...], *,
                       navigation: tuple[str, ...] = ()) -> bool:
    if not open_named(bot, screen_name):
        return False
    if not select_carousel_tab(bot, page, tab):
        return_home(bot)
        return False
    report, _ = process_lower(bot, navigation, claims)
    bot.log(f"Gift Claims: claims {report.verified}/{report.attempted} verified")
    return_home(bot)
    return True
