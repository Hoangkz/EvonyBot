"""
boss_names.py — turn what OCR read on a rally card (name label, power) into a
boss from boss.py and its level, and decide whether the Join Monster War
tab ticks it.

- The name label is "(Boss) <name>" or "(Boss) <tier> <name>", e.g.
  "(Boss) Junior Hydra". The tier word gives the level through that boss's
  own table in boss.py ("Senior" is level 3 for Cerberus, 2 for Knight Bayard).
- A boss with levels but no tier word in its name: the level whose power in
  boss.py is closest to the power read on the card.
- A boss whose levels have neither tier nor power in boss.py (and a boss
  without levels) is checked by name only.
- The OCR text may hold "?" for glyphs without a sample yet, so names and
  tiers are matched loosely (see _match).
"""
import difflib
import math
import re

from ...ocr.read_power import parse as parse_power

MATCH_CUTOFF = 0.75     # difflib ratio needed to accept a name / tier
MAX_UNKNOWN = 0.5       # more than this share of "?" in a read: too unsure, not checked
POWER_TOLERANCE = 1.3   # the power read may be at most this factor off a level's power

_catalog: dict | None = None


class Boss:
    def __init__(self, name: str):
        self.name = name
        self.levels: dict[int, tuple[str | None, int | None]] = {}   # level -> (tier, power)
        self.power_texts: dict[int, str] = {}                        # level -> "120.2m"

    @property
    def has_level_data(self) -> bool:
        """Whether boss.py gives a tier or power for any of its levels, i.e.
        whether the level on a card can be told at all."""
        return any(tier or power for tier, power in self.levels.values())

    def level_of_tier(self, tier: str) -> int | None:
        for level, (level_tier, _) in self.levels.items():
            if level_tier and level_tier.lower() == tier:
                return level
        return None

    def level_of_power_text(self, text: str | None) -> int | None:
        """Level whose power text ("120.2m") fits the OCR `text` ("12?.2?"): a "?"
        (glyph without a sample) is a position to skip, matching any 1-2 characters.
        Only a single fitting level counts."""
        if not text or "?" not in text or _too_unknown(text):
            return None
        pattern = re.compile("".join(".{1,2}" if ch == "?" else re.escape(ch)
                                     for ch in text.lower()))
        fits = [level for level, raw in self.power_texts.items() if pattern.fullmatch(raw)]
        return fits[0] if len(fits) == 1 else None

    def level_of_power(self, power: int | None) -> int | None:
        """Level whose power is closest (by ratio) to `power`, if close enough."""
        known = [(level, p) for level, (_, p) in self.levels.items() if p]
        if not power or not known:
            return None
        level, closest = min(known, key=lambda lp: abs(math.log(power / lp[1])))
        return level if abs(math.log(power / closest)) <= math.log(POWER_TOLERANCE) else None


def catalog() -> dict:
    """{"bosses": {lower name: Boss}, "tiers": {lower tier word}} from boss.py."""
    global _catalog
    if _catalog is None:
        # import trong hàm: bot không import ui ở mức module (tránh import vòng ui <-> bot).
        from ui.tabs.boss import DATA
        bosses: dict[str, Boss] = {}
        for category in DATA["boss_categories"]:
            for entry in category["list"]:
                boss = bosses.setdefault(entry["name"].lower(), Boss(entry["name"]))
                for level in entry.get("levels", []):
                    if isinstance(level, dict):
                        boss.levels[level["level"]] = (level.get("tier"),
                                                       parse_power(level.get("power")))
                        if level.get("power"):
                            boss.power_texts[level["level"]] = str(level["power"]).lower()
        tiers = {tier.lower() for boss in bosses.values()
                 for tier, _ in boss.levels.values() if tier}
        _catalog = {"bosses": bosses, "tiers": tiers}
    return _catalog


