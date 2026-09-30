"""
run.py — Activity "Join Monster War" (Optimized for Multi-threading & Low CPU).
"""
from ...common import click_images, delay, exit_images, find_first, go_home, wait_gone
from ...context import TEMPLATE_DIR
from ...ocr import read_boss_name, read_coords, read_power
from . import boss_names
from .boss_memory import JOINED as MEMORY_JOINED
from .boss_memory import SKIPPED as MEMORY_SKIPPED
from .boss_memory import BossMemory
from .constants import (ALLIANCE_ICON, BACK, BOSS_MONSTER, CHOOSE_DEVELOPMENT, CHOOSE_FAVORITE, IDLE,
                        JB, JOIN, JOIN_LIST, JOIN_MAX_Y, JOIN_MIN_Y, JOIN_THRESHOLD, JOINED, JOINED_BUTTON,
                        JOINED_OVERLAP,
                        LEAVE_ALLIANCE_POPUP, LIST_END_MAX_LIGHT, LIST_END_REGION, LISTBOSS, LOCATION,
                        MARCH, MARCH_SCREEN,
                        NO_BOSS, OUT_OF_STAMINA, PLUS, PVP_WAR, REGIONS, SAME_SPOT, SCROLL,
                        WAR_TICKED, WAR_UNTICK_TRIES,
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
    # BossMemory sống cùng BotContext (một lượt Start -> Stop của giả lập), nên
    # còn nguyên qua các lần worker gọi lại Join Boss sau khi làm activity khác.
    if getattr(bot, "boss_memory", None) is None:
        bot.boss_memory = BossMemory()
    return _Boss(bot, settings).run()


class _Boss:
    def __init__(self, bot, settings: dict):
        self.bot = bot
        self.troops = _troops(settings.get("troop"))        # Các preset troop được chọn (1, 2, 3...)
        self.troop_index = 0                                # Preset dùng cho lần march tiếp theo
        self.use_stamina = settings.get("use_stamina")     # "ALL" / "100" / "No"
        self.selected = boss_names.selection(settings)         # Boss được tích ở tab: {tên: cấp được tích}
        self.memory: BossMemory = bot.boss_memory           # Tọa độ boss đã tham gia / bỏ qua (X, Y in-game)
        self.pending = None                                 # Tọa độ boss vừa tap Join, chờ hành quân xong
        self.screen_blacklist: list[tuple[int, int]] = []   # Tọa độ nút Join đã qua xử lý trên screen hiện tại
        self.swipe = 0                                      # Vị trí trong chu kỳ cuộn (0-2: xuống; 3-5: lên)
        self.previous = None                                # Action của vòng lặp trước
        self.exit_when_idle = settings.get("exit_when_idle", False)  # Worker bật khi còn activity khác
        self.idle_scrolls = 0                               # Số lần cuộn liên tiếp mà không thấy boss mới
        self.next_screen = None                             # Ảnh mới nhất (sau khi cuộn / wait_gone), dùng cho vòng lặp kế tiếp
        self.war_taps = 0                                   # Số lần đã bấm bỏ tích ô "War" trong lượt chạy này

    def run(self):
        bot = self.bot
        targets = _targets()
        
        while True:
            # Th3: cuộn IDLE_SCROLLS lần mà không thấy boss mới (chưa có trong BossMemory) -> rảnh
            if self.idle_scrolls >= IDLE_SCROLLS and self._idle():
                return IDLE

            # Dùng ảnh vừa chụp (sau khi cuộn / wait_gone xác nhận chuyển màn), không có thì chụp mới
            screen, self.next_screen = self.next_screen, None
            if screen is None:
                screen = bot.screenshot()
            
            # Popup rời liên minh tap theo offset từ góc trên-trái
            action, pos = find_first(bot, screen, targets, top_left={LEAVE_ALLIANCE_POPUP}, regions=REGIONS)
            
            # Reset blacklist nút khi vừa chuyển trạng thái quay lại JOIN_LIST
            if action == JOIN_LIST and self.previous != JOIN_LIST:
                self.screen_blacklist.clear()
            self.previous = action

            # Danh sách War mà ô "War" (rally đánh người chơi) đang tích -> bấm bỏ tích trước
            if self._on_war_list(screen, action) and self._untick_war(screen):
                continue

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
                if not self._join(screen):
                    continue   # không tap Join (bỏ qua hết / đã cuộn) -> màn hình không cần chờ đổi

            elif action in (SCROLL, JOINED):
                self._scroll(screen)
                continue       # đã chụp ảnh sau khi cuộn (hoặc rảnh) -> không cần wait_gone

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

            # Chờ hành động cũ biến mất; ảnh xác nhận đã chuyển màn được dùng luôn cho
            # vòng lặp mới (None = hết giờ mà màn hình chưa đổi -> vòng lặp tự chụp lại)
            self.next_screen = wait_gone(bot, targets, action, pos, **_WAIT)

    def _on_war_list(self, screen, action) -> bool:
        """Đang ở màn danh sách War (tab PvP War). NO_BOSS có thể là màn hình
        chính (nút Liên minh) nên phải xem có tab PvP War không."""
        if action in (JOIN_LIST, JOINED, SCROLL):
            return True
        return action == NO_BOSS and self.bot.find(PVP_WAR, screen=screen, region=REGIONS[PVP_WAR]) is not None

    def _untick_war(self, screen) -> bool:
        """Ô "War" đang tích -> bấm bỏ tích rồi chờ dấu tích mất (ảnh xác nhận được
        dùng cho vòng lặp kế tiếp). True nếu đã bấm. Mỗi lượt chạy bấm tối đa
        WAR_UNTICK_TRIES lần, để không bấm qua bấm lại khi game chậm."""
        if self.war_taps >= WAR_UNTICK_TRIES:
            return False
        bot = self.bot
        pos = bot.find(WAR_TICKED, screen=screen, region=REGIONS[WAR_TICKED])
        if pos is None:
            return False
        self.war_taps += 1
        bot.log("Bỏ tích ô War (chỉ giữ rally đánh boss)")
        bot.tap(*pos)
        for _ in range(6):
            delay(bot, 0.5)
            shot = bot.screenshot()
            if bot.find(WAR_TICKED, screen=shot, region=REGIONS[WAR_TICKED]) is None:
                self.next_screen = shot
                break
        return True

    def _idle(self) -> bool:
        """Không có boss để join. Có activity khác -> True (thoát cho worker làm
        activity khác); chỉ có Join Boss -> chờ IDLE_WAIT giây rồi kiểm tra lại."""
        self.idle_scrolls = 0
        if self.exit_when_idle:
            return True
        delay(self.bot, IDLE_WAIT)
        self.next_screen = None   # ảnh giữ lại đã cũ sau khi chờ -> chụp lại
        return False

    def _scroll(self, screen):
        """Cuộn danh sách War: SCROLLS_EACH_WAY lần xuống rồi bấy nhiêu lần lên, rồi chụp ảnh cho vòng lặp
        kế tiếp. Đang ở đầu danh sách mà danh sách đã hiện hết thì không cần cuộn:
        mọi boss trên màn hình đều không tham gia -> rảnh ở vòng lặp kế tiếp."""
        bot = self.bot
        if self.swipe == 0 and self._list_fully_visible(screen):
            self.idle_scrolls = IDLE_SCROLLS
            return
        self.idle_scrolls += 1
        if self.swipe < SCROLLS_EACH_WAY:
            bot.swipe_percent(50, 65, 50, 40, duration=0.8)
        else:
            bot.swipe_percent(50, 40, 50, 65, duration=0.8)
        self.swipe = (self.swipe + 1) % (2 * SCROLLS_EACH_WAY)
        delay(bot, SCROLL_SETTLE)
        self.next_screen = bot.screenshot()

    @staticmethod
    def _list_fully_visible(screen) -> bool:
        """Dải ngay trên nút Battle Logs / Auto-Join trống (chỉ có nền tối) ->
        không còn thẻ rally nào bị che bên dưới."""
        h, w = screen.shape[:2]
        x0, y0, x1, y1 = LIST_END_REGION
        strip = screen[int(h * y0 / 100):int(h * y1 / 100), int(w * x0 / 100):int(w * x1 / 100)]
        return strip.size > 0 and int(strip.max()) < LIST_END_MAX_LIGHT

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
        """Màn hình March: chọn quân, hành quân. Chỉ khi màn hình March đóng lại
        sau khi tap hành quân thì boss vừa Join mới được nhớ là đã tham gia;
        mọi nhánh Back (thất bại) để boss đó được thử lại lần sau."""
        bot = self.bot
        coords, self.pending = self.pending, None
        if bot.find(BOSS_MONSTER, screen=screen, region=REGIONS[BOSS_MONSTER]) is None:
            bot.back()
            return

        # Chọn preset troop, xoay vòng qua các preset được chọn
        troop = self.troops[self.troop_index % len(self.troops)]
        self.troop_index += 1
        for _ in range(5):
            bot.tap_percent(troop * 11, 11)
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
                self.memory.mark(coords, MEMORY_JOINED)
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

    def _join(self, screen) -> bool:
        """Tap nút Join của boss đầu tiên cần tham gia; True nếu đã tap."""
        bot = self.bot
        jw, jh = bot.template_size(JOIN)
        
        # 1. Tìm các nút Join hợp lệ trong dải Y
        points = [p for p in bot.find_all(JOIN, threshold=JOIN_THRESHOLD, screen=screen, center=False,
                                          region=REGIONS[JOIN])
                  if JOIN_MIN_Y < p[1] < JOIN_MAX_Y]
        # Nút "Joined" (đã tham gia) cũng chứa chữ "Join": bỏ điểm Join nằm đè lên nó
        joined = bot.find_all(JOINED_BUTTON, screen=screen, center=False, region=REGIONS[JOINED_BUTTON])
        points = [p for p in points
                  if not any(abs(p[0] - jx) < JOINED_OVERLAP and abs(p[1] - jy) < JOINED_OVERLAP
                             for jx, jy in joined)]
        
        # 2. Lọc nhanh các nút đã xử lý trên màn hình hiện tại (Blacklist)
        points = [p for p in points if not _near(p, self.screen_blacklist)]

        if not points:
            self._scroll(screen)
            self.screen_blacklist.clear()
            return False

        for x, y in points:
            region = bot.crop(screen, x - 90, y - 150, 160, 190)
            coords = None

            # 3. Chỉ OCR nếu bật flag CAN_READ_COORDS
            if CAN_READ_COORDS:
                pin = bot.find(LOCATION, screen=region, center=False)
                if pin is not None:
                    lw, _ = bot.template_size(LOCATION)
                    coords = read_coords(bot.crop(region, pin[0] + lw, pin[1], 80, 15))

                    # Boss đã tham gia / đã bỏ qua (còn trong BossMemory) -> không kiểm tra nữa
                    if coords and self.memory.status(coords) is not None:
                        self.screen_blacklist.append((x, y))
                        continue
                    # Boss mới (dù sau đó Join hay không tham gia) -> đếm lại số lần cuộn
                    if coords:
                        self.idle_scrolls = 0

            # 4. OCR tên boss (kèm cấp): boss không được tích ở tab, hoặc chữ Join đỏ
            #    -> nhớ là không tham gia
            if not self._boss_is_wanted(screen, x, y, coords) or self._join_text_is_red(screen, x, y, jh):
                self.memory.mark(coords, MEMORY_SKIPPED)
                self.screen_blacklist.append((x, y))
                continue

            # 5. Tap nút Join; boss chỉ được nhớ là đã tham gia khi hành quân xong (_march)
            bot.report_boss(coords)
            bot.tap(x + jw // 2, y + jh // 2)
            self.pending = coords
            self.screen_blacklist.append((x, y))
            self.idle_scrolls = 0   # cả khi không đọc được tọa độ
            return True
        return False

    def _boss_is_wanted(self, screen, x, y, coords) -> bool:
        """Đọc nhãn tên "(Boss) [tier] <tên>" của thẻ có nút Join ở góc (x, y),
        tìm cấp (từ tier; không có tier thì từ lực của boss) và kiểm tra boss
        đó có được tích ở tab không. Tên / cấp không nhận ra = không tham gia."""
        if self.selected is None:
            return True
        bot = self.bot
        text = read_boss_name(bot.crop(screen, x + NAME_DX, y + NAME_DY, NAME_W, NAME_DH))
        boss, tier = boss_names.parse(text)
        level, power = boss_names.level(
            boss, tier, lambda: read_power(bot.crop(screen, x + POWER_DX, y + POWER_DY, POWER_W, POWER_DH)))
        wanted = boss_names.wanted(self.selected, boss, level)
        bot.log(f"Boss {coords}: {text!r}"
                f"{f' power {power:,}' if power else ''}"
                f" -> {boss.name if boss else 'không nhận ra'}"
                f"{f' lv {level}' if level else ''}: {'join' if wanted else 'không tham gia'}")
        return wanted

    def _join_text_is_red(self, screen, x, y, join_h) -> bool:
        """Tối ưu thuật toán đếm pixel đỏ: linh hoạt hơn với render đồ họa khác nhau."""
        crop = self.bot.crop(screen, x - 12, y + join_h - 3, 60, 20)
        b, g, r = crop[..., 0], crop[..., 1], crop[..., 2]
        # Hạ tiêu chuẩn Red xuống > 160 và G/B < 110 để tránh lệch màu giữa các máy giả lập
        return int(((r > 160) & (g < 110) & (b < 110)).sum()) > 5


# Nhãn tên boss so với góc trên-trái nút Join (đo trên 396x704, cả thẻ trên và thẻ dưới).
# Cao 30 px để lấy được tên dài xuống 2 dòng ("(Boss) Skeleton" / "Dragon": y-86..y-62);
# dừng ở y-60, trên biển "Boss Monster" (cũng chữ vàng, từ y-58).
NAME_DX, NAME_DY, NAME_W, NAME_DH = -95, -90, 168, 30
# Lực của boss (số bên phải thanh trên cùng của thẻ, sau biểu tượng kiếm).
POWER_DX, POWER_DY, POWER_W, POWER_DH = -18, -180, 75, 20   # số dài (147.5M) bắt đầu từ x-14

SCROLLS_EACH_WAY = 3                  # mỗi chu kỳ: 3 lần cuộn xuống rồi 3 lần cuộn lên
IDLE_SCROLLS = 2 * SCROLLS_EACH_WAY   # cuộn hết 1 chu kỳ (6 lần) mà không thấy boss mới -> rảnh
IDLE_WAIT = 5      # giây chờ khi rảnh mà chỉ chạy Join Boss
SCROLL_SETTLE = 0.5   # giây chờ danh sách dừng trôi sau khi vuốt, trước khi chụp
_WAIT = {"top_left": {LEAVE_ALLIANCE_POPUP}, "tolerance": SAME_SPOT}


def _near(point, points) -> bool:
    return any(abs(px - point[0]) < SAME_SPOT and abs(py - point[1]) < SAME_SPOT for px, py in points)


def _troops(value) -> list[int]:
    """'Troop 2' hoặc ['Troop 1', 'Troop 3'] -> [2] / [1, 3]; không đọc được thì [1]."""
    troops = []
    for text in value if isinstance(value, list) else [value]:
        try:
            troops.append(int(str(text).split()[-1]))
        except (IndexError, ValueError):
            pass
    return troops or [1]


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
