"""
run.py — Activity "Join Monster War" (Optimized for Multi-threading & Low CPU).
"""
from ...common import click_images, delay, exit_images, find_first, go_home, wait_gone
from ...context import TEMPLATE_DIR
from ...ocr import read_coords
from .constants import (ALLIANCE_ICON, BACK, BOSS_MONSTER, CERBERUS, CHOOSE_DEVELOPMENT, CHOOSE_FAVORITE, IDLE,
                        JB, JOIN, JOIN_LIST, JOIN_MAX_Y, JOIN_MIN_Y, JOINED, JOINED_BUTTON,
                        LEAVE_ALLIANCE_POPUP, LISTBOSS, LOCATION, MARCH, MARCH_SCREEN,
                        NO_BOSS, NOT_JOIN_LIMIT, OUT_OF_STAMINA, PLUS, PVP_WAR, REGIONS, SAME_SPOT, SCROLL,
                        SELECT, SELECT_GENERAL, STAMINA_ITEM, TAP, TROOP_CHECK, USE_STAMINA,
                        WAR_TAB)

# --- CACHE CHECKS TỒN TẠI FILE (Chạy 1 lần duy nhất khi import, không đọc ổ cứng liên tục) ---
def _check_exists(path: str) -> bool:
    return (TEMPLATE_DIR / path).exists()

CAN_SELECT_GENERAL = all(_check_exists(p) for p in (SELECT_GENERAL, CHOOSE_DEVELOPMENT, CHOOSE_FAVORITE, SELECT))
CAN_READ_COORDS = _check_exists(LOCATION)


def run(bot, settings: dict):
    """`bot` là BotContext của thiết bị; `settings` là cấu hình của tab "Join Monster War".
    Trả về IDLE nếu thoát vì rảnh, None nếu dừng hẳn."""
    return _Boss(bot, settings).run()