def parse(text: str | None) -> tuple[Boss | None, str | None]:
    """(boss, tier word or None) from the OCR text of the name label."""
    if not text:
        return None, None
    text = re.sub(r"^\s*\([^)]*\)", "", text)        # bỏ "(Boss)" ở đầu
    # Boss Special (Viking...) ghi nhãn "Lv.1 Viking" thay vì "(Boss) ...": bỏ "Lv.N" ở đầu ("?" = glyph chưa có mẫu).
    text = re.sub(r"^\s*[l?][v?]\.?\s*\d+\s+", "", text)
    # Bỏ loại quân trong ngoặc ở cuối, VD Pan có 3 loại: "Pan (Ranged Troop)" (OCR đọc
    # "pan (panged ?roop)"); ngoặc có thể bị cắt mất ở mép vùng đọc.
    text = re.sub(r"\([^)]*\)?\s*$", "", text).strip()
    bosses, tiers = catalog()["bosses"], catalog()["tiers"]
    words = text.split()
    if len(words) >= 2:
        tier = _match(words[0], tiers)
        name = _match(" ".join(words[1:]), bosses)
        if tier and name and bosses[name].level_of_tier(tier) is not None:
            return bosses[name], tier
    name = _match(text, bosses)
    return (bosses[name] if name else None), None


def level(boss: Boss | None, tier: str | None, read_power) -> tuple[int | None, int | None]:
    """(level, power read) of `boss`: from its tier word if there is one,
    else from `read_power()` (the power text, called only then) for a boss with levels."""
    if boss is None or not boss.has_level_data:
        return None, None
    if tier:
        return boss.level_of_tier(tier), None
    text = read_power()
    found = boss.level_of_power_text(text)
    if found is not None:
        return found, text
    power = parse_power(text)
    return boss.level_of_power(power), text


def selection(settings: dict) -> dict[str, tuple[set[int], bool]] | None:
    """The tab's ticked bosses as {name: (ticked levels, plain)}; `plain` is
    True when a boss of that name without levels is ticked (Nian is in both
    Boss Standard and Boss Event). None if the settings have no boss selection
    at all (then every boss is wanted)."""
    selected = settings.get("selected_bosses")
    if selected is None:
        return None
    result: dict[str, tuple[set[int], bool]] = {}
    for entry in selected:
        levels, plain = result.get(entry["name"], (set(), False))
        ticked = set(entry.get("levels", []))
        result[entry["name"]] = (levels | ticked, plain or not ticked)
    return result


def wanted(selected: dict[str, tuple[set[int], bool]] | None, boss: Boss | None,
           level: int | None) -> bool:
    """Whether to join `boss` at `level`. An unknown boss is never wanted. A
    level that was told must be ticked. Without a level, the boss is wanted if
    its plain (no-level) entry is ticked, or if boss.py gives no tier / power
    to tell its level anyway (then its name is enough)."""
    if selected is None:
        return True
    if boss is None or boss.name not in selected:
        return False
    levels, plain = selected[boss.name]
    if level is None:
        return plain or not boss.has_level_data
    return level in levels


def _too_unknown(text: str) -> bool:
    return text.count("?") > len(text) * MAX_UNKNOWN


def _match(text: str, choices) -> str | None:
    """The choice (lower case) `text` reads as. A "?" (glyph without a sample,
    maybe letters touching) stands for 1-3 letters: if exactly one choice fits,
    that's it. Otherwise the closest choice by difflib, if close enough."""
    choices = list(choices)
    if _too_unknown(text):
        return None
    if "?" in text:
        pattern = re.compile("".join(".{1,3}" if ch == "?" else re.escape(ch) for ch in text))
        fits = [choice for choice in choices if pattern.fullmatch(choice)]
        if len(fits) == 1:
            return fits[0]
        if fits:    # nhiều lựa chọn cùng khớp phần đọc được: lấy cái giống nhất
            return difflib.get_close_matches(text.replace("?", ""), fits, n=1, cutoff=0)[0]
    match = difflib.get_close_matches(text, choices, n=1, cutoff=MATCH_CUTOFF)
    if match:
        return match[0]
    # Game đôi khi đảo thứ tự từ (VD "Senior Bayar Knight" cho Knight Bayard):
    # so lại sau khi sắp xếp các từ.
    by_words = {" ".join(sorted(choice.split())): choice for choice in choices}
    match = difflib.get_close_matches(" ".join(sorted(text.split())), list(by_words), n=1,
                                      cutoff=MATCH_CUTOFF)
    return by_words[match[0]] if match else None
