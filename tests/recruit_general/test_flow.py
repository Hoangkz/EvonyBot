"""
Flow test activity Recruit General (bot/activities/recruit_general/): menu Tavern -> icon Recruit -> màn Recruit General ->
tích Historic General, bỏ tích Epic (Orange) General.

Ảnh trong screens/ chụp nguyên màn hình giả lập 396x704 (2026-10-16): 01 menu tròn của Tavern (nút "•••" vẫn hiện, Tavern ở
giữa), 02 màn Recruit General cả hai ô chưa tích, 03 cả hai ô đã tích. Ảnh "?hist" / "?epic_off" / "?both_off" ... là ảnh TỔNG HỢP:
dán ô tích từ ảnh 02 / 03 lên (chỉ đổi trạng thái hai ô, phần còn lại là ảnh thật).
"""
import importlib
import unittest
from pathlib import Path

from bot.activities import recruit_general
from bot.activities.recruit_general.constants import (CANCEL, CONFIRM, DETAIL_BUY_TOKEN, DETAIL_RECRUIT, LIST_USE, MENU_RECRUIT, POPUP_MAX, POPUP_USE,
                                                      REFRESH, REFRESH_MAX, REFRESH_WAIT)
from tests.flow import Step, end, run_flow, swipe, tap, tap_at, tap_pct

SCREENS = Path(__file__).parent / "screens"
EPIC_BOX = (28, 572, 56, 598)       # x0, y0, x1, y1 của hai ô tích trên màn Recruit General
HISTORIC_BOX = (210, 572, 238, 598)
HISTORIC_PCT = (56.6, 83)
EPIC_PCT = (10.6, 83)
CITY_MAP = {"tavern": [0, 0], "keep": [97, -231]}   # có route trong DB (nhánh quét không chạy)


def _paste(dst_name, box_src_name, box):
    """Hàm biến thể: dán ô `box` của ảnh `box_src_name` lên ảnh đích."""
    import cv2
    src = cv2.imread(str(SCREENS / box_src_name))
    x0, y0, x1, y1 = box

    def apply(img):
        img[y0:y1, x0:x1] = src[y0:y1, x0:x1]
        return img
    return apply


def _both(*pastes):
    def apply(img):
        for p in pastes:
            img = p(img)
        return img
    return apply


VARIANTS = {
    # từ 02 (cả hai chưa tích): Historic đã tích
    "hist": _paste("", "03_recruit_both_checked.png", HISTORIC_BOX),
    # từ 03 (cả hai đã tích): Epic bỏ tích
    "epic_off": _paste("", "02_recruit_unchecked.png", EPIC_BOX),
}
VARIANTS["right"] = VARIANTS["hist"]   # dùng với 02: Historic tích, Epic chưa tích (đúng trạng thái cần)


def _setup(ctx):
    ctx.city_map = dict(CITY_MAP)


class DotColors(unittest.TestCase):
    """Thanh chấm màu 6 tướng: màu từng chấm, chỉ tím và vàng được quan tâm."""

    @staticmethod
    def _shot(name):
        import cv2
        return cv2.imread(str(SCREENS / name))

    def test_colors(self):
        from bot.activities.recruit_general.run import dot_colors
        unch = self._shot("02_recruit_unchecked.png")
        both = self._shot("03_recruit_both_checked.png")
        popup = self._shot("04_high_quality_popup.png")   # ảnh bị popup làm mờ
        self.assertEqual(dot_colors(unch), ["blue", "blue", "blue", "green", "blue", "green"])
        self.assertEqual(dot_colors(both), ["purple", "blue", "blue", "green", "green", "green"])
        self.assertEqual(dot_colors(popup), ["green", "white", "blue", "gold", "blue", "green"])


class DotCount(unittest.TestCase):
    """Số chấm 3..6 (tài khoản yếu chỉ có 3 tướng): bố cục căn giữa, nhận ra số chấm; ảnh tổng hợp = ảnh thật 03 xoá hết chấm cũ rồi vẽ lại."""

    # BGR của chấm (lấy từ ảnh thật) và viền vàng của tướng đang hiện
    PALETTE = {"blue": (255, 170, 20), "green": (30, 190, 40), "white": (225, 225, 225), "purple": (255, 60, 255), "gold": (40, 180, 255)}
    RING = (30, 200, 255)

    def _image(self, colors, shown):
        import cv2
        import numpy as np
        image = cv2.imread(str(SCREENS / "03_recruit_both_checked.png"))
        mask = np.zeros(image.shape[:2], np.uint8)
        mask[452:482, 120:280] = 255
        image = cv2.inpaint(image, mask, 3, cv2.INPAINT_TELEA)       # xoá 6 chấm cũ (và vương miện)
        n, centre, spacing = len(colors), 198, 21.2
        for i, name in enumerate(colors):
            x = round(centre + (i - (n - 1) / 2) * spacing)
            if i == shown:
                cv2.circle(image, (x, 467), 6, self.RING, 1)
            cv2.circle(image, (x, 467), 3, self.PALETTE[name], -1)
        return image

    def test_three_to_six_dots(self):
        from bot.activities.recruit_general.run import dot_colors, dot_xs, shown_slot
        cases = [
            (["blue", "green", "white"], 1),                                              # tài khoản yếu: 3 chấm
            (["white", "blue", "purple", "green"], 3),                                    # 4 chấm
            (["blue", "blue", "gold", "green", "white"], 2),                              # 5 chấm
            (["green", "blue", "blue", "purple", "white", "gold"], 0),                    # 6 chấm
        ]
        for colors, shown in cases:
            image = self._image(colors, shown)
            self.assertEqual(len(dot_xs(image)), len(colors), colors)
            self.assertEqual(dot_colors(image), colors)
            self.assertEqual(shown_slot(image), shown, colors)

    def test_real_three_four_five_generals(self):
        """Ảnh THẬT tài khoản chưa mở đủ tướng (chữ "Unlocked Generals: n/6"): số chấm = n, đúng màu, đúng tướng đang hiện."""
        import cv2
        from bot.activities.recruit_general.run import dot_colors, dot_xs, shown_slot
        expected = {
            "12_three_generals.png": ([177, 198, 219], ["green", "blue", "white"], 1),                    # 3/6
            "13_four_generals.png": ([166, 187, 209, 230], ["green", "blue", "white", "green"], 1),       # 4/6
            "14_five_generals.png": ([156, 177, 198, 219, 240], ["green", "blue", "white", "green", "white"], 1),   # 5/6
        }
        for name, (xs, colors, shown) in expected.items():
            image = cv2.imread(str(SCREENS / name))
            self.assertEqual(dot_xs(image), xs, name)
            self.assertEqual(dot_colors(image), colors, name)
            self.assertEqual(shown_slot(image), shown, name)

    def test_no_dots(self):
        import cv2
        import numpy as np
        from bot.activities.recruit_general.run import dot_xs, shown_slot
        image = cv2.imread(str(SCREENS / "03_recruit_both_checked.png"))
        mask = np.zeros(image.shape[:2], np.uint8)
        mask[452:482, 120:280] = 255
        image = cv2.inpaint(image, mask, 3, cv2.INPAINT_TELEA)
        self.assertEqual(dot_xs(image), [])
        self.assertIsNone(shown_slot(image))


