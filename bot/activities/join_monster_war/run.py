"""
run.py — Activity "Join Monster War" (Optimized for Multi-threading & Low CPU).
"""
import time

from ...common import click_images, delay, exit_images, find_first, go_home, wait_gone
from ...context import TEMPLATE_DIR
from ...ocr import read_boss_name, read_coords
from ...ocr.read_power import text as read_power_text
from . import boss_names
from .boss_memory import JOINED as MEMORY_JOINED
from .boss_memory import BossMemory
from .constants import (ALLIANCE_ICON, ASSISTANT_GENERAL, BACK, BOSS_MONSTER, CHOOSE_DEVELOPMENT,
                        FAVORITE_OFF, FAVORITE_ON,
                        GENERAL_SEARCH, IDLE, JB, JOIN, JOIN_LIST, JOIN_MAX_Y, JOIN_MIN_Y, MAIN_GENERAL,
                        JOIN_THRESHOLD, JOINED, JOINED_BUTTON, JOINED_OVERLAP, LEAVE_ALLIANCE_POPUP,
                        LIST_END_MAX_LIGHT, LIST_END_REGION, LISTBOSS, LOCATION, MARCH, MARCH_SCREEN,
                        NO_BOSS, NOT_ENOUGH_STAMINA, OUT_OF_STAMINA, PRESET_COUNT, PRESET_DX,
                        PRESET_LOCKED, PRESET_X0, PRESET_Y, PVP_WAR, REGIONS, SAME_SPOT, SCROLL, SELECT,
                        SELECT_GENERAL, STAMINA_ITEM_USE, STAMINA_REFILL_WAIT, STAMINA_SLIDER_END,
                        STAMINA_ADDED_WAIT, STAMINA_BASE, STAMINA_BAR_REGION, STAMINA_ITEM_MIN_SCORE, STAMINA_ITEM_REGION, STAMINA_ITEMS,
                        STAMINA_PLUS, STAMINA_PLUS_DELAY,
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
        self.memory: BossMemory = bot.boss_memory           # Tọa độ boss đã xác nhận tham gia (X, Y in-game)
        self.screen_blacklist: list[tuple[int, int]] = []   # Tọa độ nút Join đã qua xử lý trên screen hiện tại
        self.swipe = 0                                      # Vị trí trong chu kỳ cuộn (0-2: xuống; 3-5: lên)
        self.previous = None                                # Action của vòng lặp trước
        self.exit_when_idle = settings.get("exit_when_idle", False)  # Worker bật khi còn activity khác
        self.idle_scrolls = 0                               # Số lần cuộn liên tiếp mà không thấy boss mới
        self.next_screen = None                             # Ảnh mới nhất (sau khi cuộn / wait_gone), dùng cho vòng lặp kế tiếp
        self.war_taps = 0                                   # Số lần đã bấm bỏ tích ô "War" trong lượt chạy này
        if getattr(bot, "join_boss_perf", None) is None:
            bot.join_boss_perf = {}
        self.performance = bot.join_boss_perf               # giữ số liệu qua nhiều lượt worker gọi Join Boss

    def _perf(self, step: str, started: float, ok: bool) -> None:
        """Ghi thời gian thật của một bước để đo p50/p95/max trên MEmu."""
        elapsed = time.perf_counter() - started
        status = "OK" if ok else "TIMEOUT"
        if elapsed > STEP_TARGET:
            status = f"SLOW/{status}"
        elapsed_ms = elapsed * 1000
        self.bot.log(f"[PERF] {step}: {elapsed_ms:.0f} ms {status}")

        samples = self.performance.setdefault(step, [])
        samples.append(elapsed_ms)
        del samples[:-200]  # đủ cho thống kê gần đây nhưng không tăng bộ nhớ vô hạn
        if len(samples) % PERF_SUMMARY_EVERY == 0:
            ordered = sorted(samples)
            p50 = ordered[(len(ordered) - 1) // 2]
            p95 = ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))]
            self.bot.log(
                f"[PERF SUMMARY] {step}: n={len(samples)} p50={p50:.0f} ms "
                f"p95={p95:.0f} ms max={max(samples):.0f} ms"
            )

    def _poll_screen(self, step: str, predicate, timeout: float | None = None,
                     interval: float | None = None):
        """Chụp lại tới khi predicate đúng; thường xong <1 s, không quá 2 s.

        Trả ``(ảnh cuối, kết quả predicate)``. Dùng số lượt cố định để test có
        đồng hồ giả vẫn kiểm tra đúng timeout như khi chạy thật.
        """
        timeout = STEP_TIMEOUT if timeout is None else timeout
        interval = POLL_INTERVAL if interval is None else interval
        started = time.perf_counter()
        deadline = started + timeout
        shot = result = None
        attempts = max(1, int(timeout / interval + 0.999))
        for _ in range(attempts):
            delay(self.bot, interval)
            shot = self.bot.screenshot()
            result = predicate(shot)
            if result:
                self._perf(step, started, True)
                return shot, result
            if time.perf_counter() >= deadline:
                break
        self._perf(step, started, False)
        return shot, result

    def _wait_gone(self, targets, action, pos, step: str):
        started = time.perf_counter()
        screen = wait_gone(self.bot, targets, action, pos, **_WAIT)
        self._perf(step, started, screen is not None)
        return screen

    def _wait_after_join(self, targets) -> None:
        """Chờ Join mở màn kế tiếp; nếu vẫn ở list sau 2 s thì cho phép thử lại."""
        def changed(screen):
            action = find_first(self.bot, screen, targets,
                                top_left={LEAVE_ALLIANCE_POPUP}, regions=REGIONS)[0]
            return action if action not in (None, JOIN_LIST) else None

        shot, _ = self._poll_screen("join_to_next_screen", changed)
        self.next_screen = shot

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
            detect_started = time.perf_counter()
            action, pos = find_first(bot, screen, targets, top_left={LEAVE_ALLIANCE_POPUP}, regions=REGIONS)
            self._perf("detect_screen", detect_started, True)
            
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
                if self.use_stamina not in STAMINA_CHOICES:
                    bot.record("Join Monster War: hết thể lực, không dùng vật phẩm -> dừng Join Boss")
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
                # Không ngủ cố định: sau khi tap Join, kiểm tra trạng thái mới mỗi 0,2 s.
                # Nếu sau 2 s vẫn ở danh sách thì vòng sau được phép thử lại nút đó.
                if self._join(screen):
                    self._wait_after_join(targets)
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
                self._wait_gone(targets, action, pos, "close_leave_alliance_popup")
                bot.back()

            else:
                # Không nhận diện được màn hình: thường là hiệu ứng tạm (màn tối / thông báo sau
                # khi bấm Join) -> polling tối đa 2 giây; nhận ra được thì đi tiếp, không thì go_home
                # (go_home nhấn Back, có thể thoát khỏi danh sách War).
                shot, recognized = self._poll_screen(
                    "recognize_unknown_screen",
                    lambda image: find_first(bot, image, targets,
                                             top_left={LEAVE_ALLIANCE_POPUP},
                                             regions=REGIONS)[0],
                )
                if recognized is not None:
                    self.next_screen = shot
                else:
                    bot.record("Màn hình vẫn không nhận ra: go_home")
                    go_home(bot, shot)
                continue

            # Chờ hành động cũ biến mất; ảnh xác nhận đã chuyển màn được dùng luôn cho
            # vòng lặp mới (None = hết giờ mà màn hình chưa đổi -> vòng lặp tự chụp lại)
            self.next_screen = self._wait_gone(targets, action, pos, f"{action}_to_next_screen")

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
        shot, gone = self._poll_screen(
            "untick_war",
            lambda image: bot.find(WAR_TICKED, screen=image,
                                   region=REGIONS[WAR_TICKED]) is None,
        )
        if gone:
            self.next_screen = shot
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
        _, buttons = self._poll_screen(
            "open_stamina_items",
            lambda image: sorted(bot.find_all(STAMINA_ITEM_USE, screen=image,
                                              region=REGIONS[STAMINA_ITEM_USE]),
                                 key=lambda p: p[1]),
        )
        if not buttons:
            # Hết vật phẩm: Back 2 lần. Boss chưa được tham gia nên tuyệt đối không ghi JOINED;
            # lượt Join Boss sau có thể thử lại khi thể lực đã hồi.
            bot.record("Join Monster War: hết vật phẩm thể lực")
            bot.back(delay=1)
            bot.back(delay=1)
            self.idle_scrolls = IDLE_SCROLLS
            return
        bot.tap(*buttons[0])

        # Popup số lượng: 100 -> Use luôn; ALL -> bấm cuối thanh trượt (dùng hết) rồi Use
        shot, use = self._poll_screen(
            "open_stamina_amount",
            lambda image: bot.find(STAMINA_USE, screen=image, region=REGIONS[STAMINA_USE]),
        )
        if use is None:
            bot.back()
            return
        if self.use_stamina == "ALL":
            bot.tap_percent(*STAMINA_SLIDER_END)
            delay(bot, POLL_INTERVAL)
        elif self.use_stamina in STAMINA_MULTIPLES:
            self._add_stamina(shot, int(self.use_stamina))
        bot.tap(*use)
        bot.record(f"Join Monster War: dùng vật phẩm thể lực ({self.use_stamina})")

        # Popup đóng là tín hiệu vật phẩm đã được dùng; không chờ cố định 5 giây.
        self._poll_screen(
            "apply_stamina",
            lambda image: bot.find(STAMINA_USE, screen=image,
                                   region=REGIONS[STAMINA_USE]) is None,
            timeout=STAMINA_REFILL_WAIT,
        )
        bot.back()
        shot, march = self._poll_screen(
            "stamina_back_to_march",
            lambda image: bot.find(MARCH, screen=image, region=REGIONS[MARCH]),
        )
        if march is not None:
            coords = self._read_march_target_coords(shot) if CAN_READ_COORDS else None
            if CAN_READ_COORDS and coords is None:
                bot.record("Join Monster War: sau khi dùng thể lực không đọc được tọa độ đích; không March")
                bot.back()
                return
            self._press_march(coords, march, shot)

    def _add_stamina(self, shot, target: int):
        """Popup số lượng mở sẵn ở mốc 100 thể lực: bấm nút + thêm (target - 100) / `item`
        lần (item = thể lực mỗi vật phẩm), mỗi lần cách STAMINA_PLUS_DELAY, xong chờ
        STAMINA_ADDED_WAIT."""
        bot = self.bot
        item = _item_stamina(bot, shot)
        plus = bot.find(STAMINA_PLUS, screen=shot, region=STAMINA_BAR_REGION)
        if item is None or plus is None:
            bot.record(f"Join Monster War: không xác định được vật phẩm / nút + ({self.use_stamina}); dùng mốc 100")
            return
        times = max(target - STAMINA_BASE, 0) // item
        for _ in range(times):
            bot.tap(*plus)
            delay(bot, STAMINA_PLUS_DELAY)
        bot.log(f"Thể lực {target}: vật phẩm {item}, bấm + {times} lần")
        delay(bot, STAMINA_ADDED_WAIT)

    def _march(self, screen, march_pos):
        """Màn hình March: chọn quân, hành quân. Chỉ khi quay lại danh sách War
        sau khi tap hành quân thì boss vừa Join mới được nhớ là đã tham gia;
        mọi nhánh Back (thất bại) để boss đó được thử lại lần sau."""
        bot = self.bot
        if bot.find(BOSS_MONSTER, screen=screen, region=REGIONS[BOSS_MONSTER]) is None:
            bot.back()
            return

        # Tọa độ trên màn March là mục tiêu thật. Không so với tọa độ đọc ở danh sách:
        # nếu card dịch chuyển và bot mở một rally khác thì xử lý rally thực tế đang mở.
        coords = self._read_march_target_coords(screen) if CAN_READ_COORDS else None
        if CAN_READ_COORDS and coords is None:
            bot.record("Join Monster War: không đọc được tọa độ đích trên March; không March")
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

        self._press_march(coords, march_pos, screen)

    def _press_march(self, coords, march_pos=None, screen=None):
        """Bấm March và ghi JOINED khi game quay lại danh sách War.

        Popup hết thể lực được kiểm tra trước và không được tính là thành công. Sau khi dùng
        thể lực, `_use_stamina()` gọi lại hàm này nên lần March mới được kiểm tra bình thường.
        """
        bot = self.bot
        screen = screen if screen is not None else bot.screenshot()
        pos = bot.find(MARCH, screen=screen, region=REGIONS[MARCH]) or march_pos
        if pos is None:
            return

        bot.tap(*pos)

        def march_result(shot):
            # Không đủ thể lực: popup "Get more now?" đè lên màn March (nút March mờ vẫn khớp
            # ảnh mẫu) -> trả màn này cho vòng lặp chính xử lý OUT_OF_STAMINA.
            # Không giữ tọa độ cũ; sau khi dùng thể lực `_use_stamina()` sẽ OCR lại
            # mục tiêu đang hiện trên màn March trước khi bấm March lần nữa.
            if bot.find(NOT_ENOUGH_STAMINA, screen=shot) is not None:
                return OUT_OF_STAMINA

            # Chỉ coi thành công khi về danh sách War và thấy hàng Joined đúng tọa độ
            # mục tiêu thật đã đọc trên March. Thấy mỗi tab PvP War là chưa đủ.
            if bot.find(PVP_WAR, screen=shot, region=REGIONS[PVP_WAR]) is not None:
                if coords is not None and self._joined_target_visible(shot, coords):
                    return JOINED
            return None

        last_shot, result = self._poll_screen("march_to_result", march_result)
        if result == OUT_OF_STAMINA:
            self.next_screen = last_shot
            return
        if result == JOINED:
            self.next_screen = last_shot
            self.memory.mark(coords, MEMORY_JOINED)
            bot.record(f"Join Monster War: đã hành quân tới boss {coords}")
            return

        # Chỉ Back khi vẫn còn ở màn March. Nếu chuyển sang màn khác nhưng chưa về danh sách
        # War, giữ ảnh hiện tại cho vòng chính tự nhận diện và không ghi nhớ tọa độ.
        if (last_shot is not None
                and bot.find(PVP_WAR, screen=last_shot, region=REGIONS[PVP_WAR]) is not None):
            self.next_screen = last_shot
            bot.record(f"Join Monster War: đã về danh sách nhưng chưa thấy Joined đúng boss {coords}; không ghi nhớ")
        elif last_shot is not None and bot.find(MARCH, screen=last_shot, region=REGIONS[MARCH]) is not None:
            bot.back()
        else:
            self.next_screen = last_shot
            bot.record(f"Join Monster War: chưa quay lại danh sách War cho boss {coords}; không ghi nhớ")

    def _joined_target_visible(self, screen, coords) -> bool:
        """Danh sách War có hàng Joined mang đúng tọa độ mục tiêu vừa hành quân."""
        points = self.bot.find_all(JOINED_BUTTON, screen=screen, center=False,
                                   region=REGIONS[JOINED_BUTTON])
        return any(JOIN_MIN_Y < y < JOIN_MAX_Y
                   and self._read_card_coords(screen, x, y) == coords for x, y in points)

    def _read_march_target_coords(self, screen):
        """Đọc tọa độ mục tiêu bên phải màn March (bên trái là tọa độ người gọi rally)."""
        bot = self.bot
        width = screen.shape[1]
        pins = [point for point in bot.find_all(LOCATION, screen=screen, center=False)
                if point[0] > width // 2]
        if not pins:
            return None
        x, y = max(pins, key=lambda point: point[0])
        lw, _ = bot.template_size(LOCATION)
        coords = read_coords(bot.crop(screen, x + lw, y, 90, 18))
        if coords is None or not all(0 <= value <= MAX_MAP_COORD for value in coords):
            return None
        return coords

    def _read_card_coords(self, screen, x, y):
        """Đọc và kiểm tra tọa độ thẻ rally theo góc trên-trái nút Join/Joined."""
        bot = self.bot
        region = bot.crop(screen, x - 90, y - 150, 160, 190)
        pin = bot.find(LOCATION, screen=region, center=False)
        if pin is None:
            return None
        lw, _ = bot.template_size(LOCATION)
        coords = read_coords(bot.crop(region, pin[0] + lw, pin[1], 80, 15))
        if coords is None:
            return None
        if not all(0 <= value <= MAX_MAP_COORD for value in coords):
            bot.log(f"Bỏ tọa độ OCR không hợp lệ: {coords}")
            return None
        return coords

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
            bot.record(f"Join Monster War: đội quân đã chọn {self.troops} đều đang khoá ({locked} ô khoá)")
            return None
        for troop in usable:
            self.last_troop = troop   # đội đang được chọn trên màn March (nếu cần chọn tướng cho nó)
            bot.tap_percent(PRESET_X0 + (troop - 1) * PRESET_DX, PRESET_Y)
            _, found = self._poll_screen(
                f"select_troop_{troop}",
                lambda image: bot.find(GENERAL_SEARCH, screen=image,
                                       region=REGIONS[GENERAL_SEARCH]),
            )
            if found is not None:
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
        bot.tap(*plus)

        # Chờ màn "Select a General": nhận bằng trái tim lọc (luôn có, kể cả khi danh sách
        # trống "No favorite General" thì không có nút Select nào)
        screen, opened = self._poll_screen(
            f"open_{name}",
            lambda image: (bot.find(FAVORITE_ON, screen=image, region=REGIONS[FAVORITE_ON])
                           or bot.find(FAVORITE_OFF, screen=image, region=REGIONS[FAVORITE_OFF])),
        )
        if not opened:
            bot.record(f"Chọn {name}: không mở được màn Select a General")
            return False

        # Chỉ hiện tướng phát triển: bấm tab Development (không thấy cái búa = tab đang chọn sẵn)
        if self.development_general:
            hammer = bot.find(CHOOSE_DEVELOPMENT, screen=screen, region=REGIONS[CHOOSE_DEVELOPMENT])
            if hammer is not None:
                bot.tap(*hammer)
                screen, _ = self._poll_screen(
                    f"select_development_{name}",
                    lambda image: bot.find(CHOOSE_DEVELOPMENT, screen=image,
                                           region=REGIONS[CHOOSE_DEVELOPMENT]) is None,
                )

        # Chỉ hiện tướng yêu thích: trái tim lọc chưa tích thì bấm tích
        if bot.find(FAVORITE_ON, screen=screen, region=REGIONS[FAVORITE_ON]) is None:
            heart = bot.find(FAVORITE_OFF, screen=screen, region=REGIONS[FAVORITE_OFF])
            if heart is not None:
                bot.tap(*heart)
                screen, _ = self._poll_screen(
                    f"favorite_filter_{name}",
                    lambda image: bot.find(FAVORITE_ON, screen=image,
                                           region=REGIONS[FAVORITE_ON]),
                )

        # Chỉ nút Select màu xanh: tướng đang là tướng chính có nút xám (không chọn được làm
        # tướng phụ), nút xám vẫn khớp ảnh mẫu tới 0,88.
        buttons = sorted((p for p in bot.find_all(SELECT, screen=screen, region=REGIONS[SELECT])
                          if _is_green_button(screen, p)), key=lambda p: p[1])
        if not buttons:
            # Không có tướng yêu thích nào ("No favorite General"), hoặc chỉ còn tướng đang là
            # tướng chính (nút xám) -> quay về màn March
            bot.record(f"Chọn {name}: không có tướng nào để chọn")
            bot.back()
            self._poll_screen(
                f"back_from_{name}",
                lambda image: bot.find(MARCH, screen=image, region=REGIONS[MARCH]),
            )
            return False
        bot.tap(*buttons[0])

        # Quay về màn March, ô đã có tướng
        _, selected = self._poll_screen(
            f"confirm_{name}",
            lambda image: bot.find(GENERAL_SEARCH, screen=image, region=slot),
        )
        if selected is not None:
            bot.log(f"Đã chọn {name}")
            return True
        bot.record(f"Chọn {name}: chưa thấy tướng trong ô sau khi Select")
        return False

    def _join(self, screen) -> bool:
        """Tap nút Join của boss đầu tiên cần tham gia; True nếu đã tap."""
        bot = self.bot
        jw, jh = bot.template_size(JOIN)
        
        # 1. Tìm các nút Join hợp lệ trong dải Y
        points, _ = self._join_buttons(screen)
        
        # 2. Lọc nhanh các nút đã xử lý trên màn hình hiện tại, rồi duyệt ổn định từ trên
        # xuống dưới. find_all ưu tiên điểm khớp ảnh nên thứ tự gốc không phản ánh thứ tự thẻ.
        points = sorted((p for p in points if not _near(p, self.screen_blacklist)),
                        key=lambda p: (p[1], p[0]))

        if not points:
            self._scroll(screen)
            self.screen_blacklist.clear()
            return False

        for x, y in points:
            coords = None

            # 3. Chỉ OCR nếu bật flag CAN_READ_COORDS
            if CAN_READ_COORDS:
                coords = self._read_card_coords(screen, x, y)

                # Không có danh tính ổn định để tìm lại card. Bỏ nút này trong màn hiện tại
                # thay vì xóa blacklist và lặp vô hạn trên cùng một thẻ OCR lỗi.
                if coords is None:
                    bot.log(f"Không đọc được tọa độ card tại ({x}, {y}); bỏ qua trong màn hiện tại")
                    self.screen_blacklist.append((x, y))
                    continue

                # Chỉ JOINED dài hạn mới được chặn theo tọa độ. Không dùng SKIPPED dài hạn:
                # một lần OCR sai không được phép khóa nhầm boss hợp lệ trong 6 phút.
                if coords and self.memory.status(coords) == MEMORY_JOINED:
                    self.screen_blacklist.append((x, y))
                    continue

            # 4. Boss không được tích chỉ bị blacklist trên màn hình hiện tại. Sau khi cuộn hoặc
            # mở lại Join Boss, tên/cấp sẽ được OCR lại.
            if not self._boss_is_wanted(screen, x, y, coords):
                self.screen_blacklist.append((x, y))
                continue

            # 5. Thời gian dưới nút Join màu đỏ (VD vừa bấm Join mà không đủ đội quân) -> bỏ qua
            #    LẦN NÀY: không nhớ vào BossMemory (lần quét sau kiểm tra lại, hết đỏ thì Join),
            #    không đếm lại số lần cuộn (boss đỏ không giữ bot khỏi rảnh)
            if self._join_text_is_red(screen, x, y, jh):
                bot.log(f"Boss {coords}: thời gian đỏ, bỏ qua lần này")
                self.screen_blacklist.append((x, y))
                continue

            # 6. OCR phía trên có thể mất vài giây. Chụp một ảnh mới và tìm lại card đúng
            #    tọa độ trước khi tap. Nếu vẫn có race sau đó, màn March dùng tọa độ thật.
            target = self._stable_join_target(coords, (x, y), jh)
            if target is None:
                return False
            x, y = target

            # 7. Tap nút Join; boss chỉ được nhớ là đã tham gia khi hành quân xong (_march).
            #    Không đưa nút vào screen_blacklist: nếu bấm mà không vào được màn March (VD
            #    thông báo "You cannot send more troops.") thì lượt sau xét lại chính nút này
            #    (thời gian đỏ -> bỏ qua, không đỏ -> bấm Join lại), không bỏ sang Join khác.
            bot.report_boss(coords)
            bot.tap(x + jw // 2, y + jh // 2)
            self.idle_scrolls = 0   # cả khi không đọc được tọa độ
            return True
        return False

    def _join_buttons(self, screen):
        """Trả các nút Join thật và các nút Joined trên cùng một ảnh chụp."""
        bot = self.bot
        points = [p for p in bot.find_all(JOIN, threshold=JOIN_THRESHOLD, screen=screen,
                                          center=False, region=REGIONS[JOIN])
                  if JOIN_MIN_Y < p[1] < JOIN_MAX_Y]
        joined = bot.find_all(JOINED_BUTTON, screen=screen, center=False,
                              region=REGIONS[JOINED_BUTTON])
        points = [p for p in points
                  if not any(abs(p[0] - jx) < JOINED_OVERLAP and
                             abs(p[1] - jy) < JOINED_OVERLAP for jx, jy in joined)]
        return sorted(points, key=lambda p: (p[1], p[0])), joined

    def _stable_join_target(self, coords, old_point, join_h):
        """Tìm lại boss trên ảnh mới và chỉ trả vị trí còn ổn định ngay trước khi tap.

        Nếu rally bị chèn thêm/xóa đi giữa lúc OCR, vị trí cũ không còn được sử dụng.
        Khi danh sách tiếp tục đổi ở ảnh xác nhận thứ hai, vòng hiện tại bị hủy và ảnh
        mới nhất được đưa lại cho vòng lặp chính xử lý từ đầu.
        """
        bot = self.bot
        fresh = bot.screenshot()
        points, _ = self._join_buttons(fresh)

        if coords is not None:
            # Thử điểm gần vị trí cũ trước và dừng ngay khi tìm thấy A, tránh OCR toàn bộ
            # danh sách. Nếu card lại đổi sau ảnh này, màn March sẽ phát hiện tọa độ B.
            matches = []
            for point in sorted(points, key=lambda p: abs(p[0] - old_point[0]) +
                                abs(p[1] - old_point[1])):
                if self._read_card_coords(fresh, *point) == coords:
                    matches.append(point)
                    break
        elif CAN_READ_COORDS:
            # Không có danh tính để bảo đảm thẻ tại vị trí cũ vẫn là cùng một boss.
            matches = []
        else:
            # Chỉ dành cho bản thiếu template LOCATION: dùng vị trí gần nhất và kiểm tra
            # lại đầy đủ loại boss/timer trên ảnh mới thay vì tap tọa độ cũ một cách mù.
            matches = [point for point in points if _near(point, [old_point])]

        if not matches:
            bot.log(f"Boss {coords}: danh sách đã đổi trước khi Join, quét lại")
            self.next_screen = fresh
            self.screen_blacklist.clear()
            return None

        point = min(matches, key=lambda p: abs(p[0] - old_point[0]) + abs(p[1] - old_point[1]))
        if self._join_text_is_red(fresh, *point, join_h):
            bot.log(f"Boss {coords}: thời gian đã chuyển đỏ trước khi Join")
            self.next_screen = fresh
            self.screen_blacklist = [point]
            return None
        if coords is None and not self._boss_is_wanted(fresh, *point, coords):
            self.next_screen = fresh
            self.screen_blacklist = [point]
            return None

        return point

    def _join_text_is_red(self, screen, x, y, join_h) -> bool:
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
            boss, tier, lambda: read_power_text(bot.crop(screen, x + POWER_DX, y + POWER_DY, POWER_W, POWER_DH)))
        wanted = boss_names.wanted(self.selected, boss, level)
        bot.log(f"Boss {coords}: {text!r}"
                f"{f' power {power}' if power else ''}"
                f" -> {boss.name if boss else 'không nhận ra'}"
                f"{f' lv {level}' if level else ''}: {'join' if wanted else 'không tham gia'}")
        return wanted



# Nhãn tên boss so với góc trên-trái nút Join (đo trên 396x704, cả thẻ trên và thẻ dưới).
# Cao 30 px để lấy được tên dài xuống 2 dòng ("(Boss) Skeleton" / "Dragon": y-86..y-62);
# dừng ở y-60, trên biển "Boss Monster" (cũng chữ vàng, từ y-58).
NAME_DX, NAME_DY, NAME_W, NAME_DH = -95, -90, 168, 30
# Lực của boss (số bên phải thanh trên cùng của thẻ, sau biểu tượng kiếm).
POWER_DX, POWER_DY, POWER_W, POWER_DH = -18, -180, 85, 20   # số dài (147.5M) bắt đầu từ x-14

SCROLLS_EACH_WAY = 3                  # mỗi chu kỳ: 3 lần cuộn xuống rồi 3 lần cuộn lên
IDLE_SCROLLS = 2 * SCROLLS_EACH_WAY   # cuộn hết 1 chu kỳ (6 lần) mà không thấy boss mới -> rảnh
IDLE_WAIT = 2      # polling khi rảnh; không phải độ trễ của một thao tác UI
SCROLL_SETTLE = 0.5   # giây chờ danh sách dừng trôi sau khi vuốt, trước khi chụp
POLL_INTERVAL = 0.2     # kiểm tra sớm để đa số bước hoàn thành gần 1 giây
STEP_TARGET = 1.0       # quá mức này ghi SLOW trong log performance
STEP_TIMEOUT = 2.0      # không bước UI nào chờ lâu hơn 2 giây
PERF_SUMMARY_EVERY = 10 # mỗi 10 mẫu in p50/p95/max của bước đó
MAX_MAP_COORD = 2000    # chặn kết quả OCR tọa độ hỏng rõ ràng; cố ý rộng hơn mọi map đang dùng
_WAIT = {"top_left": {LEAVE_ALLIANCE_POPUP}, "tolerance": SAME_SPOT,
         "timeout": STEP_TIMEOUT, "interval": POLL_INTERVAL}


STAMINA_MULTIPLES = ("200", "300", "400", "500")     # thể lực muốn nhận; popup mở sẵn ở mốc 100
STAMINA_CHOICES = ("ALL", "100", *STAMINA_MULTIPLES)


def _item_stamina(bot, screen) -> int | None:
    """Thể lực mỗi vật phẩm (10 / 25 / 50 / 100) của popup số lượng đang mở, nhận theo số vàng
    trên biểu tượng. Thử từ lớn xuống nhỏ vì số "10" nằm trong số "100" (khớp 0,99)."""
    for amount, template in STAMINA_ITEMS.items():
        if bot.find(template, threshold=STAMINA_ITEM_MIN_SCORE, screen=screen,
                    region=STAMINA_ITEM_REGION):
            return amount
    return None


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
