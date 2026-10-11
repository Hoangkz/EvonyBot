"""
Flow test Event / King's Path: phần chung — rương Login Rewards, Voyage, mở danh sách event, Day khoá, nhường boss.
Test từng nhiệm vụ nằm ở thư mục riêng (patrol/, donate/, city_tax/, train_troop/, heal/, wheel/, refine/, black_market/).
Ảnh dùng chung ở screens/ (ảnh chụp nguyên màn hình giả lập 396x704, Day 5 đang khoá).
"""
import sys
from dataclasses import replace
import unittest
from unittest import mock
from bot.activities import event
from bot.activities.event.constants import KINGS_PATH_ICON
from bot.activities.event.kings_path import donate, heal, patrol, path_task, wheel
from bot.activities.event.kings_path.wheel.constants import SPINS_100
from bot.context.errors import YieldToBoss
from tests.flow import Step, back, end, run_flow, swipe, tap, tap_at
from tests.event import CLAIM_LOGIN_REWARD, OPEN_VOYAGE
from bot.activities.event import common as event_common
from bot.activities.event.constants import LOGIN_REWARD_KEY, VOYAGE_ICON, VOYAGE_KEY, VOYAGE_SKIP_OFF
from tests.event.kings_path.common import SCREENS, KP, EVENT_BUTTON, _run
from tests.event import setUpModule, tearDownModule, run_event_tasks  # noqa: F401 (tắt lượt nhận thưởng)


class LoginRewardFlow(unittest.TestCase):
    """Rương Login Rewards hôm nay ở đầu danh sách event (event/common.py claim_login_reward)."""

    def _run(self, flow, **kw):
        with mock.patch.object(event_common, "claim_login_reward", CLAIM_LOGIN_REWARD):
            return _run(self, flow, {wheel.KEY: {"value": 100, "day": 4}}, **kw)

    def test_unopened_chest_claimed(self):
        """Rương trên đầu thanh tiến độ (122, 306) chưa mở: bấm (122, 271), lưu DB, rồi tìm icon King's
        Path như thường."""
        flow = [
            Step("03_main.png?main_claimed", tap_at(*EVENT_BUTTON)),
            Step("event_list_reward.png", tap_at(122, 271, tol=3)),
            Step("04_event_list.png", tap(KINGS_PATH_ICON)),
            Step("day4_fortune_wheel.png", tap_at(335, 344)),
            Step("wheel_of_fortune.png", tap(SPINS_100), back(), end()),
        ]
        device = self._run(flow)
        self.assertIn(LOGIN_REWARD_KEY, device.daily_done)
        self.assertIn(wheel.KEY, device.daily_done)

    def test_unopened_chest_scrolled_row(self):
        """Hàng rương đã cuộn ngang (máy 21923): đầu thanh (68, 306), rương ngày 2 chưa nhận -> bấm
        (68, 271)."""
        flow = [
            Step("03_main.png?main_claimed", tap_at(*EVENT_BUTTON)),
            Step("event_list_reward_scrolled.png", tap_at(68, 271, tol=3)),
            Step("04_event_list.png", tap(KINGS_PATH_ICON)),
            Step("day4_fortune_wheel.png", tap_at(335, 344)),
            Step("wheel_of_fortune.png", tap(SPINS_100), back(), end()),
        ]
        device = self._run(flow)
        self.assertIn(LOGIN_REWARD_KEY, device.daily_done)

    def test_opened_chest_skipped(self):
        """Rương hôm nay đã mở (nắp mở): không bấm, lưu DB (hôm nay không kiểm nữa). Ảnh này không có
        icon King's Path: cuộn hết rồi Back, bỏ nhiệm vụ."""
        flow = [
            Step("03_main.png?main_claimed", tap_at(*EVENT_BUTTON)),
            Step("event_list_reward_opened.png", *[swipe(50, 80, 50, 50) for _ in range(4)], back()),
            Step("03_main.png?main_claimed", end()),
        ]
        device = self._run(flow)
        self.assertIn("Event: login reward already opened", device.logs)
        self.assertIn(LOGIN_REWARD_KEY, device.daily_done)

    def test_checked_today_not_again(self):
        """Hôm nay đã kiểm (DB có LOGIN_REWARD_KEY): không bấm rương, tìm icon luôn."""
        flow = [
            Step("03_main.png?main_claimed", tap_at(*EVENT_BUTTON)),
            Step("04_event_list.png", tap(KINGS_PATH_ICON)),
            Step("day4_fortune_wheel.png", tap_at(335, 344)),
            Step("wheel_of_fortune.png", tap(SPINS_100), back(), end()),
        ]
        device = self._run(flow, daily_done={LOGIN_REWARD_KEY: "2026-10-03T09:00:00"})
        self.assertIn(wheel.KEY, device.daily_done)