class CrownedSlots(unittest.TestCase):
    """Vương miện = tướng xịn (có thể 2 tướng); viền vàng quanh chấm = tướng đang hiện."""

    def test_crowns_and_shown(self):
        import cv2
        from bot.activities.recruit_general.run import crowned_slots, shown_slot
        from bot.context import TEMPLATE_DIR

        class Bot:   # chỉ cần find(path, screen, threshold, region) như BotContext
            @staticmethod
            def find(path, screen, threshold, region):
                h, w = screen.shape[:2]
                x0, y0, x1, y1 = (int(region[0] * w / 100), int(region[1] * h / 100), int(region[2] * w / 100), int(region[3] * h / 100))
                result = cv2.matchTemplate(screen[y0:y1, x0:x1], cv2.imread(str(TEMPLATE_DIR / path)), cv2.TM_CCOEFF_NORMED)
                return True if float(result.max()) >= threshold else None

        shot = lambda name: cv2.imread(str(SCREENS / name))
        expected = {
            "02_recruit_unchecked.png": ([], 2),            # tướng thường (chấm xanh): không vương miện
            "03_recruit_both_checked.png": ([0], 0),        # tím + vương miện
            "04_high_quality_popup.png": ([3], 3),          # vàng + vương miện (ảnh mờ)
            "07_after_recruit.png": ([4], 4),               # tím + vương miện, tím khác không vương miện
            "08_two_generals.png": ([0, 4], 4),             # HAI tướng xịn: tím (slot 1) và vàng (slot 5, đang hiện)
            "09_rustam.png": ([], 1),                       # đang hiện là chấm TRẮNG; có chấm tím nhưng không vương miện
            "10_arminius.png": ([1], 1),                    # vàng + vương miện, đang hiện
            "15_five_crowned.png": ([2], 2),                # 5 chấm, tím + vương miện; váy tướng có viền thêu vàng ngay trên chấm 1, 2 (không phải vương miện)
            "11_barrack.png": ([1], 3),                     # vương miện ở chấm vàng 2 KHÔNG đang hiện; đang hiện là chấm XANH LÁ (slot 4)
        }
        for name, (crowns, shown) in expected.items():
            self.assertEqual(crowned_slots(Bot, shot(name)), crowns, name)
            self.assertEqual(shown_slot(shot(name)), shown, name)


