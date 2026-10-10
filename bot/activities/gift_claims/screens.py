"""Stable names for gift screens, identified only by their inner titles."""
from enum import Enum

from .common import find


class GiftScreen(str, Enum):
    UNKNOWN = "Unknown"
    SUPER_VALUE_RETURN = "SuperValueReturn"
    VALUABLE_EVENT = "ValuableEvent"
    EVENT_CENTER = "EventCenter"
    DRAGON_BATTLE = "DragonBattle"
    GRACE_OF_STAR_TRAIL = "GraceOfStarTrail"
    BACCHUS_TAVERN = "BacchusTavern"
    BACK_TO_TERRITORY = "BackToTerritory"
    FOLLOW_US = "FollowUs"


TITLE_TEMPLATES = {
    GiftScreen.SUPER_VALUE_RETURN: "SuperValueReturn/title",
    GiftScreen.VALUABLE_EVENT: "ValuableEvent/title",
    GiftScreen.EVENT_CENTER: "EventCenter/title",
    GiftScreen.DRAGON_BATTLE: "DragonBattle/title",
    GiftScreen.GRACE_OF_STAR_TRAIL: "GraceOfStarTrail/title",
    GiftScreen.BACCHUS_TAVERN: "BacchusTavern/title",
    GiftScreen.BACK_TO_TERRITORY: "BackToTerritory/title",
    GiftScreen.FOLLOW_US: "FollowUs/title",
}


def identify(bot, screen=None) -> GiftScreen | None:
    """Identify the open flow from its fixed title, never its lobby icon."""
    screen = bot.screenshot() if screen is None else screen
    for name, template in TITLE_TEMPLATES.items():
        if find(bot, template, screen, threshold=0.72, region=(0, 0, 100, 13)) is not None:
            return name
    return None

