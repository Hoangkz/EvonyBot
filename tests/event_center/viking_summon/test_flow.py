"""
Flow test nhiệm vụ Event Center "Viking Summon" (bot/activities/event_center/viking_summon).

Ảnh thật chụp trên giả lập (độ khó Easy đã xác nhận thật; các độ khó khác chỉ chọn rồi Cancel ở hộp thoại).
Chưa có ảnh đường đi tới icon "Viking Challenge" trong tab Activities (run_task dùng chung, đã test ở crazy_eggs): flow bắt đầu từ màn Viking.
Ask for Help và chia sẻ (_ask_for_help / _share_boss) được giả trong các ca của `_flow`; _ask_for_help có ca riêng trên ảnh thật. Chia sẻ: đã chạy thật 1 lần, ra 407:686 (xem FLOW.md).
"""
import importlib
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

from bot.activities.event_center.viking_summon import constants as c
from tests.flow import Step, run_flow, tap, tap_at

# `from .run import run` ở __init__ che tên module `run` bằng hàm: lấy module qua importlib.
viking = importlib.import_module("bot.activities.event_center.viking_summon.run")

SCREENS = Path(__file__).parent / "screens"
F = c.FOLDER
BADGE = {"Easy": (65, 385), "Hard": (243, 385)}


def _run(bot, settings):
    bot.server = "1835"
    return viking.run(bot, settings)