class VoyageFlow(unittest.TestCase):
    """Voyage to Civilizations ở danh sách event (event/common.py open_voyage): hôm nay chưa bấm Free
    -> vào, tích Skip animation, có Free thì bấm và lưu VOYAGE_KEY, Back về danh sách."""

    def _run(self, flow, **kw):
        with mock.patch.object(event_common, "open_voyage", OPEN_VOYAGE):
            return _run(self, flow, {wheel.KEY: {"value": 100, "day": 4}}, **kw)

    def test_free_voyage(self):
        """Hôm nay chưa làm: vào Voyage -> tích Skip animation -> bấm Voyage Once (Free) -> popup
        Congratulations -> Back (đóng popup) -> Back (về danh sách) -> tìm icon King's Path như thường."""
        flow = [
            Step("03_main.png?main_claimed", tap_at(*EVENT_BUTTON)),
            Step("event_list_voyage_dot.png", tap(VOYAGE_ICON)),
            Step("voyage_screen.png", tap(VOYAGE_SKIP_OFF)),
            Step("voyage_skip_ticked.png", tap_at(287, 670, tol=5)),
            Step("voyage_congrats.png", back()),
            Step("voyage_no_free.png", back()),
            Step("04_event_list.png", tap(KINGS_PATH_ICON)),
            Step("day4_fortune_wheel.png", tap_at(335, 344)),
            Step("wheel_of_fortune.png", tap(SPINS_100), back(), end()),
        ]
        device = self._run(flow)
        self.assertIn("Event: Voyage: free Voyage Once", device.logs)
        self.assertIn(VOYAGE_KEY, device.daily_done)

    def test_no_free(self):
        """Đã tích Skip animation, không thấy Free: không bấm gì, Back. VOYAGE_KEY lưu ngay khi vào (mỗi ngày
        chỉ vào Voyage 1 lần, có Free hay không)."""
        flow = [
            Step("03_main.png?main_claimed", tap_at(*EVENT_BUTTON)),
            Step("event_list_voyage_dot.png", tap(VOYAGE_ICON)),
            Step("voyage_no_free.png", back()),
            Step("04_event_list.png", tap(KINGS_PATH_ICON)),
            Step("day4_fortune_wheel.png", tap_at(335, 344)),
            Step("wheel_of_fortune.png", tap(SPINS_100), back(), end()),
        ]
        device = self._run(flow)
        self.assertIn("Event: Voyage: no Free today", device.logs)
        self.assertIn(VOYAGE_KEY, device.daily_done)

    def test_done_today_not_entered(self):
        """Hôm nay đã bấm Free (DB có VOYAGE_KEY): không vào Voyage. Ảnh không có icon King's Path: cuộn hết,
        Back."""
        flow = [
            Step("03_main.png?main_claimed", tap_at(*EVENT_BUTTON)),
            Step("event_list_voyage_dot.png", *[swipe(50, 80, 50, 50) for _ in range(4)], back()),
            Step("03_main.png?main_claimed", end()),
        ]
        self._run(flow, daily_done={VOYAGE_KEY: "2026-10-03T09:00:00"})