class SwitchGeneral(unittest.TestCase):
    """Kéo ảnh tướng sang trái / phải tới tướng khác (logic, bot giả: ảnh không đổi thật nên mock shown_slot)."""

    class Bot:
        """Bot giả: mỗi lần kéo, ảnh màn hình đổi sang khung nhiễu mới sau `delay_polls` lần chụp (None = không bao giờ đổi)."""

        def __init__(self, delay_polls=0):
            import numpy as np
            rng = np.random.default_rng(1)
            self.frames = [rng.integers(0, 255, (704, 396, 3), dtype=np.uint8) for _ in range(40)]
            self.index, self.delay_polls, self.pending = 0, delay_polls, None
            self.swipes, self.logs, self.slept = [], [], 0

        def screenshot(self):
            if self.pending is not None:
                self.pending -= 1
                if self.pending <= 0:
                    self.index, self.pending = self.index + 1, None
            return self.frames[self.index]

        def swipe_percent(self, *args, delay=0):
            self.swipes.append(args)
            if self.delay_polls is not None:
                self.pending = self.delay_polls + 1

        def sleep(self, seconds):
            self.slept += seconds

        def log(self, message):
            self.logs.append(message)

        record = log

    def _run(self, slots, fn, *args):
        """Chạy fn(bot, *args) với shown_slot trả lần lượt `slots`; trả (kết quả, bot)."""
        from unittest import mock
        module = importlib.import_module("bot.activities.recruit_general.run")
        bot = self.Bot()
        def swipe(bot, swipe):   # chỉ ghi lần kéo (phần chờ ảnh đổi được test riêng)
            bot.swipe_percent(*swipe)
            return True
        with mock.patch.object(module, "shown_slot", side_effect=list(slots)),                 mock.patch.object(module, "_swipe_until_changed", side_effect=swipe),                 mock.patch.object(module, "_wait_emblem", return_value=True):
            return getattr(module, fn)(bot, *args), bot

    def test_swipe_done_when_shown_dot_moves(self):
        """Chỉ cần chấm đang hiện đổi vị trí là đủ (không xét ảnh tướng, hai tướng giống nhau cũng được): chấm 4 -> 3 sau 2 lần kiểm tra."""
        from unittest import mock
        from bot.activities.recruit_general.constants import SWIPE_LEFT
        module = importlib.import_module("bot.activities.recruit_general.run")
        bot = self.Bot(delay_polls=None)   # ảnh không bao giờ đổi
        with mock.patch.object(module, "shown_slot", side_effect=[4, 4, 3]):   # trước khi kéo: 4; lần 1 vẫn 4; lần 2 đã sang 3
            self.assertTrue(module._swipe_until_changed(bot, SWIPE_LEFT))
        self.assertEqual(bot.slept, 2)
        self.assertEqual(len(bot.swipes), 1)

    def test_swipe_dot_unchanged_gives_up_after_8s(self):
        """Chấm đang hiện không đổi: chờ đủ 8 giây rồi trả False (người gọi kéo lại)."""
        from unittest import mock
        from bot.activities.recruit_general.constants import SWIPE_CHANGE_WAIT, SWIPE_LEFT
        module = importlib.import_module("bot.activities.recruit_general.run")
        bot = self.Bot(delay_polls=None)
        with mock.patch.object(module, "shown_slot", return_value=4):
            self.assertFalse(module._swipe_until_changed(bot, SWIPE_LEFT))
        self.assertEqual(bot.slept, SWIPE_CHANGE_WAIT)
        self.assertEqual(SWIPE_CHANGE_WAIT, 8)

    def test_swipe_unknown_dot_before_swipe_does_not_wait(self):
        """Không đọc được chấm đang hiện trước khi kéo: chờ 1 giây rồi xong (người gọi đọc lại)."""
        from unittest import mock
        from bot.activities.recruit_general.constants import SWIPE_LEFT
        module = importlib.import_module("bot.activities.recruit_general.run")
        bot = self.Bot(delay_polls=None)
        with mock.patch.object(module, "shown_slot", return_value=None):
            self.assertTrue(module._swipe_until_changed(bot, SWIPE_LEFT))
        self.assertEqual(bot.slept, 1)

    def test_goto_slot_swipes_left_first(self):
        from bot.activities.recruit_general.constants import SWIPE_LEFT
        ok, bot = self._run([0, 1, 2, 3], "_goto_slot", 3)   # tướng đang hiện đi 0 -> 1 -> 2 -> 3
        self.assertTrue(ok)
        self.assertEqual(bot.swipes, [SWIPE_LEFT] * 3)

    def test_goto_slot_swipes_right_for_target_on_the_left(self):
        from bot.activities.recruit_general.constants import SWIPE_RIGHT
        ok, bot = self._run([4, 3, 2, 1, 0], "_goto_slot", 0)   # đích bên trái: kéo sang phải ngay lần đầu
        self.assertTrue(ok)
        self.assertEqual(bot.swipes, [SWIPE_RIGHT] * 4)

    def test_goto_slot_flips_direction(self):
        from bot.activities.recruit_general.constants import SWIPE_LEFT, SWIPE_RIGHT
        ok, bot = self._run([2, 1, 2, 3], "_goto_slot", 3)   # kéo trái: 2 -> 1 (xa hơn) -> đổi hướng phải: 2 -> 3
        self.assertTrue(ok)
        self.assertEqual(bot.swipes, [SWIPE_LEFT, SWIPE_RIGHT, SWIPE_RIGHT])

    def _handle(self, crowned, shown, names, settings=None):
        """Chạy _handle_generals với: các chấm có vương miện `crowned`, tướng đang hiện `shown` (dãy các lần đọc), `names` (kết quả
        _wanted_general lần lượt). Trả (số tướng mua, danh sách đích _goto_slot, mock _buy)."""
        from unittest import mock
        module = importlib.import_module("bot.activities.recruit_general.run")
        names = iter(names)
        with mock.patch.object(module, "crowned_slots", return_value=crowned),                 mock.patch.object(module, "dot_colors", return_value=["purple", "blue", "gold", "green", "purple", "white"]),                 mock.patch.object(module, "shown_slot", side_effect=list(shown) + [shown[-1]] * 20),                 mock.patch.object(module, "_wanted_general", side_effect=lambda bot, wanted: next(names)),                 mock.patch.object(module, "_buy", return_value=True) as buy,                 mock.patch.object(module, "_goto_slot", return_value=True) as goto:
            bought = module._handle_generals(self.Bot(), settings or {})
        return bought, [c.args[1] for c in goto.call_args_list], buy

    def test_handle_two_generals_checks_shown_first(self):
        """HAI tướng xịn (slot 1 và 5, đang hiện slot 5): kiểm tra tướng đang hiện trước, rồi kéo sang tướng kia; tên cần mua thì mua."""
        bought, gotos, buy = self._handle([0, 4], [4], [None, "Frederick the Great"], {"buy_with": "Buy General Token"})
        self.assertEqual(bought, 1)
        self.assertEqual(gotos, [0])
        self.assertEqual(buy.call_args.args[1:], ("Frederick the Great", "Buy General Token", False))

    def test_handle_keeps_swiping_after_buying(self):
        """Mua tướng đang hiện xong vẫn kéo tiếp sang tướng xịn còn lại."""
        bought, gotos, buy = self._handle([0, 4], [4], ["X", "Y"])
        self.assertEqual(bought, 2)
        self.assertEqual(buy.call_count, 2)
        self.assertEqual(gotos, [0])

    def test_handle_shown_not_crowned_skips_it(self):
        """Tướng đang hiện (slot 3) không có vương miện: không kiểm tra tên nó, kéo thẳng tới tướng có vương miện."""
        bought, gotos, buy = self._handle([0, 4], [2], ["X", None])
        self.assertEqual(gotos, [0, 4])   # gần slot 3 trước: slot 1 (cách 2) và slot 5 (cách 2): giữ thứ tự theo số chấm

    def test_handle_no_crown_visits_nothing(self):
        from unittest import mock
        module = importlib.import_module("bot.activities.recruit_general.run")
        with mock.patch.object(module, "crowned_slots", return_value=[]):
            bot = self.Bot()
            self.assertEqual(module._handle_generals(bot, {}), 0)
        self.assertEqual(bot.swipes, [])


