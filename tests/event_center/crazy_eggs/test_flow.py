"""
Flow test nhiệm vụ Event Center "Crazy Eggs" (bot/activities/event_center/crazy_eggs).

Ảnh tổng hợp (chưa có ảnh chụp thật):
- `cracked_<quả>`: 04_eggs_ready.png với nhãn của các quả đó lấy từ 05_eggs_waiting.png
  ("Waiting:", không có búa) — trạng thái sau khi đập từng quả.
"""
import unittest
from pathlib import Path

import cv2

from bot.activities.event_center import crazy_eggs
from bot.activities.event_center.crazy_eggs.constants import DONE_KEY, LUCKY_KEY
from bot.activities.event_center.constants import AFTER_RESTART_ATTEMPTS, ATTEMPTS, LIST_MAX_SCROLLS
from tests.flow import Step, back, end, run_flow, shell, swipe, tap, tap_at, tap_pct

SCREENS = Path(__file__).parent / "screens"
ICON = "EventCenter/CrazyEggs/icon.png"

# Tâm icon búa (7.png) của từng quả: bot bấm thẳng vào đó.
EGGS = {1: (139, 393), 2: (297, 393), 3: (139, 583), 4: (297, 583)}
# Búa vàng: bấm nhãn "Waiting:" của quả 2 (quả đang chờ không có búa).
EGG_2_WAITING = (250, 391)
CONFIRM = "EventCenter/CrazyEggs/confirm.png"
CANCEL = "EventCenter/CrazyEggs/cancel.png"
LUCKY_USED = {LUCKY_KEY: "2026-10-02T09:00:00"}
# Vùng nhãn "Scout Cost:" / "Waiting:" của từng quả (x0, y0, x1, y1).
LABELS = {1: (55, 378, 190, 402), 2: (210, 378, 345, 402),
          3: (55, 568, 190, 592), 4: (210, 568, 345, 592)}


def _no_activities_tab(screen):
    """Xoá chữ trên tab Activities (màn Event Center không có tab Activities)."""
    region = screen[66:94, 150:248]
    region[:] = region.reshape(-1, 3).mean(axis=0)
    return screen


def _cracked(*eggs):
    waiting = cv2.imread(str(SCREENS / "05_eggs_waiting.png"))

    def variant(screen):
        for n in eggs:
            x0, y0, x1, y1 = LABELS[n]
            screen[y0:y1, x0:x1] = waiting[y0:y1, x0:x1]
        return screen
    return variant


VARIANTS = {
    "cracked_2": _cracked(2),
    "cracked_23": _cracked(2, 3),
    "cracked_231": _cracked(2, 3, 1),
    "cracked_3": _cracked(3),
    "no_activities_tab": _no_activities_tab,
}


def _retry_flow(attempt):
    """Kịch bản run_task_with_retry: ATTEMPTS lần `attempt()`, force-stop game, rồi
    AFTER_RESTART_ATTEMPTS lần nữa, cuối cùng return ở màn chính."""
    flow = [step for _ in range(ATTEMPTS) for step in attempt()]
    flow[-1].actions.append(shell("am force-stop"))
    flow += [step for _ in range(AFTER_RESTART_ATTEMPTS) for step in attempt()]
    return flow + [Step("01_main.png", end())]