def _screen_bot(frames):
    """Bot giả: screenshot() đưa lần lượt các ảnh `frames`; find() tìm ảnh mẫu thật trên ảnh được đưa vào; ghi lại tap / back / sleep."""
    import cv2
    from bot.context import TEMPLATE_DIR
    sequence = iter(frames)
    bot = mock.Mock()
    bot.screenshot.side_effect = lambda: next(sequence)

    def find(template, threshold=0.9, screen=None, region=None, **kw):
        image = cv2.imread(str(TEMPLATE_DIR / template))
        _, score, _, (x, y) = cv2.minMaxLoc(cv2.matchTemplate(screen, image, cv2.TM_CCOEFF_NORMED))
        return (x + image.shape[1] // 2, y + image.shape[0] // 2) if score >= threshold else None

    bot.find.side_effect = find
    return bot


def _flow(testcase, flow, settings, **kwargs):
    calls = []
    with mock.patch.object(viking, "_ask_for_help", side_effect=lambda bot, pos: calls.append("ask") or "asked") as ask,             mock.patch.object(viking, "_share_boss", side_effect=lambda bot, pos: calls.append("share") or "shared") as share:
        device = run_flow(testcase, _run, SCREENS, flow, settings, **kwargs)
    device.share, device.ask, device.calls = share, ask, calls
    return device


class VikingSummonFlow(unittest.TestCase):
    def test_select_easy_then_summon_and_share(self):
        """Màn chọn độ khó: bấm huy hiệu Easy -> Confirm -> hộp thoại "Select Easy level?" -> Confirm -> "Congratulations!" ->
        màn Summon -> Summon -> bản đồ, boss Viking ở giữa -> chia sẻ."""
        flow = [
            Step("02_difficulty_easy.png", tap_at(*BADGE["Easy"]), tap(c.CONFIRM)),
            Step("03_confirm_popup_easy.png", tap(c.POPUP_CONFIRM)),
            Step("05_congratulations.png", tap(c.CONGRATULATIONS)),
            Step("06_summon_screen.png", tap(c.SUMMON)),
            Step("09_viking_map_0.png", end_()),
        ]
        device = _flow(self, flow, {"viking_level": "Easy"})
        self.assertEqual(device.calls, ["ask", "share"])   # Ask for Help trước, rồi mới chia sẻ
        self.assertEqual(getattr(device.ctx, c.CHECKS_ATTR), 0)   # đếm lại các lần kiểm tra tới lần chia sẻ kế
        pos = device.share.call_args.args[1]
        self.assertTrue(abs(pos[0] - 190) < 20 and abs(pos[1] - 333) < 20, pos)

    def test_wrong_level_in_dialog_is_cancelled(self):
        """Muốn Hard mà hộp thoại hỏi Easy: Cancel (không xác nhận nhầm độ khó không đổi lại được), chọn lại Hard rồi mới Confirm."""
        flow = [
            Step("03_confirm_popup_easy.png", tap(c.POPUP_CANCEL)),
            Step("02_difficulty_hard.png", tap_at(*BADGE["Hard"]), tap(c.CONFIRM)),
            Step("03_confirm_popup_hard.png", tap(c.POPUP_CONFIRM)),
            Step("05_congratulations.png", tap(c.CONGRATULATIONS)),
        ]
        _flow(self, flow, {"viking_level": "Hard"})

    def test_level_dialog_not_shown_retries(self):
        """Bấm Confirm mà hộp thoại không hiện sau 5 lần chờ 1 giây: chọn lại từ đầu."""
        flow = [
            Step("02_difficulty_easy.png", tap_at(*BADGE["Easy"]), tap(c.CONFIRM)),
            Step("02_difficulty_easy.png", tap_at(*BADGE["Easy"]), tap(c.CONFIRM)),
            Step("03_confirm_popup_easy.png", tap(c.POPUP_CONFIRM)),
            Step("05_congratulations.png", tap(c.CONGRATULATIONS)),
        ]
        _flow(self, flow, {"viking_level": "Easy"})

    def test_level_already_chosen_goes_straight_to_summon(self):
        """Đã chọn độ khó ở lần trước: vào thẳng màn Summon, không chọn lại; độ khó khác yêu cầu (Easy, muốn Hell) chỉ ghi log."""
        flow = [
            Step("06_summon_screen.png", tap(c.SUMMON)),
            Step("09_viking_map_0.png", end_()),
        ]
        device = _flow(self, flow, {"viking_level": "Hell"})
        self.assertTrue(any("already uses level Easy" in line for line in device.logs))
        device.share.assert_called_once()

    def test_boss_still_alive_go_to_boss_and_share_again(self):
        """Boss chưa bị hạ: màn Viking có nút Go thay cho Summon -> bấm Go (về vị trí boss) -> chia sẻ lại ."""
        flow = [
            Step("10_live_end.png", tap(c.GO)),
            Step("09_viking_map_0.png", end_()),
        ]
        device = _flow(self, flow, {"viking_level": "Easy"})
        device.share.assert_called_once()
        self.assertTrue(any("still alive" in line for line in device.logs))

    def test_go_shares_again_only_at_4th_check(self):
        """Boss còn sống đã chia sẻ: kiểm tra lần 1, 2, 3 sau lần chia sẻ chỉ xem (đếm); lần 4 bấm Go rồi chia sẻ lại và đếm lại từ đầu.
        Chưa chia sẻ lần nào trong lượt chạy này (None): chia sẻ ngay."""
        def checks(n):
            return lambda ctx: setattr(ctx, c.CHECKS_ATTR, n)
        for n in (0, 1, 2):
            device = _flow(self, [Step("10_live_end.png", end_())], {"viking_level": "Easy"}, setup=checks(n))
            device.share.assert_not_called()
            self.assertEqual(getattr(device.ctx, c.CHECKS_ATTR), n + 1)
        flow = [Step("10_live_end.png", tap(c.GO)), Step("09_viking_map_0.png", end_())]
        for n in (3, None):
            device = _flow(self, flow, {"viking_level": "Easy"}, setup=checks(n))
            self.assertEqual(device.calls, ["ask", "share"])
            self.assertEqual(getattr(device.ctx, c.CHECKS_ATTR), 0)

    def test_boss_gone_summon_again_and_reset_counter(self):
        """Boss đã bị đánh hoặc quá lâu không đánh nên mất: màn Viking hiện lại nút Summon (16_boss_gone_summon.png) -> Summon boss mới,
        nhờ giúp + chia sẻ ngay và đếm lại các lần kiểm tra từ 0 (dù đang đếm dở)."""
        flow = [Step("16_boss_gone_summon.png", tap(c.SUMMON)), Step("09_viking_map_0.png", end_())]
        device = _flow(self, flow, {"viking_level": "Easy"}, setup=lambda ctx: setattr(ctx, c.CHECKS_ATTR, 2))
        self.assertEqual(device.calls, ["ask", "share"])
        self.assertEqual(getattr(device.ctx, c.CHECKS_ATTR), 0)

    def test_summon_seen_resets_counter_to_zero_even_if_share_fails(self):
        """Thấy nút Summon là bộ đếm về 0 (đếm lại từ lần kiểm tra đầu), không đợi chia sẻ thành công: chia sẻ lỗi vẫn đếm lại từ 0."""
        flow = [Step("16_boss_gone_summon.png", tap(c.SUMMON)), Step("09_viking_map_0.png", end_())]
        with mock.patch.object(viking, "_ask_for_help", return_value="asked"),                 mock.patch.object(viking, "_share_boss", return_value="failed"):
            device = run_flow(self, _run, SCREENS, flow, {"viking_level": "Easy"},
                              setup=lambda ctx: setattr(ctx, c.CHECKS_ATTR, 2))
        self.assertEqual(getattr(device.ctx, c.CHECKS_ATTR), 0)

    def test_waits_through_white_fog_until_dots_button(self):
        """Từ thành ra thế giới: màn trắng, màn trắng, sương, bản đồ (ảnh thật 07_after_summon_1..4). Chờ tới khi thấy nút "•••" (khung thứ 4)
        mới xong: tiêu đề Viking mất ngay ở màn trắng nên không dùng làm mốc. Chưa thấy thì không bấm gì."""
        import cv2
        frames = [cv2.imread(str(SCREENS / f"07_after_summon_{i}.png")) for i in (1, 2, 3, 4)]
        bot = _screen_bot(frames)
        self.assertTrue(viking._wait_map(bot))
        self.assertEqual(bot.screenshot.call_count, 4)
        bot.tap.assert_not_called()
        bot.back.assert_not_called()

    def test_already_on_world_map_is_ready_at_once(self):
        """Đã ở thế giới nên không có sương: thấy "•••" ở lần nhìn đầu là xong, không chờ."""
        import cv2
        bot = _screen_bot([cv2.imread(str(SCREENS / "09_viking_map_0.png"))])
        self.assertTrue(viking._wait_map(bot))
        self.assertEqual(bot.screenshot.call_count, 1)
        bot.sleep.assert_not_called()

    def test_popup_is_closed_before_dots_button_counts(self):
        """Thấy ảnh click thì bấm, ảnh exit thì Back (ưu tiên hơn "•••"), cho tới khi thấy "•••" lần đầu."""
        import cv2
        shot = cv2.imread(str(SCREENS / "09_viking_map_0.png"))
        bot = _screen_bot([shot, shot, shot])
        answers = iter([(c.TAP, (10, 20)), (c.BACK, (30, 40)), (c.ON_MAP, (1, 1))])
        with mock.patch.object(viking, "find_first", side_effect=lambda *a, **k: next(answers)):
            self.assertTrue(viking._wait_map(bot))
        bot.tap.assert_called_once_with(10, 20, delay=1)
        bot.back.assert_called_once()

    def test_map_never_ready_gives_up(self):
        """Màn trắng mãi: hết MAP_READY_STEPS bước thì False (mỗi bước chờ 1 giây)."""
        import cv2
        bot = _screen_bot([cv2.imread(str(SCREENS / "07_after_summon_1.png"))] * c.MAP_READY_STEPS)
        self.assertFalse(viking._wait_map(bot))
        self.assertEqual(bot.sleep.call_count, c.MAP_READY_STEPS)

    def _share_state(self):
        return {"need_share": False, "share_tries": 0, "asked": False}

    def _patched_share(self, results, find):
        """Các hàm bên trong _share được giả: chia sẻ lần lượt trả `results`, tìm boss trả lần lượt `find` (None = không thấy)."""
        return (mock.patch.object(viking, "_find_viking", side_effect=find),
                mock.patch.object(viking, "_ask_for_help", return_value="already"),
                mock.patch.object(viking, "_wait_map", return_value=True),
                mock.patch.object(viking, "_share_boss", side_effect=results))

    def test_share_failed_is_retried_up_to_3_times(self):
        """Chia sẻ chưa được (VD bấm trượt boss): về bản đồ sạch, tìm lại boss, chia sẻ lại; thành công ở lần nào thì dừng ở đó."""
        bot, state = mock.Mock(), self._share_state()
        find, ask, wait_map, share = self._patched_share(["failed", "failed", "shared"], [(190, 333)] * 3)
        with find, ask, wait_map as wm, share as sh:
            self.assertTrue(viking._share(bot, state))
            self.assertEqual(sh.call_count, 3)
            self.assertEqual(wm.call_count, 2)                 # về bản đồ sạch sau mỗi lần lỗi
        self.assertFalse(state["need_share"])
        self.assertEqual(getattr(bot, c.CHECKS_ATTR), 0)

    def test_share_gives_up_after_3_failures(self):
        bot, state = mock.Mock(spec=[]), self._share_state()
        bot.record = bot.log = mock.Mock()
        find, ask, wait_map, share = self._patched_share(["failed"] * 3, [(190, 333)] * 3)
        with find, ask, wait_map, share as sh:
            self.assertTrue(viking._share(bot, state))          # hết lượt thử thì thôi
            self.assertEqual(sh.call_count, c.SHARE_TRIES)
        self.assertFalse(state["need_share"])
        self.assertFalse(hasattr(bot, c.CHECKS_ATTR))           # chưa chia sẻ được: không đặt lại bộ đếm

    def test_boss_not_found_on_retry_goes_back_to_press_go(self):
        """Chia sẻ lỗi, về bản đồ sạch mà không thấy boss: không bấm mò, trả False để quay lại màn Viking bấm Go (camera vào đúng boss); còn
        need_share nên lần ở màn Viking bấm Go ngay (không đợi đếm lần kiểm tra) và chia sẻ tiếp từ lần thử thứ 2."""
        bot, state = mock.Mock(), self._share_state()
        find, ask, wait_map, share = self._patched_share(["failed"], [(198, 352), None])
        with find as fv, ask, wait_map, share:
            self.assertFalse(viking._share(bot, state))
            self.assertEqual([call.kwargs["fallback"] for call in fv.call_args_list], [True, False])   # lần đầu bấm giữa màn, sau đó thì không
        self.assertTrue(state["need_share"])
        self.assertEqual(state["share_tries"], 1)
        flow = [Step("10_live_end.png", tap(c.GO)), Step("09_viking_map_0.png", end_())]
        with mock.patch.object(viking, "_ask_for_help", return_value="already"),                 mock.patch.object(viking, "_share_boss", return_value="shared") as sh:
            def run_with_state(bot, settings):
                bot.viking_checks = 0   # đang đếm dở: bình thường chưa tới lần kiểm tra thứ 4 nên chỉ xem
                return viking._viking(bot, "Easy", state)
            run_flow(self, run_with_state, SCREENS, flow, {})
            sh.assert_called_once()
        self.assertFalse(state["need_share"])

    def test_ask_for_help_flow(self):
        """Bấm boss -> menu nhanh: Attack -> cửa sổ boss: Ask for Help -> hộp thoại (tốn 1 Viking Poleaxe): Confirm -> nhãn thành "Asking for help"."""
        flow = [
            Step("09_viking_map_0.png", tap_at(196, 333)),
            Step("15_quick_menu.png", tap_at(100, 261, tol=25)),
            Step("13_boss_popup.png", tap(c.ASK_FOR_HELP)),
            Step("14_ask_help_dialog.png", tap(c.POPUP_CONFIRM)),
            Step("11_asking_for_help_map.png", end_("asked")),
        ]
        run_flow(self, lambda bot, s: viking._ask_for_help(bot, (196, 333)), SCREENS, flow, {})

    def test_already_asking_for_help_is_not_asked_again(self):
        """Nhãn đã "Viking(Asking for help)": không bấm gì (mỗi lần nhờ tốn 1 Viking Poleaxe); _share vẫn chia sẻ."""
        run_flow(self, lambda bot, s: viking._ask_for_help(bot, (196, 333)), SCREENS,
                 [Step("11_asking_for_help_map.png", end_("already"))], {})

    def test_viking_nearest_to_center_is_shared(self):
        """Hai nhãn Viking trên bản đồ: chia sẻ cái gần giữa màn hình."""
        import cv2
        shot = cv2.imread(str(SCREENS / "09_viking_map_0.png"))
        far = shot.copy()
        far[480:530, 20:130] = shot[318:368, 170:280]   # nhãn Viking thứ hai ở góc dưới trái
        names = [(95, 495), (190, 333)]
        bot = mock.Mock()
        bot.screenshot.return_value = far
        bot.find_all.side_effect = lambda template, **kw: names if template == c.BOSS_NAME else []
        self.assertEqual(viking._find_viking(bot), (190, 333))


    def test_no_viking_label_taps_screen_center(self):
        """Không thấy nhãn Viking sau BOSS_NAME_TRIES lần kiểm tra (mỗi lần chờ 1 giây): bấm giữa màn hình, không bấm sớm hơn."""
        import numpy as np
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), np.uint8)
        bot.find_all.return_value = []
        self.assertEqual(viking._find_viking(bot), (198, 352))
        self.assertEqual(bot.sleep.call_count, c.BOSS_NAME_TRIES)