class KingsPathFlow(unittest.TestCase):
    def test_event_list_not_opened_retries(self):
        """Bấm nút event mà không vào được danh sách (không thấy tiêu đề, cuộn hết không thấy icon ->
        Back): thử lại thêm 2 lần (EVENT_OPEN_RETRIES), vẫn không được thì bỏ nhiệm vụ."""
        flow = [
            *[step for _ in range(3) for step in (
                Step("03_main.png?main_claimed", tap_at(*EVENT_BUTTON)),
                Step("04_event_list.png?no_list", *[swipe(50, 80, 50, 50) for _ in range(4)], back()),
            )],
            Step("03_main.png?main_claimed", end()),
        ]
        device = _run(self, flow, {wheel.KEY: {"value": 100, "day": 4}})
        self.assertIn("Wheel: event list not opened after 3 tries, skip to next task", device.logs)
        self.assertNotIn(wheel.KEY, device.daily_done)

    def test_event_list_retry_then_open(self):
        """Lần đầu không vào được danh sách -> thử lại -> lần 2 vào được, mở King's Path như thường."""
        flow = [
            Step("03_main.png?main_claimed", tap_at(*EVENT_BUTTON)),
            Step("04_event_list.png?no_list", *[swipe(50, 80, 50, 50) for _ in range(4)], back()),
            Step("03_main.png?main_claimed", tap_at(*EVENT_BUTTON)),
            Step("04_event_list.png", tap(KINGS_PATH_ICON)),
            Step("day4_fortune_wheel.png", tap_at(335, 344)),
            Step("wheel_of_fortune.png", tap(SPINS_100), back(), end()),
        ]
        device = _run(self, flow, {wheel.KEY: {"value": 100, "day": 4}})
        self.assertIn("Wheel: event list not opened, retry 1/2", device.logs)
        self.assertIn(wheel.KEY, device.daily_done)

    def test_open_from_main(self):
        """Màn chính -> nút dưới Event Center -> danh sách event (đã cuộn, King's Path ở dưới)
        -> icon King's Path -> màn King's Path Day 4 -> tab Fortune Wheel đang chọn -> Go."""
        flow = [
            Step("03_main.png?main_claimed", tap_at(*EVENT_BUTTON)),
            Step("04_event_list.png", tap(KINGS_PATH_ICON)),
            Step("day4_fortune_wheel.png", tap_at(335, 344)),
            Step("wheel_of_fortune.png", tap(SPINS_100), back(), end()),
        ]
        device = _run(self, flow, {wheel.KEY: {"value": 100, "day": 4}})
        self.assertIn(wheel.KEY, device.daily_done)

    def test_target_reached(self):
        """Đã đạt mục tiêu người dùng chọn (140 >= 100): đánh dấu xong, không bấm Go."""
        flow = [Step("day2_teamwork.png", end())]
        device = _run(self, flow, {patrol.KEY: {"value": 100, "day": 2}})
        self.assertIn(patrol.KEY, device.daily_done)

    def test_open_day(self):
        """Đang ở Day 4 -> bấm Day 3 -> tab Healing Heart đang chọn -> Go trên cùng."""
        flow = [
            Step("day4_accumulation.png", tap(f"{KP}/Day/day3.png")),
            Step("day3_healing_heart.png", tap_at(335, 344)),   # sau Go: harness dừng bot
        ]
        device = _run(self, flow, {heal.KEY: {"value": 50000, "day": 3}})
        self.assertIn("Heal: done 0, target 50000", device.logs)

    def test_after_go_again_rereads_progress(self):
        """after_go trả AGAIN (VD Heal vừa Speed Up): không dừng, đi lại tới dòng Go, OCR lại số đã
        làm rồi bấm Go lần nữa."""
        heal_run = sys.modules["bot.activities.event.kings_path.heal.run"]
        results = iter([path_task.AGAIN, None])
        path = replace(heal_run.PATH, after_go=lambda *args: next(results))
        flow = [
            Step("day3_healing_heart.png", tap_at(335, 344)),
            Step("day3_healing_heart.png", tap_at(335, 344), end()),
        ]
        with mock.patch.object(heal_run, "PATH", path):
            device = _run(self, flow, {heal.KEY: {"value": 50000, "day": 3}})
        self.assertIn("Heal: again from the start (re-read progress, round 1)", device.logs)
        self.assertEqual(device.logs.count("Heal: done 0, target 50000"), 2)

    def test_day_locked(self):
        """Ngày của nhiệm vụ còn khoá (Day 5): lưu "chưa thể thực hiện", không bấm gì."""
        flow = [Step("day4_fortune_wheel.png", end())]
        device = _run(self, flow, {wheel.KEY: {"value": 100, "day": 5}})
        self.assertIn(f"{wheel.KEY}_locked", device.daily_done)
        self.assertNotIn(wheel.KEY, device.daily_done)

    def test_not_kings_path_backs(self):
        """Hàng tab Day giống Gather Troops: không thấy tiêu đề King's Path -> Back."""
        flow = [
            Step("day3_healing_heart.png?not_kp", back()),
            Step("day3_healing_heart.png", tap_at(335, 344)),   # sau Go: harness dừng bot
        ]
        _run(self, flow, {heal.KEY: {"value": 50000, "day": 3}})

    def test_no_icon_skips(self):
        """Chưa có ảnh icon King's Path: bỏ qua nhiệm vụ, không bấm gì."""
        flow = [Step("day4_fortune_wheel.png", end())]
        with mock.patch.object(path_task, "KINGS_PATH_ICON", f"{KP}/missing.png"):
            run_flow(self, run_event_tasks, SCREENS, flow, {wheel.KEY: {"value": 100, "day": 4}})


if __name__ == "__main__":
    unittest.main()
