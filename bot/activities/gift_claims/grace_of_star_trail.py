"""Claim the highlighted cumulative reward on Grace of Star Trail."""
from .common import (GiftTask, claim_fixed_controls, open_event_center_event,
                     return_home, tap_claims)

KEY = "gift_grace_of_star_trail"


def run(bot):
    if not open_event_center_event(bot, "GraceOfStarTrail/list_row",
                                   "GraceOfStarTrail/title"):
        return False
    # The row dot leads to a nested Star Trail Gift tab. Its green Claim is
    # the free reward; cumulative-draw chests on the main page are not tapped.
    tap_claims(bot, ("GraceOfStarTrail/button_star_trail_gift",),
               max_taps=1, initial_wait_attempts=2)
    claim_fixed_controls(bot, ("GraceOfStarTrail/button_claim",))
    return_home(bot)
    return True


TASK = GiftTask(KEY, "Grace of Star Trail", run)
