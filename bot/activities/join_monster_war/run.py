"""
run.py — Activity "Join Monster War" (port từ class Boss bên C#).

Mở danh sách War của liên minh và tham gia các rally đánh quái (boss): bấm
"Join" vào rally chưa tham gia, chọn preset troop đã cấu hình rồi March.
Bỏ qua rally của boss bị skip, hoặc rally có chữ đỏ dưới nút Join (không
join được); khi không còn rally nào để join thì cuộn danh sách. Mỗi vòng
lặp chụp 1 screenshot, tìm ảnh đầu tiên khớp (xét theo thứ tự trong list
`_targets`) rồi xử lý theo ảnh đó. Khi hết thể lực: dùng item thể lực
("Use Stamina" = ALL / 100), hoặc kết thúc activity nếu "Use Stamina" = No.
"""
import time

from ...common import click_images, delay, exit_images, find_first, go_home, wait_gone
from ...context import TEMPLATE_DIR
from ...ocr import read_coords
from .constants import (ALLIANCE, BACK, CERBERUS, CHECK_MARCHING, CHOOSE_DEVELOPMENT,
                        CHOOSE_FAVORITE, JB, JOIN,
                        JOIN_LIST, JOIN_MAX_Y, JOIN_MIN_Y, JOINED, LEAVE_ALLIANCE_POPUP, LOCATION,
                        MARCH, MARCH_SCREEN, NOT_JOIN_LIMIT, OUT_OF_STAMINA, PLUS, SAME_SPOT,
                        SCROLL, SELECT, SELECT_GENERAL, STAMINA_ITEM, TAP, TROOP_CHECK,
                        USE_STAMINA, VIKING_SUMMON)
from .support import buy_hammer, buy_stamina, crazy_eggs, speed_marching, viking


def run(bot, settings: dict):
    """`bot` là BotContext của thiết bị; `settings` là cấu hình của tab "Join Monster War"."""
    quantity = _number(settings.get("buy_stamina"))
    if quantity > 0:
        bot.log(f"Join Monster War: buy {quantity} stamina")
        buy_stamina(bot, quantity)
        settings["buy_stamina"] = "0"
    if settings.get("buy_hammer"):
        bot.log("Join Monster War: buy hammer")
        buy_hammer(bot)
        settings["buy_hammer"] = False
    _Boss(bot, settings).run()

