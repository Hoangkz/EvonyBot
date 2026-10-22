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
    PRECIOUS_BLAZON_EXCHANGE = "PreciousBlazonExchange"
    POSEIDONS_DAY = "PoseidonsDay"
    HYPNOS_DREAM = "HypnosDream"
    DWARFS_TREASURE = "DwarfsTreasure"
    DWARFS_LUCKY_APPLE = "DwarfsLuckyApple"
    REVELATION_OF_HORUS = "RevelationOfHorus"
    SEALED_IMPERIAL_TREASURY = "SealedImperialTreasury"
    GIANTS_WISDOM_TEMPLE = "GiantsWisdomTemple"
    WISHFUL_WINDMILL_FESTIVAL = "WishfulWindmillFestival"
    EAGLE_OF_FREEDOM = "EagleOfFreedom"


TITLE_TEMPLATES = {
    GiftScreen.SUPER_VALUE_RETURN: "SuperValueReturn/title",
    GiftScreen.VALUABLE_EVENT: "ValuableEvent/title",
    GiftScreen.EVENT_CENTER: "EventCenter/title",
    GiftScreen.DRAGON_BATTLE: "DragonBattle/title",
    # Check Eagle before Grace: their wide red title bars score about 0.727
    # against each other, while Eagle's supplied title is an exact 1.0 match.
    GiftScreen.EAGLE_OF_FREEDOM: "EagleOfFreedom/title",
    GiftScreen.GRACE_OF_STAR_TRAIL: "GraceOfStarTrail/title",
    GiftScreen.BACCHUS_TAVERN: "BacchusTavern/title",
    GiftScreen.BACK_TO_TERRITORY: "BackToTerritory/title",
    GiftScreen.FOLLOW_US: "FollowUs/title",
    GiftScreen.PRECIOUS_BLAZON_EXCHANGE: "PreciousBlazonExchange/title",
    GiftScreen.POSEIDONS_DAY: "PoseidonsDay/title",
    GiftScreen.HYPNOS_DREAM: "HypnosDream/title",
    GiftScreen.DWARFS_TREASURE: "DwarfsTreasure/title",
    GiftScreen.DWARFS_LUCKY_APPLE: "DwarfsLuckyApple/title",
    GiftScreen.REVELATION_OF_HORUS: "RevelationOfHorus/title",
    GiftScreen.SEALED_IMPERIAL_TREASURY: "SealedImperialTreasury/title",
    GiftScreen.WISHFUL_WINDMILL_FESTIVAL: "WishfulWindmillFestival/title",
}

PAGE_MARKERS = {
    # Giant's page title is animated/scaled differently from its stable list
    # label.  The exact Skip animation controls supplied by the user are a
    # safer page identity and cannot occur on the Event Center list.
    GiftScreen.GIANTS_WISDOM_TEMPLE: (
        "GiantsWisdomTemple/checkbox_skip_animation_unchecked",
        "GiantsWisdomTemple/checkbox_skip_animation_checked",
    ),
}


def identify(bot, screen=None) -> GiftScreen | None:
    """Identify the open flow from its fixed title, never its lobby icon."""
    screen = bot.screenshot() if screen is None else screen
    for name, template in TITLE_TEMPLATES.items():
        if find(bot, template, screen, threshold=0.72, region=(0, 0, 100, 13)) is not None:
            return name
    for name, templates in PAGE_MARKERS.items():
        if any(find(bot, template, screen, threshold=0.72,
                    region=(35, 35, 100, 65)) is not None
               for template in templates):
            return name
    return None

