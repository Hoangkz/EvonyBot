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
from .constants import (ALLIANCE_ICON, ASSISTANT_GENERAL, BACK, BOSS_MONSTER, CHOOSE_DEVELOPMENT,
                        FAVORITE_OFF, FAVORITE_ON,
                        GENERAL_SEARCH, IDLE, JB, JOIN, JOIN_LIST, JOIN_MAX_Y, JOIN_MIN_Y, MAIN_GENERAL,
                        JOIN_THRESHOLD, JOINED, JOINED_BUTTON, JOINED_OVERLAP, LEAVE_ALLIANCE_POPUP,
                        LIST_END_MAX_LIGHT, LIST_END_REGION, LISTBOSS, LOCATION, MARCH, MARCH_SCREEN,
                        NO_BOSS, NOT_ENOUGH_STAMINA, OUT_OF_STAMINA, PRESET_COUNT, PRESET_DX,
                        PRESET_LOCKED, PRESET_X0, PRESET_Y, PVP_WAR, REGIONS, SAME_SPOT, SCROLL, SELECT,
                        SELECT_GENERAL, STAMINA_ITEM_USE, STAMINA_REFILL_WAIT, STAMINA_SLIDER_END,
                        STAMINA_USE, TAP, WAR_TAB, WAR_TICKED, WAR_UNTICK_TRIES)