class Emblem(unittest.TestCase):
    """Huy hiệu bên trái tên tướng xịn (có vương miện): chờ nó hiện sau khi kéo tới."""

    @staticmethod
    def _bot(shot):
        import cv2
        from bot.context import TEMPLATE_DIR

        class Bot:
            slept = 0

            @staticmethod
            def find(path, threshold, region):
                h, w = shot.shape[:2]
                x0, y0, x1, y1 = (int(region[0] * w / 100), int(region[1] * h / 100), int(region[2] * w / 100), int(region[3] * h / 100))
                score = float(cv2.matchTemplate(shot[y0:y1, x0:x1], cv2.imread(str(TEMPLATE_DIR / path)), cv2.TM_CCOEFF_NORMED).max())
                return True if score >= threshold else None

            @classmethod
            def sleep(cls, seconds):
                cls.slept += seconds

            @staticmethod
            def log(message):
                pass
        return Bot

    def test_emblem_shown_on_crowned_general(self):
        import cv2
        module = importlib.import_module("bot.activities.recruit_general.run")
        for name in ("03_recruit_both_checked.png", "04_high_quality_popup.png"):   # tím sáng, vàng mờ
            bot = self._bot(cv2.imread(str(SCREENS / name)))
            self.assertTrue(module._wait_emblem(bot), name)
            self.assertEqual(bot.slept, 0)

    def test_no_emblem_waits_then_continues(self):
        import cv2
        module = importlib.import_module("bot.activities.recruit_general.run")
        bot = self._bot(cv2.imread(str(SCREENS / "02_recruit_unchecked.png")))   # tướng thường: không huy hiệu
        self.assertFalse(module._wait_emblem(bot))
        self.assertEqual(bot.slept, 3)


class BuyWait(unittest.TestCase):
    """Sau khi bấm vào tướng: chờ 1 giây / lần, mất nút Refresh = ra màn chi tiết -> mua; còn Refresh thì chờ tới tối đa 8 giây."""

    class Bot:
        def __init__(self, refresh_script, how_to_get=(), full=False):
            self.script, self.slept, self.taps, self.logs, self.backs = list(refresh_script), 0, [], [], 0
            self.full = full   # popup hết chỗ tướng đang hiện
            self.how = list(how_to_get)   # lần lượt: màn "How to get" có hiện sau khi bấm nút mua không (hết dãy = không)

        def tap_percent(self, *args, **kwargs):
            self.taps.append(("pct",) + args)

        def tap(self, *args, **kwargs):
            self.taps.append(("tap",) + args)

        def sleep(self, seconds):
            self.slept += seconds

        def screenshot(self):
            return object()

        def find(self, path, screen=None, threshold=0.8, region=None):
            if path.endswith("Refresh.png"):
                return (10, 10) if (self.script.pop(0) if self.script else False) else None
            if path.endswith("GeneralsFull.png"):
                return (50, 50) if self.full else None
            return (50, 50)   # nút ở màn chi tiết: DetailRecruit / DetailBuyToken (kiểu hai nút)

        def wait_for(self, path, timeout=10, threshold=0.8, interval=0.5):
            if path.endswith("HowToGetTitle.png"):
                shown = self.how.pop(0) if self.how else False
                if not shown:
                    self.slept += timeout   # chờ hết thời gian mà không thấy
                return (50, 50) if shown else None
            return (50, 50)   # nút mua của màn chi tiết (sau khi mở vàng)

        def back(self, delay=0):
            self.backs += 1

        def log(self, message):
            self.logs.append(message)

        record = log

    def test_detail_opens_after_one_second(self):
        module = importlib.import_module("bot.activities.recruit_general.run")
        bot = self.Bot([False, True, True])    # sau 1 giây mất Refresh (ra chi tiết); sau khi bấm mua: không thấy How to get, thấy Refresh (đã về); chờ danh sách 1 giây
        self.assertTrue(module._buy(bot, "X"))
        self.assertEqual(bot.slept, 1 + 1 + 1 + 2)   # chi tiết + chờ How to get + chờ danh sách + 2 giây chờ game load lại dữ liệu
        self.assertEqual(bot.backs, 0)
        self.assertEqual(bot.taps[0], ("pct", 50, 40))
        self.assertEqual(len(bot.taps), 2)   # bấm tướng + bấm nút mua

    def test_waits_more_while_refresh_visible(self):
        module = importlib.import_module("bot.activities.recruit_general.run")
        bot = self.Bot([True, True, False, True, True])   # còn Refresh 2 lần, lần 3 mất; sau khi mua về ngay
        self.assertTrue(module._buy(bot, "X"))
        self.assertEqual(bot.slept, 3 + 1 + 1 + 2)

    def test_waits_for_list_after_buy(self):
        """Sau khi mua: chờ 1 giây / lần để về danh sách (thấy Refresh); về sau 4 giây thì không Back."""
        module = importlib.import_module("bot.activities.recruit_general.run")
        bot = self.Bot([False, True, False, False, False, True])
        self.assertTrue(module._buy(bot, "X"))
        self.assertEqual(bot.slept, 1 + 1 + 4 + 2)
        self.assertEqual(bot.backs, 0)

    def test_back_when_list_never_returns(self):
        """Sau khi mua, 10 giây vẫn chưa về danh sách: bấm Back."""
        module = importlib.import_module("bot.activities.recruit_general.run")
        bot = self.Bot([False, True] + [False] * 10)
        self.assertTrue(module._buy(bot, "X"))
        self.assertEqual(bot.slept, 1 + 1 + 10 + 2)
        self.assertEqual(bot.backs, 1)

    def test_gives_up_after_8s(self):
        module = importlib.import_module("bot.activities.recruit_general.run")
        bot = self.Bot([True] * 8)
        self.assertFalse(module._buy(bot, "X"))
        self.assertEqual(bot.slept, 8)
        self.assertEqual(len(bot.taps), 1)   # chỉ bấm vào tướng, không bấm nút mua


    def test_generals_full_popup_stops(self):
        """Sau khi bấm mua hiện popup "You can only have up to N Generals" (nút Confirm giữa màn): dừng activity, không bấm Confirm / Back."""
        module = importlib.import_module("bot.activities.recruit_general.run")
        bot = self.Bot([False], full=True)
        with self.assertRaises(module.GeneralsFull):
            module._buy(bot, "X")
        self.assertEqual(len(bot.taps), 2)   # bấm tướng + bấm nút mua, không bấm Confirm
        self.assertEqual(bot.backs, 0)

    def test_not_enough_gold_without_open_gold_stops(self):
        """Bấm nút mua ra màn How to get (thiếu vàng), tab không tích Open Gold: Back hai lần về danh sách rồi NotEnoughGold (dừng activity)."""
        module = importlib.import_module("bot.activities.recruit_general.run")
        bot = self.Bot([False, True], how_to_get=[True])
        with self.assertRaises(module.NotEnoughGold):
            module._buy(bot, "X", open_gold=False)
        self.assertEqual(bot.backs, 2)
        self.assertEqual(len(bot.taps), 2)   # bấm tướng + bấm nút mua, không mở vàng

    def test_not_enough_gold_with_open_gold_opens_and_buys_again(self):
        """Thiếu vàng + tích Open Gold: mở hết vàng, Back về chi tiết, bấm mua lại; đủ vàng thì mua xong."""
        from unittest import mock
        module = importlib.import_module("bot.activities.recruit_general.run")
        bot = self.Bot([False, True, True], how_to_get=[True, False])   # lần bấm đầu: How to get; lần bấm lại: không còn (đã mua, về danh sách)
        with mock.patch.object(module, "_open_all_gold", return_value=3) as opened:
            self.assertTrue(module._buy(bot, "X", open_gold=True))
        opened.assert_called_once()
        self.assertEqual(bot.backs, 1)       # How to get -> màn chi tiết
        self.assertEqual(len(bot.taps), 3)   # bấm tướng + nút mua + nút mua lại

    def test_still_not_enough_gold_after_opening_stops(self):
        """Đã mở hết vàng mà bấm mua lại vẫn ra How to get: Back về danh sách rồi NotEnoughGold."""
        from unittest import mock
        module = importlib.import_module("bot.activities.recruit_general.run")
        bot = self.Bot([False, True], how_to_get=[True, True])
        with mock.patch.object(module, "_open_all_gold", return_value=3):
            with self.assertRaises(module.NotEnoughGold):
                module._buy(bot, "X", open_gold=True)
        self.assertEqual(bot.backs, 3)       # How to get -> chi tiết, rồi hai lần Back về danh sách