class CrazyEggsFlow(unittest.TestCase):
    def test_main_flow(self):
        """Màn chính -> Event Center (chính nút cúp) -> tab Activities -> Crazy Eggs ->
        đập 2-3-1-4 -> hết quả có búa -> búa vàng cho quả 2 -> Confirm -> popup "Congratulations!" -> return. Sau quả 2:
        popup "Congratulations!" -> BACK (06_congratulations.png là ảnh thật của
        một lần đập khác)."""
        flow = [
            Step("01_main.png", tap_at(359, 216)),
            Step("02_event_center.png", tap("EventCenter/activitiesTab.png")),
            Step("03_activities.png", swipe()),
            Step("03_activities_crazy_eggs.png", tap(ICON)),
            Step("04_eggs_ready.png", tap_at(*EGGS[2])),
            Step("06_congratulations.png", back()),
            Step("04_eggs_ready.png?cracked_2", tap_at(*EGGS[3])),
            Step("04_eggs_ready.png?cracked_23", tap_at(*EGGS[1])),
            Step("04_eggs_ready.png?cracked_231", tap_at(*EGGS[4])),
            Step("05_eggs_waiting.png", tap_at(*EGG_2_WAITING)),
            Step("07_lucky_hammer.png", tap(CONFIRM)),
            Step("06_congratulations.png", back()),
            Step("05_eggs_waiting.png", end()),
        ]
        device = run_flow(self, crazy_eggs.run, SCREENS, flow, {}, variants=VARIANTS)
        self.assertIn(LUCKY_KEY, device.daily_done)

    def test_not_enough_hammers_dialog(self):
        """Bấm quả 3 khi hết búa (08_egg_1_activated.png) -> hộp thoại "You don't have enough Hammers"
        (11) -> Cancel -> hết búa; búa vàng đã dùng -> return."""
        flow = [
            Step("08_egg_1_activated.png", tap_at(*EGGS[3])),
            Step("11_not_enough_hammers.png", tap(CANCEL)),
            Step("08_egg_1_activated.png", end()),
        ]
        run_flow(self, crazy_eggs.run, SCREENS, flow, {}, daily_done=LUCKY_USED)

    def test_out_of_hammers(self):
        """Bấm quả 2 mà vẫn còn búa (số quả có búa không giảm) -> hết búa. Quả 2 không chờ
        nên không dùng búa vàng -> return."""
        flow = [
            Step("04_eggs_ready.png", tap_at(*EGGS[2])),
            Step("04_eggs_ready.png", end()),
        ]
        device = run_flow(self, crazy_eggs.run, SCREENS, flow, {})
        self.assertNotIn(LUCKY_KEY, device.daily_done)

    def test_all_waiting_lucky_used_returns(self):
        """Mọi quả đang chờ, búa vàng đã dùng hôm nay: không bấm gì, return luôn."""
        run_flow(self, crazy_eggs.run, SCREENS, [Step("05_eggs_waiting.png", end())], {},
                 daily_done=LUCKY_USED)

    def test_activated_egg_skipped(self):
        """Quả 1 đã vỡ ("Activated", 08_egg_1_activated.png): chỉ đập quả 3 (còn búa). Giả sử quả
        3 vỡ luôn: animation (10, màn tối) -> bấm (50 %, 95 %) -> popup "Congratulations on
        activating the egg!" (09) -> BACK -> return.
        Có quả vỡ thì không phải lần chạy đầu trong ngày, nên búa vàng đã dùng."""
        flow = [
            Step("08_egg_1_activated.png", tap_at(*EGGS[3])),
            Step("10_egg_breaking.png", tap_pct(50, 95)),
            Step("09_egg_activated_rewards.png", back()),
            Step("08_egg_1_activated.png?cracked_3", end()),
        ]
        run_flow(self, crazy_eggs.run, SCREENS, flow, {}, variants=VARIANTS, daily_done=LUCKY_USED)

    def test_no_lucky_hammer_left(self):
        """Số búa vàng trên màn là "0" (12_all_activated.png, đã dùng tay, DB chưa có): lưu đã dùng,
        return (4 quả đã vỡ, không còn gì để đập)."""
        device = run_flow(self, crazy_eggs.run, SCREENS, [Step("12_all_activated.png", end())], {})
        self.assertIn(LUCKY_KEY, device.daily_done)

    def test_no_activities_tab_marks_done(self):
        """Màn Event Center (thấy tab Competition) mà không có tab Activities: BACK; thử ATTEMPTS lần,
        tắt game (force-stop) rồi thử thêm AFTER_RESTART_ATTEMPTS lần, vẫn không thấy -> lưu đã xong
        hôm nay, return."""
        def attempt():
            return [
                Step("01_main.png", tap_at(359, 216)),
                Step("02_event_center.png?no_activities_tab", back()),
            ]
        flow = _retry_flow(attempt)
        device = run_flow(self, crazy_eggs.run, SCREENS, flow, {}, variants=VARIANTS)
        self.assertIn(DONE_KEY, device.daily_done)

    def test_icon_not_found_restarts_then_marks_done(self):
        """Tab Activities không có icon Crazy Eggs (03_activities.png thật): mỗi lần cuộn hết rồi BACK;
        thử ATTEMPTS lần, tắt game (force-stop) rồi thử thêm AFTER_RESTART_ATTEMPTS lần, vẫn không
        thấy -> lưu đã xong hôm nay, return."""
        def attempt():
            return [
                Step("01_main.png", tap_at(359, 216)),
                Step("02_event_center.png", tap("EventCenter/activitiesTab.png")),
                Step("03_activities.png", *[swipe() for _ in range(LIST_MAX_SCROLLS)], back()),
            ]
        device = run_flow(self, crazy_eggs.run, SCREENS, _retry_flow(attempt), {})
        self.assertIn(DONE_KEY, device.daily_done)

    def test_done_today_skips(self):
        """Đã đánh dấu xong hôm nay: return ngay, không thao tác gì."""
        run_flow(self, crazy_eggs.run, SCREENS, [Step("01_main.png", end())], {},
                 daily_done={DONE_KEY: "2026-10-02T09:00:00"})

    def test_lucky_hammer_no_dialog(self):
        """Bấm quả 2 để dùng búa vàng mà không hiện hộp thoại (đã dùng tay) -> lưu đã dùng, return."""
        flow = [
            Step("05_eggs_waiting.png", tap_at(*EGG_2_WAITING)),
            Step("05_eggs_waiting.png", end()),
        ]
        device = run_flow(self, crazy_eggs.run, SCREENS, flow, {})
        self.assertIn(LUCKY_KEY, device.daily_done)


if __name__ == "__main__":
    unittest.main()