class _Boss:
    def __init__(self, bot, settings: dict):
        self.bot = bot
        self.troop = _troop(settings.get("troop"))          # số thứ tự preset troop (1, 2, 3...)
        self.use_stamina = settings.get("use_stamina")   # "ALL" / "100" / "No"
        self.skipped_bosses = [CERBERUS] if settings.get("skip_cerberus") else []
        self.viking_enabled = bool(settings.get("viking"))
        self.crazy_hours = _hours(settings.get("crazy_eggs_time_check"))
        self.speed_seconds = _seconds(settings.get("speed_marching"))
        self.next_crazy = 0.0 if self.crazy_hours else float("inf")
        self.next_viking = time.monotonic() + 600 if self.viking_enabled else float("inf")
        self.not_join: list[tuple[int, int]] = []           # toạ độ boss đã xử lý, không join lại (C# settingboss.ListBossNotJoin)
        self.screen_blacklist: list[tuple[int, int]] = []   # vị trí nút Join đã xử lý trên màn hình hiện tại
        self.swipe = 0                                      # bộ đếm chu kỳ cuộn (0,1: xuống; 2,3: lên)
        self.previous = None                                # action của vòng lặp trước
        # Chỉ chọn general khi có đủ các ảnh template cần thiết.
        self.can_select_general = all(_exists(p) for p in (
            SELECT_GENERAL, CHOOSE_DEVELOPMENT, CHOOSE_FAVORITE, SELECT))
        # Chỉ đọc toạ độ boss (OCR) khi có ảnh icon Location.
        self.can_read_coords = _exists(LOCATION)

    def run(self):
        """Vòng lặp chính: chụp màn hình -> nhận diện -> xử lý, cho tới khi hết thể lực."""
        bot = self.bot
        targets = _targets(self.viking_enabled, self.speed_seconds > 0)
        screen = bot.screenshot()
        while True:
            now = time.monotonic()
            if now >= self.next_crazy:
                bot.log("Join Monster War: Crazy Eggs")
                detected_hours = crazy_eggs(bot)
                self.next_crazy = (time.monotonic() + detected_hours * 3600
                                   if detected_hours else float("inf"))
                screen = bot.screenshot()
                continue
            if now >= self.next_viking:
                bot.log("Join Monster War: Viking check")
                viking(bot)
                self.next_viking = time.monotonic() + 600
                screen = bot.screenshot()
                continue
            # Popup rời liên minh tap theo offset từ góc trên-trái của ảnh, nên lấy toạ độ góc.
            action, pos = find_first(bot, screen, targets, top_left={LEAVE_ALLIANCE_POPUP})
            # Vừa quay lại danh sách War (vòng trước ở màn khác) -> reset blacklist màn hình.
            if action == JOIN_LIST and self.previous != JOIN_LIST:
                self.screen_blacklist.clear()
            self.previous = action

            if action == OUT_OF_STAMINA:
                # Hết thể lực: không cho dùng item -> kết thúc activity.
                if self.use_stamina not in ("ALL", "100"):
                    return
                bot.tap(*pos)
                wait_gone(bot, targets, action, pos, **_WAIT)   # chờ mở danh sách item thể lực
                self._use_stamina()
            elif action == MARCH_SCREEN:
                # Đang ở màn hình March (sau khi bấm Join) -> chọn troop và xuất quân.
                self._march(screen, pos)
            elif action == JOIN_LIST:
                # Đang ở danh sách War -> tìm rally để join.
                self._join(screen)
            elif action == SCROLL:
                # Đang ở tab War nhưng chưa thấy nút Join -> cuộn danh sách.
                self._scroll()
            elif action == JOINED:
                # Rally hiện tại đã join rồi -> cuộn tiếp và dọn bớt not_join.
                self._scroll()
                self.not_join = [p for p in self.not_join if p[0] < 800 and p[1] < 800]
            elif action == VIKING_SUMMON:
                viking(bot)
                self.next_viking = time.monotonic() + 600
            elif action == CHECK_MARCHING:
                if not speed_marching(bot, self.speed_seconds):
                    self._scroll()
            elif action == ALLIANCE:
                bot.tap(pos[0] + 20, pos[1] - 10, delay=5)
            elif action == TAP:
                bot.tap(*pos)
            elif action == BACK:
                bot.back()
            elif action == LEAVE_ALLIANCE_POPUP:
                # Đóng popup rời liên minh rồi back ra.
                bot.tap(pos[0] + 40, pos[1] + 40)
                wait_gone(bot, targets, action, pos, **_WAIT)
                bot.back()
            else:
                # Không nhận ra màn hình nào -> về màn hình chính.
                go_home(bot, screen)

            # Chờ màn hình đổi (action vừa xử lý biến mất) rồi dùng ảnh cuối cho vòng sau.
            screen = wait_gone(bot, targets, action, pos, **_WAIT)


    def _scroll(self):
        """Cuộn danh sách War: xuống 2 lần, rồi lên 2 lần, cứ thế lặp lại."""
        if self.swipe < 2:
            self.bot.swipe_percent(50, 65, 50, 40, duration=1.0)   # vuốt lên = cuộn xuống
        else:
            self.bot.swipe_percent(50, 40, 50, 65, duration=1.0)   # vuốt xuống = cuộn lên
        self.swipe = (self.swipe + 1) % 4

    def _use_stamina(self):
        """Danh sách item thể lực (C# Data.Stamina): tap item trên cùng, chọn
        số lượng ("ALL": nút ở vị trí 28.9 % / 71.6 %, "100": nút bên phải
        nút "+") rồi bấm Use, sau đó đóng danh sách."""
        bot = self.bot
        # Sắp xếp theo toạ độ y để lấy item nằm trên cùng.
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
                # Chế độ "100": tap 2 lần vào nút ngay bên phải nút "+".
                plus = bot.find(PLUS, center=False)
                if plus is not None:
                    pw, _ = bot.template_size(PLUS)
                    bot.tap(plus[0] + pw, plus[1] + 5)
                    bot.tap(plus[0] + pw, plus[1] + 5)
            delay(bot, 2)
            bot.tap(*use)
        else:
            # Không có item thể lực nào -> đóng danh sách.
            bot.back()
        delay(bot, 2)
        bot.back()
        delay(bot, 2)

    # ---- màn hình March -----------------------------------------------
    def _march(self, screen, march_pos):
        """Màn hình March sau khi bấm Join: chọn preset troop rồi xuất quân."""
        bot = self.bot
        if bot.find(f"{JB}/bossMonster.png", screen=screen) is None:
            bot.back()      # không phải rally đánh quái -> thoát ra
            delay(bot, 2)
            return

        # Tap preset troop (mỗi preset cách nhau 11% chiều ngang), thử tối đa
        # 7 lần cho tới khi thấy dấu tick xác nhận đã chọn.
        for _ in range(7):
            bot.tap_percent(self.troop * 11, 11)
            delay(bot)
            if bot.find(TROOP_CHECK) is not None:
                break
        else:
            # Không chọn được troop -> thoát ra.
            bot.back()
            delay(bot, 2)
            return

        if self.can_select_general:
            self._select_general()

        # Bấm March (nếu không tìm lại được nút thì dùng vị trí cũ).
        pos = bot.find(MARCH)
        bot.tap(*(pos or march_pos))
        delay(bot)
        # Chờ màn hình March đóng; nếu không đóng thì back ra.
        for _ in range(5):
            if bot.find(TROOP_CHECK) is None:
                return
            delay(bot)
        bot.back()
        bot.back()
        delay(bot, 2)

    def _select_general(self):
        """Chọn general: Select General -> Development -> Favorite -> Select (tối đa 2 lần)."""
        bot = self.bot
        for _ in range(2):
            pos = bot.find(SELECT_GENERAL, threshold=0.7)
            if pos is None:
                return
            bot.tap(*pos)
            delay(bot, 2)
            # Lọc danh sách general: tab Development -> Favorite.
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
            # Chờ quay lại màn hình March.
            for _ in range(5):
                delay(bot, 1)
                if bot.find(MARCH) is not None:
                    break

    # ---- danh sách War ------------------------------------------------
    def _join(self, screen):
        """Danh sách War: bấm Join vào rally đầu tiên join được, nếu không có thì cuộn."""
        bot = self.bot
        jw, jh = bot.template_size(JOIN)
        # Tìm mọi nút Join nằm trong vùng danh sách (bỏ các nút ngoài khoảng y hợp lệ).
        points = [p for p in bot.find_all(JOIN, threshold=0.8, screen=screen, center=False)
                  if JOIN_MIN_Y < p[1] < JOIN_MAX_Y]
        # Bỏ các nút đã xử lý trước đó.
        points = [p for p in points
                  if not _near(p, self.not_join) and not _near(p, self.screen_blacklist)]
        if not points:
            self._scroll()
            self.screen_blacklist.clear()
            return

        for x, y in points:
            # Vùng thẻ rally chứa nút Join này (ảnh boss + toạ độ).
            region = bot.crop(screen, x - 90, y - 150, 160, 190)
            coords = None
            if self.can_read_coords:
                # Đọc toạ độ boss bằng OCR, ngay bên phải icon Location.
                pin = bot.find(LOCATION, screen=region, center=False)
                if pin is not None:
                    lw, _ = bot.template_size(LOCATION)
                    coords = read_coords(bot.crop(region, pin[0] + lw, pin[1], 80, 15))
                    if coords is None:
                        continue
                    # Boss này đã xử lý rồi -> bỏ qua.
                    if coords in self.not_join:
                        self.screen_blacklist.append((x, y))
                        continue

            # Boss nằm trong danh sách skip, hoặc chữ đỏ (không join được) -> ghi nhớ và bỏ qua.
            skipped = any(bot.find(path, threshold=0.7, screen=region) is not None
                          for path in self.skipped_bosses)
            if skipped or self._join_text_is_red(screen, x, y, jh):
                self._remember(coords, x, y)
                continue

            # Bấm vào tâm nút Join -> vòng lặp sau sẽ gặp màn hình March.
            bot.tap(x + jw // 2, y + jh // 2)
            self._remember(coords, x, y)
            break

        # Giới hạn độ dài not_join, chỉ giữ các phần tử mới nhất.
        self.not_join = self.not_join[-NOT_JOIN_LIMIT:]

    def _remember(self, coords, x, y):
        """Ghi nhớ rally đã xử lý: toạ độ boss (nếu đọc được) và vị trí nút trên màn hình."""
        if coords is not None:
            self.not_join.append(coords)
        self.screen_blacklist.append((x, y))

    def _join_text_is_red(self, screen, x, y, join_h) -> bool:
        """Chữ màu đỏ bên dưới nút Join nghĩa là rally này không join được."""
        crop = self.bot.crop(screen, x - 12, y + join_h - 3, 60, 20)
        b, g, r = crop[..., 0], crop[..., 1], crop[..., 2]
        # Đếm số pixel đỏ (R cao, G và B thấp); nhiều hơn 5 pixel thì coi là chữ đỏ.
        return int(((r > 180) & (g < 100) & (b < 100)).sum()) > 5

# Tham số chung cho wait_gone: cùng cách nhận diện như find_first ở vòng lặp chính.
_WAIT = {"top_left": {LEAVE_ALLIANCE_POPUP}, "tolerance": SAME_SPOT}


def _exists(path: str) -> bool:
    """Kiểm tra file ảnh template có tồn tại trong thư mục Images/ không."""
    return (TEMPLATE_DIR / path).exists()


def _near(point, points) -> bool:
    """`point` có nằm gần (trong phạm vi SAME_SPOT pixel) điểm nào trong `points` không."""
    return any(abs(px - point[0]) < SAME_SPOT and abs(py - point[1]) < SAME_SPOT
               for px, py in points)


def _troop(text) -> int:
    """"Troop 3" -> 3 (mặc định Troop 1 nếu chưa chọn)."""
    try:
        return int(str(text).split()[-1])
    except (IndexError, ValueError):
        return 1


def _number(value) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return 0


def _hours(value) -> int:
    text = str(value or "0").upper().rstrip("H")
    return _number(text)


def _seconds(value) -> int:
    text = str(value or "0").lower().rstrip("s")
    return _number(text)


def _targets(viking_enabled: bool = False,
             speed_enabled: bool = False) -> list[tuple[str, str]]:
    """Danh sách (ảnh, action) để nhận diện màn hình; ảnh đứng trước được ưu tiên hơn."""
    targets = [
        ("click/lencap.png", TAP),                          # popup lên cấp
        (f"{JB}/hettheluc.png", OUT_OF_STAMINA),            # hết thể lực
        (MARCH, MARCH_SCREEN),                              # màn hình March
        (JOIN, JOIN_LIST),                                  # danh sách War có nút Join
        (f"{JB}/Joined.png", JOINED),                       # rally đã join
        (f"{JB}/PvPWar.png", SCROLL),                       # tab War, chưa thấy nút Join
        (f"{JB}/checkChienTranh.png", SCROLL),
        ("Items/outLM.png", LEAVE_ALLIANCE_POPUP),          # popup rời liên minh
        (f"{JB}/chientranh.png", TAP),                      # nút tab Chiến tranh
        *[(path, BACK) for path in exit_images()],          # các nút thoát/đóng chung
        *[(path, TAP) for path in click_images()],          # các nút cần bấm chung
        (f"{JB}/listboss.png", TAP),                        # icon mở danh sách boss
        (f"{JB}/lienminh.png", ALLIANCE),                    # mở Alliance từ màn hình chính
    ]
    if speed_enabled:
        targets.insert(3, (f"{JB}/CheckMarching.png", CHECK_MARCHING))
    if viking_enabled:
        targets.insert(0, ("Viking/Summom.png", VIKING_SUMMON))
    return targets
