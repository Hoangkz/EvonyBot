"""
run.py — Activity "Join Monster War": tham gia các rally đánh boss của liên minh.

Mỗi vòng lặp chụp 1 ảnh, nhận diện đang ở màn hình nào (chỉ dò ảnh trong
vùng nhỏ nơi nó xuất hiện, nên rất nhẹ CPU) rồi xử lý:

1.   Màn hình chính: có icon listboss -> bấm vào danh sách War; không có (chỉ
     thấy nút Alliance) -> chờ tối đa 10s cho icon xuất hiện.
2.   Danh sách War: chọn nút Join đầu tiên join được — bỏ qua boss trong
     JoinBossNotParticipat/, rally có thời gian màu đỏ (không kịp) và rally đã
     xử lý. Không còn Join nào: nếu thẻ dưới cùng có mặt thì cuộn xuống xem
     tiếp, hết danh sách thì quay lên đầu và chờ tối đa 10s cho Join mới.
3.   Màn hình March: bấm preset troop đã cấu hình.
4.   Có ô chọn tướng -> chọn tướng đầu tiên; sau đó bấm March.
5.   Popup hết thể lực -> dùng item thể lực ("Use Stamina" = ALL / 100), hoặc
     kết thúc activity nếu "Use Stamina" = No.

Không có delay cố định: sau mỗi thao tác đều chờ tới khi màn hình kế tiếp
xuất hiện (wait_until), có giới hạn thời gian.
"""
import numpy as np

from ...common import click_images, exit_images, go_home, images_in, wait_until
from ...ocr import read_coords
from .constants import (ALLIANCE_HOME, BOSS_MONSTER, BOTTOM_CARD_Y, FULL, IDLE_WAIT, JOIN,
                        JOINED, LEAVE_ALLIANCE, LISTBOSS, LOCATION, MARCH, MAX_SCROLL,
                        NOT_JOIN_LIMIT, OUT_OF_STAMINA, PLUS, PVP_WAR, REGIONS, ROI_LIST,
                        ROI_TROOPS, S_BACK, S_GENERALS, S_HOME, S_LEAVE_ALLIANCE, S_LIST,
                        S_MARCH, S_STAMINA_LIST, S_STAMINA_POPUP, S_TAP, SAME_SPOT, SELECT,
                        SELECT_GENERAL, SKIP_DIR, STAMINA_ITEM, USE_STAMINA)


def run(bot, settings: dict):
    """`bot` là BotContext của thiết bị; `settings` là cấu hình của tab "Join Monster War"."""
    _Boss(bot, settings).run()


