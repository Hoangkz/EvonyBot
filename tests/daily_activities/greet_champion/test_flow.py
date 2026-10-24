"""
Flow test Daily Activities / Greet Champion (bot/activities/daily_activities/greet_champion/): màn Champion đã đủ lượt
(chữ "Greet 10/10") -> nhận ra ngay, không bấm giữa màn, trả FULL và lưu "xong hôm nay" (KEY + MORE_KEY) để lần sau không vào
lại. Thông báo "You cannot Empower anymore for today!" chỉ làm bot thôi bấm giữa, không phải xong.

Ảnh trong screens/ là ảnh chụp nguyên màn hình giả lập 396x704 (mỹ nữ Esmeralda, Greet 10/10; ảnh _toast có thêm thông báo
"You cannot Empower anymore for today!" sau khi bấm giữa).
"""
import unittest
from pathlib import Path
from unittest import mock

import cv2

from bot.activities.daily_activities.greet_champion import run as greet_run
from bot.activities.daily_activities.greet_champion.constants import KEY, MORE_KEY
from bot.activities.daily_activities.greet_champion.run import FULL, TIMEOUT, _greet_loop, after_go, greet_full
from tests.flow import Step, end, run_flow

SCREENS = Path(__file__).parent / "screens"
FULL_SCREEN = "champion_greet_full.png"
TOAST_SCREEN = "champion_greet_full_toast.png"
HELEN_FULL = "champion_helen_greet_full.png"          # 21913: Helen, Greet 10/10
HELEN_2_LOCKED = "champion_helen_greet_2_locked.png"  # 21913: Helen, Greet 2/10 đang chờ hồi (ổ khoá + đếm ngược)


def no_label(screen):
    """ẢNH TỔNG HỢP: che chữ "Greet 10/10" (nền tối) để chỉ còn thông báo giữa màn nhận ra đủ lượt."""
    screen[505:530, 0:90] = (30, 30, 30)
    return screen


def _loop(bot, _settings):
    return _greet_loop(bot)


def _after_go(bot, _settings):
    return after_go(bot)


class GreetChampionFlow(unittest.TestCase):
    def test_greet_full_by_text_shape_on_any_background(self):
        # Chữ 10/10 đè trong suốt lên nền: so hình chữ vàng nên nhận ra trên cả Esmeralda lẫn Helen (21913); 2/10 thì không.
        for screen, full in ((FULL_SCREEN, True), (TOAST_SCREEN, True), (HELEN_FULL, True), (HELEN_2_LOCKED, False)):
            with self.subTest(screen=screen):
                self.assertEqual(greet_full(cv2.imread(str(SCREENS / screen))), full)

    def test_greet_10_of_10_is_recognised(self):
        for screen in (FULL_SCREEN, TOAST_SCREEN, HELEN_FULL):
            with self.subTest(screen=screen):
                device = run_flow(self, _loop, SCREENS, [Step(screen, end(result=FULL))], {})
                self.assertIn("Greet Champion: Greet 10/10", device.logs)

    def test_cannot_empower_message_only_stops_middle_taps(self):
        # Thông báo "You cannot Empower anymore for today!" KHÔNG phải 10/10 (21913: hiện cả lúc Greet 2/10 chờ hồi): che chữ
        # 10/10 đi, Greet khoá -> bot không bấm gì (bấm giữa là sai kịch bản), chỉ chờ tới hết giờ (TIMEOUT, không báo xong).
        with mock.patch.object(greet_run, "TASK_MAX_SECONDS", 5):
            device = run_flow(self, _loop, SCREENS, [Step(f"{TOAST_SCREEN}?no_label", end(result=TIMEOUT))], {},
                              variants={"no_label": no_label})
        self.assertIn("Greet Champion: cannot Empower anymore today, stop tapping the middle", device.logs)
        self.assertNotIn(MORE_KEY, device.daily_done)

    def test_after_go_full_saves_done_so_it_is_not_entered_again(self):
        # Bỏ qua bước vào màn Champion (trái tim / Keep) và Back về thành: chỉ xét phần nhận đủ lượt + lưu DB.
        with mock.patch.object(greet_run, "_open_champion", return_value=True), \
                mock.patch.object(greet_run, "_leave"):
            device = run_flow(self, _after_go, SCREENS, [Step(FULL_SCREEN, end(result=True))], {})
        self.assertIn(KEY, device.daily_done)        # kết quả "xong" được ghi như worker (run_flow -> record_result)
        self.assertIn(MORE_KEY, device.daily_done)   # việc chào tiếp (more) cũng xong: hôm nay không vào lại


if __name__ == "__main__":
    unittest.main()
