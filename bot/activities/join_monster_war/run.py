"""
run.py — "Join Monster War" activity (port of C# Boss).

Opens the alliance War list and joins monster (boss) rallies: taps "Join"
on a rally not joined yet, picks the chosen troop preset and marches.
Rallies of skipped bosses, or whose join text is red (can't join), are
skipped; the list is scrolled when nothing is left to join. Each loop
takes one screenshot, finds the first known image on it (checked in list
order) and acts on it. When stamina runs out, uses stamina items ("Use
Stamina" ALL / 100), or ends the activity with "Use Stamina" No.
"""
from ...common import click_images, delay, exit_images, find_first, go_home
from ...context import TEMPLATE_DIR
from ...ocr import read_coords
from .constants import (ALLIANCE, BACK, CERBERUS, CHOOSE_DEVELOPMENT, CHOOSE_FAVORITE, JB, JOIN,
                        JOIN_LIST, JOIN_MAX_Y, JOIN_MIN_Y, JOINED, LEAVE_ALLIANCE_POPUP, LOCATION,
                        MARCH, MARCH_SCREEN, NOT_JOIN_LIMIT, OUT_OF_STAMINA, PLUS, SAME_SPOT,
                        SCROLL, SELECT, SELECT_GENERAL, STAMINA_ITEM, TAP, TROOP_CHECK,
                        USE_STAMINA)


def run(bot, settings: dict):
    """`bot` is the device's BotContext; `settings` is the "Join Monster War" tab's config."""
    _Boss(bot, settings).run()


def _exists(path: str) -> bool:
    return (TEMPLATE_DIR / path).exists()


def _near(point, points) -> bool:
    return any(abs(px - point[0]) < SAME_SPOT and abs(py - point[1]) < SAME_SPOT
               for px, py in points)


def _troop(text) -> int:
    """"Troop 3" -> 3 (Troop 1 when nothing is chosen)."""
    try:
        return int(str(text).split()[-1])
    except (IndexError, ValueError):
        return 1


def _targets() -> list[tuple[str, str]]:
    return [
        ("click/lencap.png", TAP),
        (f"{JB}/hettheluc.png", OUT_OF_STAMINA),
        (MARCH, MARCH_SCREEN),
        (JOIN, JOIN_LIST),
        (f"{JB}/Joined.png", JOINED),
        (f"{JB}/PvPWar.png", SCROLL),
        (f"{JB}/checkChienTranh.png", SCROLL),
        ("Items/outLM.png", LEAVE_ALLIANCE_POPUP),
        (f"{JB}/chientranh.png", TAP),
        *[(path, BACK) for path in exit_images()],
        *[(path, TAP) for path in click_images()],
        (f"{JB}/lienminh.png", ALLIANCE),
    ]