# --- CACHE CHECKS TỒN TẠI FILE (Chạy 1 lần duy nhất khi import, không đọc ổ cứng liên tục) ---
def _check_exists(path: str) -> bool:
    return (TEMPLATE_DIR / path).exists()

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
        self.troops = _troops(settings.get("troop"))        # Các đội quân (preset 1-8) được chọn ở tab
        self.last_troop = None                              # Đội vừa bấm chọn trên màn March
        self.select_general = bool(settings.get("select_general"))            # Tích "Select General"
        self.select_assistant = bool(settings.get("select_assistant_general"))  # Tích "With Assistant General"
        self.development_general = bool(settings.get("development_general"))  # Tích "Development General"
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
            if action != self.previous:
                bot.log(f"Màn hình: {action or 'không nhận ra'}{f' tại {pos}' if pos else ''}")
            self.previous = action

            # Danh sách War mà ô "War" (rally đánh người chơi) đang tích -> bấm bỏ tích trước
            if self._on_war_list(screen, action) and self._untick_war(screen):
                continue

            if action == OUT_OF_STAMINA:
                # Không đủ thể lực: use_stamina = No -> dừng hẳn Join Boss
                if self.use_stamina not in ("ALL", "100"):
                    return
                bot.tap(*pos)
                self._use_stamina()
                continue   # _use_stamina đã March lại, hoặc (hết vật phẩm) đánh dấu rảnh

            elif action == NO_BOSS:
                # Th2: danh sách War (tab PvP War) không thấy nút Join / Joined nào trong dải hợp
                # lệ: có thể trống thật, hoặc đã cuộn tới đoạn toàn thẻ "Attacking" -> xử lý như
                # cuộn (_scroll: đầu danh sách mà đã hiện hết -> rảnh, còn thẻ bị che -> cuộn tiếp)
                if bot.find(PVP_WAR, screen=screen, region=REGIONS[PVP_WAR]) is not None:
                    self._scroll(screen)
                    continue
                # Th1: màn hình chính có Liên minh nhưng không có listboss -> rảnh
                if self._idle():
                    return IDLE
                continue   # màn hình không đổi -> không cần wait_gone

            elif action == MARCH_SCREEN:
                self._march(screen, pos)

            elif action == JOIN_LIST:
                # Đã tap Join: chờ cố định JOIN_TAP_WAIT giây rồi chụp lại (không wait_gone: nếu
                # không Join được thì nút Join vẫn còn, wait_gone sẽ chờ hết 10 giây).
                # Không tap (bỏ qua hết / đã cuộn): quét lại ngay.
                if self._join(screen):
                    delay(bot, JOIN_TAP_WAIT)
                continue

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
                # Không nhận diện được màn hình: thường là hiệu ứng tạm (màn tối / thông báo sau
                # khi bấm Join) -> chụp lại vài lần; nhận ra được thì đi tiếp, không thì go_home
                # (go_home nhấn Back, có thể thoát khỏi danh sách War).
                for _ in range(UNKNOWN_RETRIES):
                    delay(bot, 1)
                    shot = bot.screenshot()
                    if find_first(bot, shot, targets, top_left={LEAVE_ALLIANCE_POPUP},
                                  regions=REGIONS)[0] is not None:
                        self.next_screen = shot
                        break
                else:
                    bot.log("Màn hình vẫn không nhận ra: go_home")
                    go_home(bot, shot)
                continue

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
        self.bot.log("Rảnh: không còn boss để tham gia")
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
        bot.log(f"Cuộn {'xuống' if self.swipe < SCROLLS_EACH_WAY else 'lên'} ({self.idle_scrolls}/{IDLE_SCROLLS})")
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
        """Sau khi bấm Confirm ở popup không đủ thể lực: màn "Use Item" -> bấm nút Use đầu
        tiên (vật phẩm trên cùng) -> popup số lượng -> Use -> chờ, Back về màn March, March lại."""
        bot = self.bot
        buttons = []
        for _ in range(6):
            delay(bot, 0.5)
            buttons = sorted(bot.find_all(STAMINA_ITEM_USE, region=REGIONS[STAMINA_ITEM_USE]),
                             key=lambda p: p[1])
            if buttons:
                break
        if not buttons:
            # Hết vật phẩm thể lực: Back 2 lần (thoát màn Use Item, rồi màn March). Không dừng Join
            # Boss (thể lực tự hồi theo thời gian): nhớ boss này là đã tham gia để không thử lại
            # ngay, và coi như đang rảnh (worker làm activity khác / chờ rồi quét lại).
            bot.log("Hết vật phẩm thể lực")
            bot.back(delay=1)
            bot.back(delay=1)
            coords, self.pending = self.pending, None
            self.memory.mark(coords, MEMORY_JOINED)
            self.idle_scrolls = IDLE_SCROLLS
            return
        bot.tap(*buttons[0])

        # Popup số lượng: 100 -> Use luôn; ALL -> bấm cuối thanh trượt (dùng hết) rồi Use
        use = None
        for _ in range(6):
            delay(bot, 0.5)
            use = bot.find(STAMINA_USE, region=REGIONS[STAMINA_USE])
            if use is not None:
                break
        if use is None:
            bot.back()
            return
        if self.use_stamina == "ALL":
            bot.tap_percent(*STAMINA_SLIDER_END)
            delay(bot, 0.5)
        bot.tap(*use)
        bot.log(f"Dùng vật phẩm thể lực ({self.use_stamina})")

        # Chờ 5 giây, Back về màn March rồi bấm March lại (đội đã chọn giữ nguyên)
        delay(bot, STAMINA_REFILL_WAIT)
        bot.back()
        for _ in range(6):
            delay(bot, 0.5)
            if bot.find(MARCH, region=REGIONS[MARCH]) is not None:
                coords, self.pending = self.pending, None
                self._press_march(coords)
                return

    def _march(self, screen, march_pos):
        """Màn hình March: chọn quân, hành quân. Chỉ khi màn hình March đóng lại
        sau khi tap hành quân thì boss vừa Join mới được nhớ là đã tham gia;
        mọi nhánh Back (thất bại) để boss đó được thử lại lần sau."""
        bot = self.bot
        coords, self.pending = self.pending, None
        if bot.find(BOSS_MONSTER, screen=screen, region=REGIONS[BOSS_MONSTER]) is None:
            bot.back()
            return

        # Chọn đội quân (preset) có tướng chính, thử lần lượt các đội người dùng chọn.
        # Không đội nào có tướng chính thì VẪN tham gia boss với đội vừa thử cuối cùng:
        # - tab có tích "Select General": chọn tướng chính cho đội đó trước (chọn không
        #   được, VD không có tướng yêu thích, thì vẫn March);
        # - không tích: March luôn.
        # Chỉ bỏ (Back, boss được thử lại sau) khi mọi đội đã chọn đều đang khoá.
        if self._pick_troop(screen) is None:
            if self.last_troop is None:
                bot.back()
                return
            if not self.select_general:
                bot.log(f"Đội quân {self.last_troop}: không có tướng chính, vẫn tham gia boss")
            elif not self._choose_general(MAIN_GENERAL):
                bot.log(f"Đội quân {self.last_troop}: không chọn được tướng chính, vẫn tham gia boss")

        # Tích "With Assistant General": ô tướng phụ đang trống thì chọn luôn
        if self.select_general and self.select_assistant:
            self._choose_general(ASSISTANT_GENERAL)

        self._press_march(coords, march_pos)

    def _press_march(self, coords, march_pos=None):
        """Bấm March trên màn March rồi chờ màn đóng: đóng thì nhớ boss `coords` là đã tham
        gia; hiện popup không đủ thể lực thì để vòng lặp chính xử lý."""
        bot = self.bot
        pos = bot.find(MARCH, region=REGIONS[MARCH]) or march_pos
        if pos is None:
            return
        bot.tap(*pos, delay=MARCH_TAP_DELAY)

        # Chờ màn hình March đóng (nút March biến mất)
        for _ in range(5):
            delay(bot, 0.8)
            shot = bot.screenshot()
            # Không đủ thể lực: popup "Get more now?" đè lên màn March (nút March mờ vẫn khớp
            # ảnh mẫu) -> trả màn này cho vòng lặp chính xử lý OUT_OF_STAMINA; giữ tọa độ
            # boss để nếu hành quân được sau khi dùng thể lực thì vẫn nhớ là đã tham gia.
            if bot.find(NOT_ENOUGH_STAMINA, screen=shot) is not None:
                self.pending = coords
                self.next_screen = shot
                return
            if bot.find(MARCH, screen=shot, region=REGIONS[MARCH]) is None:
                self.memory.mark(coords, MEMORY_JOINED)
                return
        bot.back()

    def _pick_troop(self, screen) -> int | None:
        """Màn March: chọn đội quân (preset 1-8) dùng được, trả về số đội; None nếu không có.

        - Đội dùng được = đội người dùng chọn ở tab, trừ các ô đang khoá (đếm ổ khoá ở
          hàng preset; các ô mở luôn là các ô đầu).
        - Lần nào cũng thử lần lượt từ đội nhỏ nhất (VD chọn 1, 2, 3 -> luôn thử 1, 2, 3),
          không xoay vòng theo lần Join trước.
        - Một đội đạt khi chọn xong thấy kính lúp ở ô Main General (có tướng chính)."""
        bot = self.bot
        self.last_troop = None
        locked = len(bot.find_all(PRESET_LOCKED, screen=screen, region=REGIONS[PRESET_LOCKED]))
        usable = [t for t in self.troops if t <= PRESET_COUNT - locked]
        if not usable:
            bot.log(f"Đội quân đã chọn {self.troops} đều đang khoá ({locked} ô khoá)")
            return None
        for troop in usable:
            self.last_troop = troop   # đội đang được chọn trên màn March (nếu cần chọn tướng cho nó)
            bot.tap_percent(PRESET_X0 + (troop - 1) * PRESET_DX, PRESET_Y)
            for _ in range(3):
                delay(bot, 0.5)
                if bot.find(GENERAL_SEARCH, region=REGIONS[GENERAL_SEARCH]) is not None:
                    bot.log(f"Chọn đội quân {troop}")
                    return troop
        return None

    def _choose_general(self, slot) -> bool:
        """Chọn tướng cho ô `slot` (MAIN_GENERAL / ASSISTANT_GENERAL, vùng % trên màn March).
        True nếu ô đã có tướng (sẵn có, hoặc vừa chọn xong).

        Ô trống (dấu "+") -> bấm "+" -> màn "Select a General": tích "Development General" thì
        bấm tab Development (cái búa) -> trái tim lọc (chỉ hiện tướng yêu thích) chưa tích thì
        bấm tích -> bấm nút "Select" đầu tiên -> quay về màn March, ô đã có tướng (thấy kính
        lúp trong ô)."""
        bot = self.bot
        name = "tướng chính" if slot == MAIN_GENERAL else "tướng phụ"
        plus = bot.find(SELECT_GENERAL, region=slot)
        if plus is None:
            return bot.find(GENERAL_SEARCH, region=slot) is not None
        bot.tap(*plus, delay=GENERAL_TAP_DELAY)

        # Chờ màn "Select a General": nhận bằng trái tim lọc (luôn có, kể cả khi danh sách
        # trống "No favorite General" thì không có nút Select nào)
        for _ in range(6):
            delay(bot, 0.5)
            screen = bot.screenshot()
            if (bot.find(FAVORITE_ON, screen=screen, region=REGIONS[FAVORITE_ON]) is not None
                    or bot.find(FAVORITE_OFF, screen=screen, region=REGIONS[FAVORITE_OFF]) is not None):
                break
        else:
            bot.log(f"Chọn {name}: không mở được màn Select a General")
            return False

        # Chỉ hiện tướng phát triển: bấm tab Development (không thấy cái búa = tab đang chọn sẵn)
        if self.development_general:
            hammer = bot.find(CHOOSE_DEVELOPMENT, screen=screen, region=REGIONS[CHOOSE_DEVELOPMENT])
            if hammer is not None:
                bot.tap(*hammer)
                delay(bot, 1 + GENERAL_TAP_DELAY)
                screen = bot.screenshot()

        # Chỉ hiện tướng yêu thích: trái tim lọc chưa tích thì bấm tích
        if bot.find(FAVORITE_ON, screen=screen, region=REGIONS[FAVORITE_ON]) is None:
            heart = bot.find(FAVORITE_OFF, screen=screen, region=REGIONS[FAVORITE_OFF])
            if heart is not None:
                bot.tap(*heart)
                delay(bot, 1 + GENERAL_TAP_DELAY)
                screen = bot.screenshot()

        # Chỉ nút Select màu xanh: tướng đang là tướng chính có nút xám (không chọn được làm
        # tướng phụ), nút xám vẫn khớp ảnh mẫu tới 0,88.
        buttons = sorted((p for p in bot.find_all(SELECT, screen=screen, region=REGIONS[SELECT])
                          if _is_green_button(screen, p)), key=lambda p: p[1])
        if not buttons:
            # Không có tướng yêu thích nào ("No favorite General"), hoặc chỉ còn tướng đang là
            # tướng chính (nút xám) -> quay về màn March
            bot.log(f"Chọn {name}: không có tướng nào để chọn")
            bot.back(delay=GENERAL_TAP_DELAY)
            for _ in range(6):
                delay(bot, 0.5)
                if bot.find(MARCH, region=REGIONS[MARCH]) is not None:
                    break
            return False
        bot.tap(*buttons[0], delay=GENERAL_TAP_DELAY)

        # Quay về màn March, ô đã có tướng
        for _ in range(6):
            delay(bot, 0.5)
            if bot.find(GENERAL_SEARCH, region=slot) is not None:
                bot.log(f"Đã chọn {name}")
                return True
        bot.log(f"Chọn {name}: chưa thấy tướng trong ô sau khi Select")
        return False

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

            # 4. OCR tên boss (kèm cấp): boss mới không được tích ở tab -> nhớ là không tham gia,
            #    đếm lại số lần cuộn
            if not self._boss_is_wanted(screen, x, y, coords):
                if coords:
                    self.idle_scrolls = 0
                self.memory.mark(coords, MEMORY_SKIPPED)
                self.screen_blacklist.append((x, y))
                continue

            # 5. Thời gian dưới nút Join màu đỏ (VD vừa bấm Join mà không đủ đội quân) -> bỏ qua
            #    LẦN NÀY: không nhớ vào BossMemory (lần quét sau kiểm tra lại, hết đỏ thì Join),
            #    không đếm lại số lần cuộn (boss đỏ không giữ bot khỏi rảnh)
            if self._join_text_is_red(screen, x, y, jh):
                bot.log(f"Boss {coords}: thời gian đỏ, bỏ qua lần này")
                self.screen_blacklist.append((x, y))
                continue

            # 6. Tap nút Join; boss chỉ được nhớ là đã tham gia khi hành quân xong (_march).
            #    Không đưa nút vào screen_blacklist: nếu bấm mà không vào được màn March (VD
            #    thông báo "You cannot send more troops.") thì lượt sau xét lại chính nút này
            #    (thời gian đỏ -> bỏ qua, không đỏ -> bấm Join lại), không bỏ sang Join khác.
            bot.report_boss(coords)
            bot.tap(x + jw // 2, y + jh // 2)
            self.pending = coords
            self.idle_scrolls = 0   # cả khi không đọc được tọa độ
            return True
        return False

    def _join_text_is_red(self, screen, x, y, join_h) -> bool:
        print(f"Đếm pixel đỏ ở nút Join tại {x},{y} (cao {join_h})")
        """Tối ưu thuật toán đếm pixel đỏ: linh hoạt hơn với render đồ họa khác nhau.
        Chỉ lấy dòng chữ thời gian bên trong nút (dưới chữ "Join"): vùng rộng hơn trước đây
        chạm viền đỏ của thẻ bên dưới khi nút ở vị trí lệch (sau khi cuộn), bị nhận nhầm là
        thời gian đỏ. Đo: thời gian trắng 0 pixel đỏ, thời gian đỏ ~94."""
        crop = self.bot.crop(screen, x - 6, y + join_h, 46, 12)
        b, g, r = crop[..., 0], crop[..., 1], crop[..., 2]
        # Hạ tiêu chuẩn Red xuống > 160 và G/B < 110 để tránh lệch màu giữa các máy giả lập
        return int(((r > 160) & (g < 110) & (b < 110)).sum()) > 5

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
GENERAL_TAP_DELAY = 2   # giây chờ thêm sau mỗi lần bấm khi chọn tướng ("+", trái tim, Select, Back)
MARCH_TAP_DELAY = 2     # giây chờ sau khi bấm March, trước khi kiểm tra màn March đã đóng / popup thể lực
UNKNOWN_RETRIES = 3     # màn hình không nhận ra: chụp lại tối đa bấy nhiêu lần (mỗi lần 1 s) trước khi go_home
JOIN_TAP_WAIT = 3       # giây chờ sau khi tap Join (vào màn March, hoặc không Join được thì tap lại)
_WAIT = {"top_left": {LEAVE_ALLIANCE_POPUP}, "tolerance": SAME_SPOT}


def _is_green_button(screen, center) -> bool:
    """Nút ở `center` màu xanh lá (bấm được), không phải xám (bị khoá). Đo nút Select:
    xanh B,G,R ~ 36,80,45; xám ~ 69,75,75."""
    x, y = center
    patch = screen[max(y - 8, 0):y + 8, max(x - 40, 0):x + 40].astype(int)
    b, g, r = (patch[..., i].mean() for i in range(3))
    return g - r > 15 and g - b > 15


def _near(point, points) -> bool:
    return any(abs(px - point[0]) < SAME_SPOT and abs(py - point[1]) < SAME_SPOT for px, py in points)


def _troops(value) -> list[int]:
    """'Troop 2' hoặc ['Troop 3', 'Troop 1'] -> [2] / [1, 3] (tăng dần, không trùng);
    không đọc được thì [1]."""
    troops = set()
    for text in value if isinstance(value, list) else [value]:
        try:
            troops.add(int(str(text).split()[-1]))
        except (IndexError, ValueError):
            pass
    return sorted(troops) or [1]


def _targets() -> list[tuple[str, str]]:
    return [
        ("click/lencap.png", TAP),
        (NOT_ENOUGH_STAMINA, OUT_OF_STAMINA),
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