class GeneralsFullFlow(unittest.TestCase):
    def test_full_popup_stops_the_activity_on_a_real_screen(self):
        """Ảnh thật 20 (popup hết chỗ tướng sau khi bấm mua): activity trả False, không thao tác gì thêm."""
        module = importlib.import_module("bot.activities.recruit_general.run")
        flow = [
            Step("04_high_quality_popup.png", tap(CANCEL)),
            Step("03_recruit_both_checked.png?epic_off", tap_pct(50, 40)),
            Step("05_general_detail.png", tap(DETAIL_RECRUIT)),
            Step("20_generals_full.png", end(result=False)),
        ]
        device = run_flow(self, recruit_general.run, SCREENS, flow, {"generals": ["Frederick the Great"]}, setup=_setup, variants=VARIANTS)
        self.assertTrue(any("General limit is reached" in line for line in device.logs))


class OpenAllGold(unittest.TestCase):
    """Màn "How to get": bấm Use từng rương (ảnh thật 16 danh sách, 17 popup đã ở tối đa = nút "Minimum", 18 popup chưa tối đa = nút "Max",
    19 danh sách không còn nút Use)."""

    def _run(self, flow):
        module = importlib.import_module("bot.activities.recruit_general.run")
        return run_flow(self, lambda ctx, _s: module._open_all_gold(ctx), SCREENS, flow, {}, setup=_setup, variants=VARIANTS)

    def test_no_use_button_means_no_gold(self):
        """Không thấy nút Use nào: hết vàng, dừng ngay (không bấm gì)."""
        self._run([Step("19_how_to_get_empty.png", end(result=0))])

    def test_popup_at_max_presses_use(self):
        """Bấm Use -> popup đã ở tối đa (nút trái "Minimum"): bấm Use trong popup luôn; về danh sách không còn Use thì dừng."""
        flow = [
            Step("16_how_to_get_list.png", tap(LIST_USE)),
            Step("17_gold_popup_minimum.png", tap(POPUP_USE)),
            Step("19_how_to_get_empty.png", end(result=1)),
        ]
        self._run(flow)

    def test_popup_not_at_max_presses_max_first(self):
        """Popup chưa ở tối đa (nút trái "Max"): bấm Max (nút đổi thành "Minimum") rồi mới bấm Use."""
        flow = [
            Step("16_how_to_get_list.png", tap(LIST_USE)),
            Step("18_gold_popup_max.png", tap(POPUP_MAX)),
            Step("17_gold_popup_minimum.png", tap(POPUP_USE)),
            Step("19_how_to_get_empty.png", end(result=1)),
        ]
        self._run(flow)

    def test_single_item_has_no_popup(self):
        """Chỉ có một rương: bấm Use không hiện popup, danh sách đổi (không còn Use) = đã dùng."""
        flow = [
            Step("16_how_to_get_list.png", tap(LIST_USE)),
            Step("19_how_to_get_empty.png", end(result=1)),
        ]
        self._run(flow)

    def test_use_that_does_nothing_is_skipped(self):
        """Bấm Use mà màn không đổi, không popup: bỏ qua nút đó, thử nút kế; thử hết bốn nút thì dừng (không lặp mãi)."""
        flow = [Step("16_how_to_get_list.png", tap(LIST_USE)) for _ in range(4)] + [Step("16_how_to_get_list.png", end(result=0))]
        self._run(flow)