class WindowTests(unittest.TestCase):
    def test_window_monday_to_thursday_at_reset(self):
        """Từ 14:00 thứ 2 tới 14:00 thứ 5 (giờ reset)."""
        monday = datetime(2026, 10, 26)
        self.assertFalse(viking.in_window(monday.replace(hour=13, minute=59), "14:00"))
        self.assertTrue(viking.in_window(monday.replace(hour=14), "14:00"))
        self.assertTrue(viking.in_window(monday + timedelta(days=2, hours=23), "14:00"))   # thứ 4 23:00
        self.assertTrue(viking.in_window(monday + timedelta(days=3, hours=13, minutes=59), "14:00"))
        self.assertFalse(viking.in_window(monday + timedelta(days=3, hours=14), "14:00"))   # thứ 5 14:00
        self.assertFalse(viking.in_window(monday + timedelta(days=6, hours=20), "14:00"))   # chủ nhật

    def test_window_follows_reset_time(self):
        monday = datetime(2026, 10, 26)
        self.assertTrue(viking.in_window(monday.replace(hour=9), "08:30"))
        self.assertFalse(viking.in_window(monday.replace(hour=9), "14:00"))

    def test_due_needs_enabled_window_and_interval(self):
        ctx = mock.Mock(spec=["server_time"], server_time=lambda: "14:00")   # mới Start: chưa có giờ kiểm tra
        boss = [{"category_key": "x", "name": "Viking", "levels": []}]
        on, off = {"viking_summon": True, "selected_bosses": boss}, {"viking_summon": False, "selected_bosses": boss}
        self.assertFalse(viking.summon_enabled({"viking_summon": True, "selected_bosses": []}))   # chưa chọn đánh boss Viking
        with mock.patch.object(viking, "datetime", wraps=datetime) as clock:
            clock.now.return_value = datetime(2026, 10, 27, 10)   # thứ 3
            self.assertTrue(viking._due(ctx, on))
            self.assertFalse(viking._due(ctx, off))
            ctx.viking_last_check = datetime(2026, 10, 27, 9, 55)
            self.assertFalse(viking._due(ctx, on))                # mới thử 5 phút trước (< 8)
            ctx.viking_last_check = datetime(2026, 10, 27, 9, 45)
            self.assertTrue(viking._due(ctx, on))
            clock.now.return_value = datetime(2026, 10, 31, 10)   # thứ 7: ngoài cửa sổ
            self.assertFalse(viking._due(ctx, on))


def end_(*result):
    from tests.flow import end
    return end(*result)


if __name__ == "__main__":
    unittest.main()