class _Boss:
    def __init__(self, bot, settings: dict):
        self.bot = bot
        self.troop = _troop(settings.get("troop"))          # Số thứ tự preset troop (1, 2, 3...)
        self.use_stamina = settings.get("use_stamina")     # "ALL" / "100" / "No"
        self.skipped_bosses = [CERBERUS] if settings.get("skip_cerberus") else []
        self.not_join: list[tuple[int, int]] = []           # Tọa độ boss đã xử lý (X, Y in-game)
        self.screen_blacklist: list[tuple[int, int]] = []   # Tọa độ nút Join đã qua xử lý trên screen hiện tại
        self.swipe = 0                                      # Bộ đếm chu kỳ cuộn (0,1: xuống; 2,3: lên)
        self.previous = None                                # Action của vòng lặp trước
        self.exit_when_idle = settings.get("exit_when_idle", False)  # Worker bật khi còn activity khác
        self.idle_scrolls = 0                               # Số lần cuộn liên tiếp mà không join được boss

    def run(self):
        bot = self.bot
        targets = _targets()
        
        while True:
            # Th3: cuộn hết 1 chu kỳ mà không có boss để join (đều Joined) -> rảnh
            if self.idle_scrolls >= IDLE_SCROLLS and self._idle():
                return IDLE

            # Luôn chụp màn hình mới ở đầu vòng lặp để đảm bảo tính đồng bộ
            screen = bot.screenshot()
            
            # Popup rời liên minh tap theo offset từ góc trên-trái
            action, pos = find_first(bot, screen, targets, top_left={LEAVE_ALLIANCE_POPUP}, regions=REGIONS)
            
            # Reset blacklist nút khi vừa chuyển trạng thái quay lại JOIN_LIST
            if action == JOIN_LIST and self.previous != JOIN_LIST:
                self.screen_blacklist.clear()
            self.previous = action

            if action == OUT_OF_STAMINA:
                if self.use_stamina not in ("ALL", "100"):
                    return
                bot.tap(*pos)
                wait_gone(bot, targets, action, pos, **_WAIT)
                self._use_stamina()

            elif action == NO_BOSS:
                # Th1: màn hình chính có Liên minh nhưng không có listboss
                # Th2: PvPWar nhưng không có nút Join / Joined nào -> rảnh
                if self._idle():
                    return IDLE
                continue   # màn hình không đổi -> không cần wait_gone

            elif action == MARCH_SCREEN:
                self._march(screen, pos)

            elif action == JOIN_LIST:
                self._join(screen)

            elif action in (SCROLL, JOINED):
                self._scroll()
                if action == JOINED:
                    # Dọn dẹp bớt mảng not_join nếu quá nhiều
                    self.not_join = [p for p in self.not_join if p[0] < 800 and p[1] < 800]

            elif action == TAP:
                bot.tap(*pos)

            elif action == BACK:
                bot.back()

            elif action == LEAVE_ALLIANCE_POPUP:
                bot.tap(pos[0] + 40, pos[1] + 40)
                wait_gone(bot, targets, action, pos, **_WAIT)
                bot.back()

            else:
                # Không nhận diện được màn hình -> Chờ nhẹ 1s rồi mới tính chuyện go_home
                delay(bot, 1)
                go_home(bot, bot.screenshot())

            # Chờ hành động cũ biến mất trước khi sang vòng lặp mới
            wait_gone(bot, targets, action, pos, **_WAIT)

    def _idle(self) -> bool:
        """Không có boss để join. Có activity khác -> True (thoát cho worker làm
        activity khác); chỉ có Join Boss -> chờ IDLE_WAIT giây rồi kiểm tra lại."""
        self.idle_scrolls = 0
        if self.exit_when_idle:
            return True
        delay(self.bot, IDLE_WAIT)
        return False

    def _scroll(self):
        """Cuộn danh sách War: 2 lần xuống, 2 lần lên."""
        self.idle_scrolls += 1
        if self.swipe < 2:
            self.bot.swipe_percent(50, 65, 50, 40, duration=0.8)
        else:
            self.bot.swipe_percent(50, 40, 50, 65, duration=0.8)
        self.swipe = (self.swipe + 1) % 4

    def _use_stamina(self):
        bot = self.bot
        items = sorted(bot.find_all(STAMINA_ITEM, center=False), key=lambda p: p[1])
        if items:
            bot.tap(*items[0])
            delay(bot, 2)
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
            delay(bot, 1)
            bot.tap(*use)
        else:
            bot.back()
        delay(bot, 1)
        bot.back()

    def _march(self, screen, march_pos):
        bot = self.bot
        if bot.find(BOSS_MONSTER, screen=screen, region=REGIONS[BOSS_MONSTER]) is None:
            bot.back()
            return

        # Chọn preset troop
        for _ in range(5):
            bot.tap_percent(self.troop * 11, 11)
            delay(bot, 0.5)
            if bot.find(TROOP_CHECK) is not None:
                break
        else:
            bot.back()
            return

        if CAN_SELECT_GENERAL:
            self._select_general()

        pos = bot.find(MARCH, region=REGIONS[MARCH])
        bot.tap(*(pos or march_pos))
        
        # Chờ màn hình March đóng
        for _ in range(5):
            delay(bot, 0.8)
            if bot.find(TROOP_CHECK) is None:
                return
        bot.back()

    def _select_general(self):
        bot = self.bot
        for _ in range(2):
            pos = bot.find(SELECT_GENERAL, threshold=0.7, region=REGIONS[SELECT_GENERAL])
            if pos is None:
                return
            bot.tap(*pos)
            delay(bot, 1.5)
            
            pos = bot.find(CHOOSE_DEVELOPMENT, region=REGIONS[CHOOSE_DEVELOPMENT])
            if pos is not None:
                bot.tap(*pos)
                delay(bot, 1)
                pos = bot.find(CHOOSE_FAVORITE)
                if pos is not None:
                    bot.tap(*pos)
                    delay(bot, 1)

            pos = bot.find(SELECT, region=REGIONS[SELECT])
            if pos is None:
                return
            bot.tap(*pos)
            
            for _ in range(5):
                delay(bot, 0.8)
                if bot.find(MARCH, region=REGIONS[MARCH]) is not None:
                    break

    def _join(self, screen):
        bot = self.bot
        jw, jh = bot.template_size(JOIN)
        
        # 1. Tìm các nút Join hợp lệ trong dải Y
        points = [p for p in bot.find_all(JOIN, threshold=0.8, screen=screen, center=False, region=REGIONS[JOIN])
                  if JOIN_MIN_Y < p[1] < JOIN_MAX_Y]
        
        # 2. Lọc nhanh các nút đã xử lý trên màn hình hiện tại (Blacklist)
        points = [p for p in points if not _near(p, self.screen_blacklist)]

        if not points:
            self._scroll()
            self.screen_blacklist.clear()
            return

        for x, y in points:
            region = bot.crop(screen, x - 90, y - 150, 160, 190)
            coords = None

            # 3. Chỉ OCR nếu bật flag CAN_READ_COORDS
            if CAN_READ_COORDS:
                pin = bot.find(LOCATION, screen=region, center=False)
                if pin is not None:
                    lw, _ = bot.template_size(LOCATION)
                    coords = read_coords(bot.crop(region, pin[0] + lw, pin[1], 80, 15))
                    
                    # Nếu đã xử lý tọa độ này rồi -> Skip ngay
                    if coords and coords in self.not_join:
                        self.screen_blacklist.append((x, y))
                        continue

            # 4. Kiểm tra boss bị skip hoặc dòng chữ đỏ
            skipped = any(bot.find(path, threshold=0.7, screen=region) is not None for path in self.skipped_bosses)
            if skipped or self._join_text_is_red(screen, x, y, jh):
                self._remember(coords, x, y)
                continue

            # 5. Tap nút Join
            bot.report_boss(coords)
            bot.tap(x + jw // 2, y + jh // 2)
            self._remember(coords, x, y)
            self.idle_scrolls = 0
            break

        self.not_join = self.not_join[-NOT_JOIN_LIMIT:]

    def _remember(self, coords, x, y):
        if coords is not None:
            self.not_join.append(coords)
        self.screen_blacklist.append((x, y))

    def _join_text_is_red(self, screen, x, y, join_h) -> bool:
        """Tối ưu thuật toán đếm pixel đỏ: linh hoạt hơn với render đồ họa khác nhau."""
        crop = self.bot.crop(screen, x - 12, y + join_h - 3, 60, 20)
        b, g, r = crop[..., 0], crop[..., 1], crop[..., 2]
        # Hạ tiêu chuẩn Red xuống > 160 và G/B < 110 để tránh lệch màu giữa các máy giả lập
        return int(((r > 160) & (g < 110) & (b < 110)).sum()) > 5


IDLE_SCROLLS = 4   # 1 chu kỳ cuộn (xuống, xuống, lên, lên) không có boss để join -> rảnh
IDLE_WAIT = 5      # giây chờ khi rảnh mà chỉ chạy Join Boss
_WAIT = {"top_left": {LEAVE_ALLIANCE_POPUP}, "tolerance": SAME_SPOT}


def _near(point, points) -> bool:
    return any(abs(px - point[0]) < SAME_SPOT and abs(py - point[1]) < SAME_SPOT for px, py in points)


def _troop(text) -> int:
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
        (JOINED_BUTTON, JOINED),
        (PVP_WAR, NO_BOSS),       # sau JOIN / JOINED: tới đây là list không có boss nào
        (WAR_TAB, SCROLL),
        ("Items/outLM.png", LEAVE_ALLIANCE_POPUP),
        (f"{JB}/chientranh.png", TAP),
        *[(path, BACK) for path in exit_images()],
        *[(path, TAP) for path in click_images()],
        (LISTBOSS, TAP),
        (ALLIANCE_ICON, NO_BOSS),  # sau LISTBOSS: màn hình chính không có boss
    ]