class _Boss:
    def __init__(self, bot, settings: dict):
        self.bot = bot
        self.troop = _troop(settings.get("troop"))          # số thứ tự preset troop (1, 2, 3...)
        self.use_stamina = settings.get("use_stamina")      # "ALL" / "100" / "No"
        self.skip_bosses = images_in(SKIP_DIR)              # ảnh boss không join
        self.not_join: list[tuple[int, int]] = []           # toạ độ boss đã xử lý, không join lại
        self.screen_blacklist: list[tuple[int, int]] = []   # nút Join đã xử lý (khi không đọc được toạ độ)
        self.scrolled = 0                                   # số lần đã cuộn xuống khỏi đầu danh sách
        # Popup chung: chỉ dò khi không nhận ra màn hình nào của flow.
        self.popups = ([(p, S_TAP) for p in click_images()]
                       + [(p, S_BACK) for p in exit_images()])

    def run(self):
        """Vòng lặp chính: chụp màn hình -> nhận diện -> xử lý, cho tới khi hết thể lực."""
        bot = self.bot
        while True:
            screen = bot.screenshot()
            kind, pos = self._classify(screen)
            if kind != S_LIST:
                # Rời danh sách -> vị trí nút trên màn hình không còn đúng.
                self.screen_blacklist.clear()
                self.scrolled = 0

            if kind == S_STAMINA_POPUP:
                # (5) Hết thể lực: không cho dùng item -> kết thúc activity.
                if self.use_stamina not in ("ALL", "100"):
                    return
                bot.tap(*pos)
                self._wait(lambda s: self._find(s, STAMINA_ITEM), 5)
            elif kind == S_STAMINA_LIST:
                self._use_stamina(screen)
            elif kind == S_MARCH:
                self._march(screen, pos)
            elif kind == S_GENERALS:
                # Kẹt ở danh sách tướng -> chọn tướng đầu tiên.
                self._pick_general(screen)
            elif kind == S_LIST:
                self._list(screen)
            elif kind == S_HOME:
                self._home(screen)
            elif kind == S_LEAVE_ALLIANCE:
                # Đóng popup rời liên minh rồi back ra.
                bot.tap(pos[0] + 40, pos[1] + 40)
                self._wait(lambda s: self._find(s, LEAVE_ALLIANCE) is None, 3)
                bot.back()
                self._wait_changed(screen)
            elif kind == S_TAP:
                bot.tap(*pos)
                self._wait_changed(screen)
            elif kind == S_BACK:
                bot.back()
                self._wait_changed(screen)
            else:
                # Không nhận ra màn hình nào -> về màn hình chính.
                go_home(bot, screen)
                self._wait(lambda s: self._classify(s)[0], 3)

    # ---- nhận diện màn hình ------------------------------------------------
    def _classify(self, screen):
        """(tên màn hình, vị trí ảnh nhận diện) hoặc (None, None)."""
        pos = self._find(screen, OUT_OF_STAMINA)
        if pos is not None:
            return S_STAMINA_POPUP, pos
        checks = (
            (STAMINA_ITEM, S_STAMINA_LIST),
            (MARCH, S_MARCH),
            (SELECT, S_GENERALS),
            (PVP_WAR, S_LIST),
            (ALLIANCE_HOME, S_HOME),
        )
        for path, kind in checks:
            pos = self._find(screen, path)
            if pos is not None:
                return kind, pos
        pos = self._find(screen, LEAVE_ALLIANCE, center=False)
        if pos is not None:
            return S_LEAVE_ALLIANCE, pos
        # Popup chung không biết trước vị trí -> dò cả màn hình (chỉ khi không nhận ra gì).
        for path, kind in self.popups:
            pos = self._find(screen, path, region=FULL)
            if pos is not None:
                return kind, pos
        return None, None

    # ---- (1) màn hình chính ------------------------------------------------
    def _home(self, screen):
        """Có icon listboss -> mở danh sách War; không có -> chờ tối đa 10s cho nó xuất hiện."""
        pos = self._find(screen, LISTBOSS)
        if pos is None:
            pos, screen = self._wait(lambda s: self._find(s, LISTBOSS),
                                     IDLE_WAIT, interval=1.0)
            if pos is None:
                return
        self.bot.tap(*pos)
        self._wait(lambda s: self._find(s, PVP_WAR), 5)

    # ---- (2) danh sách War ---------------------------------------------------
    def _list(self, screen):
        """Bấm Join rally đầu tiên join được; không có thì cuộn / chờ."""
        target = self._joinable(screen)
        if target is not None:
            center, corner, coords = target
            self._remember(coords, *corner)
            self.bot.tap(*center)
            # Chờ màn hình March (3); không lên thì vòng sau xét lại danh sách.
            self._wait(lambda s: self._find(s, MARCH), 5)
            return

        buttons = (self._find_all(screen, JOIN)
                   + self._find_all(screen, JOINED))
        bottom = screen.shape[0] * BOTTOM_CARD_Y / 100
        # Thẻ dưới cùng có mặt -> có thể còn rally bên dưới -> cuộn xuống xem tiếp.
        if any(y > bottom for _, y in buttons) and self.scrolled < MAX_SCROLL:
            if self._scroll(down=True, before=screen):
                self.scrolled += 1
                return
        # Danh sách trống / đã join hết / hết danh sách -> về đầu rồi chờ Join mới.
        if self.scrolled:
            self._scroll_to_top(screen)
        self._wait(self._joinable, IDLE_WAIT, interval=1.0)

    def _joinable(self, screen):
        """(tâm nút Join, góc trên-trái nút Join, toạ độ boss) của rally đầu
        tiên join được, hoặc None."""
        bot = self.bot
        jw, jh = bot.template_size(JOIN)
        for cx, cy in sorted(self._find_all(screen, JOIN), key=lambda p: p[1]):
            x, y = cx - jw // 2, cy - jh // 2           # góc trên-trái nút Join
            if _near((x, y), self.screen_blacklist):
                continue
            # Vùng thẻ rally chứa nút Join này (ảnh boss + toạ độ).
            region = bot.crop(screen, x - 90, y - 150, 160, 190)
            coords = self._coords(region)
            if coords is not None and coords in self.not_join:
                continue
            # Boss bị bỏ qua, hoặc thời gian đỏ (không kịp join) -> ghi nhớ và bỏ qua.
            skipped = any(bot.find(p, threshold=0.7, screen=region) is not None
                          for p in self.skip_bosses)
            if skipped or self._join_text_is_red(screen, x, y, jh):
                self._remember(coords, x, y)
                continue
            return (cx, cy), (x, y), coords
        return None

    def _coords(self, region):
        """Toạ độ boss (OCR ngay bên phải icon Location) trong thẻ rally, hoặc None."""
        pin = self.bot.find(LOCATION, screen=region, center=False)
        if pin is None:
            return None
        lw, _ = self.bot.template_size(LOCATION)
        return read_coords(self.bot.crop(region, pin[0] + lw, pin[1], 80, 15))

    def _remember(self, coords, x, y):
        """Ghi nhớ rally đã xử lý: theo toạ độ boss nếu đọc được, không thì theo vị trí nút."""
        if coords is not None:
            self.not_join = (self.not_join + [coords])[-NOT_JOIN_LIMIT:]
        else:
            self.screen_blacklist.append((x, y))

    def _join_text_is_red(self, screen, x, y, join_h) -> bool:
        """Thời gian màu đỏ bên dưới chữ Join nghĩa là rally này không kịp join."""
        crop = self.bot.crop(screen, x - 12, y + join_h - 3, 60, 20)
        b, g, r = crop[..., 0], crop[..., 1], crop[..., 2]
        # Đếm số pixel đỏ (R cao, G và B thấp); nhiều hơn 5 pixel thì coi là chữ đỏ.
        return int(((r > 180) & (g < 100) & (b < 100)).sum()) > 5

    def _scroll(self, down: bool, before) -> bool:
        """Cuộn danh sách 1 lần, chờ danh sách đứng yên. Trả về False nếu danh
        sách không đổi (đã tới cuối / đầu)."""
        if down:
            self.bot.swipe_percent(50, 70, 50, 40, duration=1.0)   # vuốt lên = cuộn xuống
        else:
            self.bot.swipe_percent(50, 40, 50, 70, duration=0.3)   # vuốt xuống = cuộn lên
        self.screen_blacklist.clear()
        after = self._settle(before)
        return _differs(self._crop(before, ROI_LIST), self._crop(after, ROI_LIST))

    def _scroll_to_top(self, screen):
        """Cuộn lên tới khi danh sách không đổi nữa (tối đa MAX_SCROLL lần)."""
        for _ in range(MAX_SCROLL):
            if not self._scroll(down=False, before=screen):
                break
            screen = self.bot.screenshot()
        self.scrolled = 0

    def _settle(self, previous):
        """Chờ danh sách ngừng trôi (2 ảnh liên tiếp gần như giống nhau, tối đa 3s)."""
        state = {"prev": self._crop(previous, ROI_LIST)}

        def still(s):
            cur = self._crop(s, ROI_LIST)
            same = not _differs(state["prev"], cur, 2.0)
            state["prev"] = cur
            return same

        return self._wait(still, 3)[1]

    # ---- (3, 4) màn hình March -------------------------------------------------
    def _march(self, screen, march_pos):
        """Chọn preset troop -> (chọn tướng nếu cần) -> March."""
        bot = self.bot
        if self._find(screen, BOSS_MONSTER) is None:
            # Không phải rally đánh boss -> thoát ra.
            bot.back()
            self._wait(lambda s: self._find(s, MARCH) is None, 3)
            return

        # (3) Bấm preset troop (mỗi preset cách nhau 11% chiều ngang), chờ khung quân đổi.
        before = self._crop(screen, ROI_TROOPS)
        bot.tap_percent(self.troop * 11, 11)
        _, screen = self._wait(lambda s: _differs(before, self._crop(s, ROI_TROOPS)), 2)

        # (4) Chưa có tướng -> chọn tướng đầu tiên trong danh sách.
        pos = self._find(screen, SELECT_GENERAL, threshold=0.8)
        if pos is not None:
            bot.tap(*pos)
            found, screen = self._wait(lambda s: self._find(s, SELECT), 5)
            if found is not None:
                screen = self._pick_general(screen)

        # Bấm March rồi chờ màn hình March đóng hoặc popup hết thể lực (5).
        bot.tap(*(self._find(screen, MARCH) or march_pos))
        done, _ = self._wait(lambda s: (self._find(s, OUT_OF_STAMINA) is not None
                                        or self._find(s, MARCH) is None), 5)
        if not done:
            # Không March được (VD: không đủ quân) -> thoát ra, vòng sau xét lại danh sách.
            bot.back()
            self._wait(lambda s: self._find(s, MARCH) is None, 3)

    def _pick_general(self, screen):
        """(4.1) Bấm Select của tướng trên cùng, chờ quay lại màn hình March. Trả về ảnh cuối."""
        selects = self._find_all(screen, SELECT)
        if not selects:
            return screen
        self.bot.tap(*min(selects, key=lambda p: p[1]))
        return self._wait(lambda s: self._find(s, MARCH), 5)[1]

    # ---- (5) thể lực ------------------------------------------------------------
    def _use_stamina(self, screen):
        """Use Item: tap item trên cùng, chọn số lượng ("ALL": nút ở 28.9 % / 71.6 %,
        "100": nút bên phải nút "+") rồi bấm Use, sau đó đóng danh sách."""
        bot = self.bot
        items = self._find_all(screen, STAMINA_ITEM)
        if items:
            bot.tap(*min(items, key=lambda p: p[1]))
            use, screen = self._wait(lambda s: self._find(s, USE_STAMINA), 5)
            if use is not None:
                if self.use_stamina == "ALL":
                    bot.tap_percent(28.9, 71.6, count=2)
                else:
                    # Chế độ "100": tap 2 lần vào nút ngay bên phải nút "+".
                    plus = self._find(screen, PLUS, center=False)
                    if plus is not None:
                        pw, _ = bot.template_size(PLUS)
                        bot.tap(plus[0] + pw, plus[1] + 5)
                        bot.tap(plus[0] + pw, plus[1] + 5)
                bot.tap(*use)
                self._wait(lambda s: self._find(s, USE_STAMINA) is None, 5)
        # Đóng danh sách item.
        bot.back()
        self._wait(lambda s: self._find(s, STAMINA_ITEM) is None, 5)

    # ---- tiện ích ------------------------------------------------------------------
    def _wait(self, check, timeout, interval=0.3):
        return wait_until(self.bot, check, timeout=timeout, interval=interval)

    def _wait_changed(self, screen, timeout=3):
        """Chờ màn hình khác đi so với `screen`."""
        before = self._crop(screen, FULL)
        self._wait(lambda s: _differs(before, self._crop(s, FULL)), timeout)

    def _crop(self, screen, roi):
        return self.bot.crop(screen, *_rect(screen, roi))

    def _find(self, screen, path, threshold=0.9, center=True, region=None):
        """Vị trí ảnh `path` (tâm, hoặc góc trên-trái nếu center=False) trong
        vùng REGIONS[path] (hoặc `region`), theo toạ độ màn hình; None nếu không thấy."""
        x, y, w, h = _rect(screen, region or REGIONS.get(path, FULL))
        pos = self.bot.find(path, threshold=threshold, center=center,
                            screen=self.bot.crop(screen, x, y, w, h))
        return None if pos is None else (pos[0] + x, pos[1] + y)

    def _find_all(self, screen, path):
        """Tâm mọi ảnh `path` trong vùng REGIONS[path], theo toạ độ màn hình."""
        x, y, w, h = _rect(screen, REGIONS.get(path, FULL))
        return [(px + x, py + y) for px, py in
                self.bot.find_all(path, threshold=0.8, screen=self.bot.crop(screen, x, y, w, h))]


def _rect(screen, roi):
    """Vùng `roi` (% x0, y0, x1, y1) -> (x, y, w, h) pixel trên `screen`."""
    h, w = screen.shape[:2]
    x0, y0, x1, y1 = roi
    return (int(w * x0 / 100), int(h * y0 / 100),
            int(w * (x1 - x0) / 100), int(h * (y1 - y0) / 100))


def _differs(a, b, threshold=8.0) -> bool:
    """Hai vùng ảnh khác nhau rõ rệt (chênh lệch trung bình mỗi pixel > threshold)."""
    if a.shape != b.shape:
        return True
    return float(np.mean(np.abs(a.astype(np.int16) - b.astype(np.int16)))) > threshold


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