class _Boss:
    def __init__(self, bot, settings: dict):
        self.bot = bot
        self.troop = _troop(settings.get("troop"))
        self.use_stamina = settings.get("use_stamina")   # "ALL" / "100" / "No"
        self.skipped_bosses = [CERBERUS] if settings.get("skip_cerberus") else []
        self.not_join: list[tuple[int, int]] = []           # C# settingboss.ListBossNotJoin
        self.screen_blacklist: list[tuple[int, int]] = []   # rallies handled on this screen
        self.swipe = 0
        self.previous = None
        self.can_select_general = all(_exists(p) for p in (
            SELECT_GENERAL, CHOOSE_DEVELOPMENT, CHOOSE_FAVORITE, SELECT))
        self.can_read_coords = _exists(LOCATION)

    def run(self):
        bot = self.bot
        targets = _targets()
        while True:
            screen = bot.screenshot()
            # Alliance / leave-alliance taps are offsets from the image's top-left corner.
            action, pos = find_first(bot, screen, targets,
                                     top_left={ALLIANCE, LEAVE_ALLIANCE_POPUP})
            if action == JOIN_LIST and self.previous != JOIN_LIST:
                self.screen_blacklist.clear()
            self.previous = action

            if action == OUT_OF_STAMINA:
                if self.use_stamina not in ("ALL", "100"):
                    return
                bot.tap(*pos)
                delay(bot, 2)
                self._use_stamina()
            elif action == MARCH_SCREEN:
                self._march(screen, pos)
            elif action == JOIN_LIST:
                self._join()
            elif action == SCROLL:
                self._scroll()
                delay(bot, 2)
            elif action == JOINED:
                self._scroll()
                self.not_join = [p for p in self.not_join if p[0] < 800 and p[1] < 800]
                delay(bot, 2)
            elif action == TAP:
                bot.tap(*pos)
                delay(bot, 2)
            elif action == BACK:
                bot.back()
                delay(bot, 2)
            elif action == ALLIANCE:
                bot.tap(pos[0] + 20, pos[1] - 10)
                delay(bot, 5)
            elif action == LEAVE_ALLIANCE_POPUP:
                bot.tap(pos[0] + 40, pos[1] + 40)
                delay(bot, 2)
                bot.back()
                delay(bot, 2)
            else:
                go_home(bot, screen)
                delay(bot, 2)

    def _scroll(self):
        """Scroll the War list down twice, then up twice, and so on."""
        if self.swipe < 2:
            self.bot.swipe_percent(50, 65, 50, 40, duration=1.0)
        else:
            self.bot.swipe_percent(50, 40, 50, 65, duration=1.0)
        self.swipe = (self.swipe + 1) % 4

    def _use_stamina(self):
        """Stamina items list (C# Data.Stamina): tap the top stamina item, set
        the amount ("ALL": the button at 28.9 % / 71.6 %, "100": the button
        right of "+") and tap Use, then close the list."""
        bot = self.bot
        items = sorted(bot.find_all(STAMINA_ITEM, center=False), key=lambda p: p[1])
        if items:
            bot.tap(*items[0])
            delay(bot, 3)
            use = bot.find(USE_STAMINA, center=False)
            if use is None:
                return
            if self.use_stamina == "ALL":
                bot.tap_percent(28.9, 71.6, count=2)
            else:
                plus = bot.find(PLUS, center=False)
                if plus is not None:
                    pw, _ = bot.template_size(PLUS)
                    bot.tap(plus[0] + pw, plus[1] + 5)
                    bot.tap(plus[0] + pw, plus[1] + 5)
            delay(bot, 2)
            bot.tap(*use)
        else:
            bot.back()
        delay(bot, 2)
        bot.back()
        delay(bot, 2)

    # ---- march screen ------------------------------------------------
    def _march(self, screen, march_pos):
        """March screen after tapping Join: pick the troop preset and march."""
        bot = self.bot
        if bot.find(f"{JB}/bossMonster.png", screen=screen) is None:
            bot.back()      # not a monster rally
            delay(bot, 2)
            return

        for _ in range(7):
            bot.tap_percent(self.troop * 11, 11)
            delay(bot)
            if bot.find(TROOP_CHECK) is not None:
                break
        else:
            bot.back()
            delay(bot, 2)
            return

        if self.can_select_general:
            self._select_general()

        pos = bot.find(MARCH)
        bot.tap(*(pos or march_pos))
        delay(bot)
        # Wait for the march screen to close; if it doesn't, back out.
        for _ in range(5):
            if bot.find(TROOP_CHECK) is None:
                return
            delay(bot)
        bot.back()
        bot.back()
        delay(bot, 2)

    def _select_general(self):
        """Pick a general: Select General -> Development -> Favorite -> Select (up to 2 times)."""
        bot = self.bot
        for _ in range(2):
            pos = bot.find(SELECT_GENERAL, threshold=0.7)
            if pos is None:
                return
            bot.tap(*pos)
            delay(bot, 2)
            pos = bot.find(CHOOSE_DEVELOPMENT)
            if pos is not None:
                bot.tap(*pos)
                delay(bot, 2)
                pos = bot.find(CHOOSE_FAVORITE)
                if pos is not None:
                    bot.tap(*pos)
                    delay(bot, 2)
            pos = bot.find(SELECT)
            if pos is None:
                return
            bot.tap(*pos)
            for _ in range(5):
                delay(bot, 1)
                if bot.find(MARCH) is not None:
                    break

    # ---- War list ----------------------------------------------------
    def _join(self):
        """War list: tap Join on the first rally that can be joined, or scroll."""
        bot = self.bot
        screen = bot.screenshot()
        jw, jh = bot.template_size(JOIN)
        points = [p for p in bot.find_all(JOIN, threshold=0.8, screen=screen, center=False)
                  if JOIN_MIN_Y < p[1] < JOIN_MAX_Y]
        points = [p for p in points
                  if not _near(p, self.not_join) and not _near(p, self.screen_blacklist)]
        if not points:
            self._scroll()
            self.screen_blacklist.clear()
            delay(bot, 3)   # let the list stop moving
            return

        for x, y in points:
            region = bot.crop(screen, x - 90, y - 150, 160, 190)
            coords = None
            if self.can_read_coords:
                pin = bot.find(LOCATION, screen=region, center=False)
                if pin is not None:
                    lw, _ = bot.template_size(LOCATION)
                    coords = read_coords(bot.crop(region, pin[0] + lw, pin[1], 80, 15))
                    if coords is None:
                        continue
                    if coords in self.not_join:
                        self.screen_blacklist.append((x, y))
                        continue

            skipped = any(bot.find(path, threshold=0.7, screen=region) is not None
                          for path in self.skipped_bosses)
            if skipped or self._join_text_is_red(screen, x, y, jh):
                self._remember(coords, x, y)
                continue

            bot.tap(x + jw // 2, y + jh // 2)
            self._remember(coords, x, y)
            delay(bot, 3)
            break

        self.not_join = self.not_join[-NOT_JOIN_LIMIT:]

    def _remember(self, coords, x, y):
        if coords is not None:
            self.not_join.append(coords)
        self.screen_blacklist.append((x, y))

    def _join_text_is_red(self, screen, x, y, join_h) -> bool:
        """Red text under the Join button means this rally can't be joined."""
        crop = self.bot.crop(screen, x - 12, y + join_h - 3, 60, 20)
        b, g, r = crop[..., 0], crop[..., 1], crop[..., 2]
        return int(((r > 180) & (g < 100) & (b < 100)).sum()) > 5