class OcrName(unittest.TestCase):
    """OCR tên tướng (bot/ocr/read_general_name.py) trên dải tên của ảnh thật, và so khớp một phần tên."""

    @classmethod
    def setUpClass(cls):
        cls.ocr = importlib.import_module("bot.ocr.read_general_name")

    def _read(self, screen):
        import cv2
        image = cv2.imread(str(SCREENS / screen))
        return self.ocr.run(image[478:512, 99:297])

    def test_reads_names_of_every_colour(self):
        for screen, name in [("02_recruit_unchecked.png", "hong fu nu"), ("03_recruit_both_checked.png", "frederick the great"),
                             ("09_rustam.png", "rustam"), ("10_arminius.png", "arminius"), ("11_barrack.png", "barrack"),
                             ("15_five_crowned.png", "constance i")]:
            self.assertEqual(self._read(screen), name, screen)

    def test_no_name_bar_reads_none(self):
        """Popup làm mờ màn (không còn thanh tên sáng): không đọc ra chữ."""
        self.assertIsNone(self._read("04_high_quality_popup.png"))

    def test_similarity_part_of_the_name_is_enough(self):
        s = self.ocr.similarity
        self.assertGreaterEqual(s("?athanael", "Nathanael Greene"), 0.5)   # thiếu chữ đầu
        self.assertGreaterEqual(s("nathanael", "Nathanael Greene"), 0.99)  # chỉ một phần tên
        self.assertGreaterEqual(s("witch siegei", "Witch Siegel"), 0.99)   # i / l là một chữ
        self.assertGreaterEqual(s("casimir pulaski", "Casimir Pulaski (old name: Robert Lee)"), 0.99)   # bỏ phần trong ngoặc

    def test_similarity_rejects_other_names_and_short_reads(self):
        s = self.ocr.similarity
        self.assertEqual(s("rustam", "Frederick the Great"), 0.0)
        self.assertEqual(s("ee", "Nathanael Greene"), 0.0)   # khớp dưới 3 chữ
        self.assertEqual(s("???", "Nero"), 0.0)
        self.assertEqual(s(None, "Nero"), 0.0)
        self.assertGreater(s("queen boudica", "Queen Boudica"), s("queen boudica", "Queen Victoria"))

    def test_unknown_letters_are_logged_once(self):
        """Tên OCR có "?": lưu ảnh dải tên vào logs/generals (mỗi tên một lần mỗi lần chạy)."""
        import tempfile
        from unittest import mock

        import numpy as np
        module = importlib.import_module("bot.activities.recruit_general.run")
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(module, "LOGS_DIR", Path(tmp)), mock.patch.object(module, "_logged", set()):
            strip = np.zeros((34, 198, 3), np.uint8)
            module._log_unknown("hattoi nin?a", strip)
            module._log_unknown("hattoi nin?a", strip)
            module._log_unknown("rustam", strip)   # không có "?": không lưu
            self.assertEqual(sorted(p.name for p in Path(tmp).iterdir()), ["hattoi_ninxa.png", "unknown.logs"])
            self.assertEqual(len((Path(tmp) / "unknown.logs").read_text(encoding="utf-8").splitlines()), 1)


class RecruitGeneralFlow(unittest.TestCase):
    def test_open_recruit_and_set_boxes(self):
        """Menu Tavern -> Recruit -> màn Recruit General (cả hai chưa tích): tích Historic, Epic để nguyên."""
        flow = [
            Step("01_tavern_menu.png", tap_at(198, 345, tol=80)),               # bấm Tavern
            Step("01_tavern_menu.png", tap(MENU_RECRUIT)),                       # icon Recruit
            Step("02_recruit_unchecked.png", tap_pct(*HISTORIC_PCT)),            # tích Historic
            Step("02_recruit_unchecked.png?right", tap(REFRESH)),
            Step("01_tavern_menu.png", end(result=True)),   # rời màn Recruit General (popup...): dừng Refresh
        ]
        run_flow(self, recruit_general.run, SCREENS, flow, {}, setup=_setup, variants=VARIANTS)

    def test_epic_checked_gets_unchecked(self):
        """Đã ở màn Recruit General, cả hai đã tích: chỉ bỏ tích Epic."""
        flow = [
            Step("03_recruit_both_checked.png", tap_pct(*EPIC_PCT)),
            Step("03_recruit_both_checked.png?epic_off", tap(REFRESH)),
            Step("01_tavern_menu.png", end(result=True)),
        ]
        run_flow(self, recruit_general.run, SCREENS, flow, {}, setup=_setup, variants=VARIANTS)

    def test_already_correct_goes_straight_to_refresh(self):
        """Historic đã tích, Epic chưa tích: không bấm ô nào, vào Refresh liên tục: mỗi lần bấm chờ REFRESH_WAIT giây."""
        flow = [
            Step("02_recruit_unchecked.png?right", *[tap(REFRESH)] * 3),
            Step("01_tavern_menu.png", end(result=True)),
        ]
        device = run_flow(self, recruit_general.run, SCREENS, flow, {}, setup=_setup, variants=VARIANTS)
        taps = [e for _, e in device.events if e[0] == "tap"]
        self.assertEqual(len(taps), 3)
        self.assertEqual(REFRESH_WAIT, 1)

    def test_high_quality_popup_cancel(self):
        """Refresh liên tục tới khi hiện popup "Your Tavern has a high quality General": bấm Cancel (không Confirm), dừng."""
        flow = [
            Step("02_recruit_unchecked.png?right", *[tap(REFRESH)] * 2),
            Step("04_high_quality_popup.png", tap(CANCEL)),
            Step("02_recruit_unchecked.png?right", tap(REFRESH)),   # popup đã đóng, danh sách tướng cần mua rỗng: Refresh tiếp
            Step("01_tavern_menu.png", end(result=True)),
        ]
        device = run_flow(self, recruit_general.run, SCREENS, flow, {}, setup=_setup, variants=VARIANTS)
        self.assertEqual(len([e for _, e in device.events if e[0] == "tap"]), 4)

    FREDERICK = {"generals": ["Frederick the Great"]}   # tên đọc OCR từ ảnh 03 (tướng tím chấm 1)

    def test_cancel_then_wanted_general(self):
        """Sau Cancel tướng đang hiện có vương miện (tím) và tên cần mua: sang luồng mua (chưa làm: không bấm gì thêm), dừng."""
        flow = [
            Step("02_recruit_unchecked.png?right", tap(REFRESH)),
            Step("04_high_quality_popup.png", tap(CANCEL)),
            Step("03_recruit_both_checked.png?epic_off", tap_pct(50, 40)),    # chấm tím + vương miện, tên Frederick the Great: bấm vào tướng
            Step("05_general_detail.png", tap(DETAIL_RECRUIT)),               # hai nút, mặc định setting: Recruit General
            Step("07_after_recruit.png", tap_pct(*HISTORIC_PCT)),             # game tự về danh sách ("Recruited", hai ô bị bỏ tích): tích lại Historic
            Step("02_recruit_unchecked.png?right", tap(REFRESH)),             # rồi Refresh tiếp
            Step("01_tavern_menu.png", end(result=True)),
        ]
        device = run_flow(self, recruit_general.run, SCREENS, flow, self.FREDERICK, setup=_setup, variants=VARIANTS)
        self.assertTrue(any("crowned General slot(s)" in line and "1 purple" in line for line in device.logs))
        self.assertTrue(any("wanted General Frederick the Great" in line for line in device.logs))
        self.assertTrue(any("tapped Recruit General" in line for line in device.logs))

    def _to_detail(self, detail, settings, button):
        """Tới màn chi tiết tướng `detail` rồi bấm `button` (tên tướng cần mua Frederick the Great, ảnh 03)."""
        flow = [
            Step("04_high_quality_popup.png", tap(CANCEL)),
            Step("03_recruit_both_checked.png?epic_off", tap_pct(50, 40)),
            Step(detail, tap(button)),
            Step("02_recruit_unchecked.png?right", tap(REFRESH)),       # game tự về màn danh sách tướng: Refresh tiếp
            Step("01_tavern_menu.png", end(result=True)),
        ]
        return run_flow(self, recruit_general.run, SCREENS, flow, {**settings, **self.FREDERICK}, setup=_setup, variants=VARIANTS)

    def test_detail_single_button_taps_it(self):
        """Màn chi tiết chỉ có MỘT nút Recruit General: bấm thẳng, kể cả khi setting là Buy General Token."""
        self._to_detail("06_general_detail_single.png", {"buy_with": "Buy General Token"}, DETAIL_RECRUIT)

    def test_detail_two_buttons_follows_setting(self):
        """Hai nút: bấm theo setting (Buy General Token)."""
        self._to_detail("05_general_detail.png", {"buy_with": "Buy General Token"}, DETAIL_BUY_TOKEN)

    def test_two_generals_swipe_to_the_other_and_buy(self):
        """HAI tướng xịn (ảnh 08: Barbarossa vàng đang hiện ở chấm 5 và tướng tím ở chấm 1): tên đang hiện không cần mua, kéo sang phải
        tới tướng chấm 1 (Frederick the Great, cần mua), mua, tích lại Historic rồi Refresh tiếp."""
        flow = [
            Step("04_high_quality_popup.png", tap(CANCEL)),
            Step("08_two_generals.png", swipe(5, 40, 95, 40)),                  # đích bên trái: kéo sang phải
            Step("03_recruit_both_checked.png", tap_pct(50, 40)),                # tới tướng chấm 1 (huy hiệu hiện), cần mua: bấm vào tướng
            Step("05_general_detail.png", tap(DETAIL_RECRUIT)),
            Step("07_after_recruit.png", tap_pct(*HISTORIC_PCT)),                # game về danh sách, bỏ tích hai ô: tích lại Historic
            Step("02_recruit_unchecked.png?right", tap(REFRESH)),
            Step("01_tavern_menu.png", end(result=True)),
        ]
        device = run_flow(self, recruit_general.run, SCREENS, flow, self.FREDERICK, setup=_setup, variants=VARIANTS)
        self.assertTrue(any("crowned General slot(s)" in line and "1 purple" in line and "5 gold" in line for line in device.logs))

    def test_low_level_three_or_four_generals_stops(self):
        """3/6 hoặc 4/6 tướng đã mở: ghi log level quá thấp, không bấm gì, activity dừng (False)."""
        for name in ("12_three_generals.png", "13_four_generals.png"):
            flow = [Step(name, end(result=False))]
            device = run_flow(self, recruit_general.run, SCREENS, flow, {}, setup=_setup, variants=VARIANTS)
            self.assertTrue(any("level too low" in line for line in device.logs), name)
            self.assertEqual([e for _, e in device.events if e[0] == "tap"], [], name)

    def test_five_generals_keeps_going(self):
        """5/6 tướng: đủ để roll, không dừng (chưa tích Historic nên bấm tích)."""
        flow = [
            Step("14_five_generals.png", tap_pct(*HISTORIC_PCT, count=3)),   # ảnh không đổi nên bot bấm đủ BOX_TAPS lần
            Step("14_five_generals.png", end(result=False)),                  # rồi báo không đổi được ô và dừng: KHÔNG phải vì level thấp
        ]
        device = run_flow(self, recruit_general.run, SCREENS, flow, {}, setup=_setup, variants=VARIANTS)
        self.assertFalse(any("level too low" in line for line in device.logs))

    def test_stops_after_buying_three_generals(self):
        """Mua xong vẫn Refresh tiếp; mua đủ 3 tướng (mỗi lượt popup mua 1 tướng) thì dừng, không Cancel / Refresh thêm."""
        from unittest import mock
        module = importlib.import_module("bot.activities.recruit_general.run")
        flow = [
            Step("04_high_quality_popup.png", tap(CANCEL)),
            Step("04_high_quality_popup.png", tap(CANCEL)),
            Step("04_high_quality_popup.png", tap(CANCEL)),
            Step("01_tavern_menu.png", end(result=True)),      # dừng ở đây, không thêm thao tác nào
        ]
        with mock.patch.object(module, "_handle_generals", return_value=1),                 mock.patch.object(module, "_set_warnings", return_value=True),                 mock.patch.object(module, "_refresh_confirm", return_value=True):   # bước Refresh + Confirm sau mỗi lượt test riêng
            device = run_flow(self, recruit_general.run, SCREENS, flow, {}, setup=_setup, variants=VARIANTS)
        self.assertTrue(any("bought 3 General(s), stop" in line for line in device.logs))

    def _buy_count_run(self, settings, popups):
        """Chạy `popups` lượt popup, mỗi lượt mua 1 tướng (mock): trả log."""
        from unittest import mock
        module = importlib.import_module("bot.activities.recruit_general.run")
        flow = [Step("04_high_quality_popup.png", tap(CANCEL)) for _ in range(popups)] + [Step("01_tavern_menu.png", end(result=True))]
        with mock.patch.object(module, "_handle_generals", return_value=1), mock.patch.object(module, "_set_warnings", return_value=True),                 mock.patch.object(module, "_refresh_confirm", return_value=True):
            return run_flow(self, recruit_general.run, SCREENS, flow, settings, setup=_setup, variants=VARIANTS).logs

    def test_buy_count_setting_stops_after_n(self):
        """Setting buy_count = 10: mua 10 tướng thì dừng (mỗi lượt popup mua 1 tướng)."""
        logs = self._buy_count_run({"buy_count": 10}, 10)
        self.assertTrue(any("bought 10 General(s), stop" in line for line in logs))

    def test_buy_count_all_never_stops_on_count(self):
        """buy_count = ALL: mua bao nhiêu cũng không dừng vì số tướng (ở đây hết ảnh mới rời màn)."""
        logs = self._buy_count_run({"buy_count": "ALL"}, 12)
        self.assertFalse(any("General(s), stop" in line for line in logs))
        self.assertTrue(any("bought 12/ALL General(s) so far" in line for line in logs))

    def test_refresh_count_setting_stops_after_n(self):
        """Setting refresh_count = 100: bấm Refresh đủ 100 lần rồi dừng."""
        flow = [Step("02_recruit_unchecked.png?right", *[tap(REFRESH)] * 100), Step("02_recruit_unchecked.png?right", end(result=True))]
        device = run_flow(self, recruit_general.run, SCREENS, flow, {"refresh_count": 100}, setup=_setup, variants=VARIANTS)
        self.assertEqual(len([e for _, e in device.events if e[0] == "tap"]), 100)
        self.assertTrue(any("100 refreshes done" in line for line in device.logs))

    def test_limit_values(self):
        """"ALL" = không giới hạn; số hợp lệ giữ nguyên; thiếu / sai kiểu (settings cũ) về mặc định."""
        module = importlib.import_module("bot.activities.recruit_general.run")
        self.assertIsNone(module._limit("ALL", 7))
        self.assertEqual(module._limit(300, 7), 300)
        for bad in (None, "x", 0, -5, True, 2.5):
            self.assertEqual(module._limit(bad, 7), 7, bad)

    def test_refresh_after_checking_confirms_the_popup(self):
        """Kiểm tra xong các tướng xịn: bấm Refresh; popup "high quality General" hiện lại thì bấm Confirm."""
        module = importlib.import_module("bot.activities.recruit_general.run")
        flow = [
            Step("02_recruit_unchecked.png?right", tap(REFRESH)),
            Step("04_high_quality_popup.png", tap(CONFIRM)),
            Step("02_recruit_unchecked.png?right", end(result=True)),
        ]
        run_flow(self, lambda ctx, _s: module._refresh_confirm(ctx), SCREENS, flow, {}, setup=_setup, variants=VARIANTS)

    def test_refresh_after_checking_without_popup(self):
        """Refresh miễn phí / không hiện popup: không bấm Confirm, coi là đã refresh."""
        module = importlib.import_module("bot.activities.recruit_general.run")
        flow = [
            Step("02_recruit_unchecked.png?right", tap(REFRESH)),
            Step("02_recruit_unchecked.png?right", end(result=True)),
        ]
        run_flow(self, lambda ctx, _s: module._refresh_confirm(ctx), SCREENS, flow, {}, setup=_setup, variants=VARIANTS)

    def test_cancel_then_crowned_but_unwanted_keeps_refreshing(self):
        """Có vương miện nhưng tên không có trong danh sách tướng đã tích: Refresh tiếp."""
        flow = [
            Step("04_high_quality_popup.png", tap(CANCEL)),
            Step("03_recruit_both_checked.png?epic_off", tap(REFRESH)),
            Step("01_tavern_menu.png", end(result=True)),
        ]
        run_flow(self, recruit_general.run, SCREENS, flow, {}, setup=_setup, variants=VARIANTS)

    def test_cancel_then_no_crown_keeps_refreshing(self):
        """Tên tướng đang hiện có trong danh sách nhưng không có vương miện (chấm xanh): bỏ qua, Refresh tiếp."""
        flow = [
            Step("04_high_quality_popup.png", tap(CANCEL)),
            Step("02_recruit_unchecked.png?right", tap(REFRESH)),
            Step("01_tavern_menu.png", end(result=True)),
        ]
        device = run_flow(self, recruit_general.run, SCREENS, flow, {"generals": ["Hong Fu Nu"]}, setup=_setup, variants=VARIANTS)   # Hong Fu Nu có trong danh sách nhưng ảnh 02 không có vương miện
        self.assertFalse(any("wanted General" in line for line in device.logs))

    def test_refresh_stops_at_max(self):
        """Màn Recruit General không đổi: bấm Refresh đủ REFRESH_MAX lần rồi dừng."""
        from unittest import mock
        module = importlib.import_module("bot.activities.recruit_general.run")   # `recruit_general.run` là hàm, không phải module
        flow = [Step("02_recruit_unchecked.png?right", *[tap(REFRESH)] * 5), Step("02_recruit_unchecked.png?right", end(result=True))]
        with mock.patch.object(module, "REFRESH_MAX", 5):
            device = run_flow(self, recruit_general.run, SCREENS, flow, {}, setup=_setup, variants=VARIANTS)
        self.assertEqual(len([e for _, e in device.events if e[0] == "tap"]), 5)


if __name__ == "__main__":
    unittest.main()
