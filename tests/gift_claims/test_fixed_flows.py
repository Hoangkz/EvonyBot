import unittest
from importlib import import_module
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import cv2
import numpy as np

from bot.activities import gift_claims
from bot.activities.gift_claims import common, lobby
from bot.activities.gift_claims.screens import GiftScreen, TITLE_TEMPLATES, identify
from bot.context.errors import TimedOut

event_center = import_module("bot.activities.gift_claims.event_center.run")
event_center_zone = import_module("bot.activities.gift_claims.event_center.zone")
dragon_battle = import_module(
    "bot.activities.gift_claims.event_center.dragon_battle.run")
valuable_event = import_module("bot.activities.gift_claims.valuable_event.run")
valuable_event_zone = import_module("bot.activities.gift_claims.valuable_event.zone")
valuable_named_flow = import_module(
    "bot.activities.gift_claims.valuable_event.named_flow.run")
ancient_dynasty_treasury = import_module(
    "bot.activities.gift_claims.valuable_event.ancient_dynasty_treasury.run")
back_to_territory = import_module(
    "bot.activities.gift_claims.back_to_territory.run")
empire_depot = import_module("bot.activities.gift_claims.super_value_return.empire_depot.run")
limited_offer = import_module("bot.activities.gift_claims.valuable_event.limited_offer.run")
login_gifts = import_module("bot.activities.gift_claims.super_value_return.login_gifts.run")
resource_consumption_sprint = import_module(
    "bot.activities.gift_claims.valuable_event.resource_consumption_sprint.run")
super_blazon_sale = import_module(
    "bot.activities.gift_claims.valuable_event.super_blazon_sale.run")
strategic_stockpile = import_module(
    "bot.activities.gift_claims.valuable_event.strategic_stockpile.run")
runestone_consumption_sprint = import_module(
    "bot.activities.gift_claims.valuable_event.runestone_consumption_sprint.run")
speedup_sprint = import_module(
    "bot.activities.gift_claims.valuable_event.speedup_sprint.run")
wheel_of_dragon_war = import_module(
    "bot.activities.gift_claims.valuable_event.wheel_of_dragon_war.run")
refining_weekly_card = import_module(
    "bot.activities.gift_claims.super_value_return.refining_weekly_card.run")
super_value_return = import_module(
    "bot.activities.gift_claims.super_value_return.run")
super_value_zone = import_module(
    "bot.activities.gift_claims.super_value_return.zone")


ROOT = Path(__file__).parents[2]
IMAGES = ROOT / "Images"


class CvBot:
    @staticmethod
    def log(_message):
        pass

    def _template(self, name):
        image = cv2.imread(str(IMAGES / name))
        if image is None:
            raise FileNotFoundError(name)
        return image

    @staticmethod
    def find(template, threshold=0.8, screen=None, center=True, region=None):
        if region is not None:
            height, width = screen.shape[:2]
            x0, y0, x1, y1 = region
            left, top = int(width * x0 / 100), int(height * y0 / 100)
            area = screen[top:int(height * y1 / 100), left:int(width * x1 / 100)]
        else:
            area, left, top = screen, 0, 0
        result = cv2.matchTemplate(area, template, cv2.TM_CCOEFF_NORMED)
        _, score, _, (x, y) = cv2.minMaxLoc(result)
        if score < threshold:
            return None
        return left + x + template.shape[1] // 2, top + y + template.shape[0] // 2


class FixedGiftFlowTests(unittest.TestCase):
    def setUp(self):
        self.bot = CvBot()

    def test_every_fixed_inner_title_is_identified(self):
        for expected, name in TITLE_TEMPLATES.items():
            with self.subTest(screen=expected.value):
                template = cv2.imread(str(IMAGES / "GiftClaims" / f"{name}.png"))
                screen = np.zeros((704, 396, 3), dtype=np.uint8)
                height, width = template.shape[:2]
                screen[5:5 + height, 40:40 + width] = template
                self.assertEqual(expected, identify(self.bot, screen))

    def test_unknown_inner_screen_is_not_guessed(self):
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        self.assertIsNone(identify(self.bot, screen))

    def test_dragon_battle_new_reward_crop_has_supplied_dimensions(self):
        reward = cv2.imread(str(
            IMAGES / "GiftClaims" / "EventCenter" / "DragonBattle" / "reward_230317.png"))
        claimed = cv2.imread(str(
            IMAGES / "GiftClaims" / "EventCenter" / "DragonBattle" /
            "status_reward_claimed.png"))
        self.assertEqual((25, 33), reward.shape[:2])
        self.assertEqual((34, 40), claimed.shape[:2])

    def test_dragon_battle_is_done_only_after_congratulations(self):
        bot = mock.Mock()
        wait = lambda _bot, name, **_kwargs: (
            None if name == "EventCenter/DragonBattle/status_reward_claimed" else (210, 500))
        with (mock.patch.object(event_center, "_wait_for",
                                side_effect=wait),
              mock.patch.object(event_center, "close_congratulations",
                                return_value=True)):
            report, done = event_center._handle_dragon_battle(bot)

        self.assertTrue(done)
        self.assertEqual(common.ClaimReport(1, 1), report)
        bot.tap.assert_called_once_with(
            210, 500, delay=event_center.UI_SETTLE_SECONDS)

    def test_dragon_battle_stays_pending_without_congratulations(self):
        bot = mock.Mock()
        wait = lambda _bot, name, **_kwargs: (
            None if name == "EventCenter/DragonBattle/status_reward_claimed" else (210, 500))
        with (mock.patch.object(event_center, "_wait_for",
                                side_effect=wait),
              mock.patch.object(event_center, "close_congratulations",
                                return_value=False)):
            report, done = event_center._handle_dragon_battle(bot)

        self.assertFalse(done)
        self.assertEqual(common.ClaimReport(1, 0), report)

    def test_dragon_battle_claimed_chest_is_done_without_tapping(self):
        bot = mock.Mock()
        with mock.patch.object(event_center, "_wait_for",
                               return_value=(210, 500)):
            report, done = event_center._handle_dragon_battle(bot)

        self.assertTrue(done)
        self.assertEqual(common.ClaimReport(0, 1), report)
        bot.tap.assert_not_called()

    def test_dragon_battle_standalone_run_requires_congratulations(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.screenshot.return_value = screen
        with (mock.patch.object(dragon_battle, "open_event_center_event",
                                return_value=True),
              mock.patch.object(dragon_battle, "find",
                                side_effect=lambda _bot, name, *_args, **_kwargs:
                                None if name == "EventCenter/DragonBattle/status_reward_claimed"
                                else (210, 500)),
              mock.patch.object(dragon_battle, "close_congratulations",
                                return_value=False)):
            done = dragon_battle.run(bot)

        self.assertFalse(done)

    def test_lobby_waits_for_delayed_fixed_inner_title(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(lobby, "return_home", return_value=True),
              mock.patch.object(lobby, "red_dots", return_value=[(60, 520)]),
              mock.patch.object(lobby, "identify",
                                side_effect=(None, None,
                                             GiftScreen.VALUABLE_EVENT)) as identify_screen):
            result = lobby.open_next(bot, lobby.BOTTOM, [])

        self.assertEqual(GiftScreen.VALUABLE_EVENT, result)
        self.assertEqual(identify_screen.call_count, 3)
        # One lobby-settle pause plus two title-loading retries.
        self.assertEqual(bot.sleep.call_count, 3)

    def test_lobby_uses_two_red_dot_boundaries(self):
        self.assertEqual((lobby.BOTTOM, lobby.RIGHT), lobby.BOUNDARIES)
        self.assertEqual(100, lobby.REGIONS[lobby.RIGHT][2])

    def test_lobby_valuable_event_finder_uses_ocr_caption(self):
        # Hàm cũ (ảnh launcher_*) đã xoá: lobby dùng bot/ocr/find_valuable_event, quy về chỗ cao hơn tâm chữ "Event" 10 px.
        screen = cv2.imread(str(Path(__file__).parent / "screens" / "lobby_valuable_event_done.png"))
        x, y = lobby.find_valuable_event(self.bot, screen)
        self.assertAlmostEqual(260, x, delta=4)
        self.assertAlmostEqual(580, y, delta=4)

    def test_named_valuable_event_uses_dedicated_caption_finder(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(lobby, "return_home", return_value=True),
              mock.patch.object(lobby, "identify",
                                side_effect=(None, GiftScreen.VALUABLE_EVENT)),
              mock.patch.object(lobby, "find_valuable_event",
                                return_value=(264, 590)) as finder):
            self.assertTrue(lobby.open_named(bot, GiftScreen.VALUABLE_EVENT))

        finder.assert_called_once()
        bot.tap.assert_called_once_with(264, 570, delay=1)

    def test_named_valuable_event_repositions_city_before_retry(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(lobby, "return_home", return_value=True),
              mock.patch.object(lobby, "identify",
                                side_effect=(None, None,
                                             GiftScreen.VALUABLE_EVENT)),
              mock.patch.object(lobby, "find_valuable_event",
                                side_effect=(None, (264, 590))) as finder,
              mock.patch.object(lobby, "swipe_around") as reposition):
            self.assertTrue(lobby.open_named(bot, GiftScreen.VALUABLE_EVENT))

        self.assertEqual(2, finder.call_count)
        reposition.assert_called_once_with(bot)
        bot.tap.assert_called_once_with(264, 570, delay=1)

    def test_named_valuable_event_uses_approved_fixed_fallback(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(lobby, "return_home", return_value=True),
              mock.patch.object(lobby, "identify",
                                side_effect=(None, None, None,
                                             GiftScreen.VALUABLE_EVENT)),
              mock.patch.object(lobby, "find_valuable_event",
                                return_value=None),
              mock.patch.object(lobby, "swipe_around")):
            self.assertTrue(lobby.open_named(bot, GiftScreen.VALUABLE_EVENT))

        bot.tap.assert_called_once_with(255, 566, delay=1)
        self.assertTrue(any(
            "bấm fallback x=255 y=566" in call.args[0]
            for call in bot.record.call_args_list))

    def test_named_valuable_event_uses_super_value_gateway_when_missing(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(lobby, "return_home", return_value=True),
              mock.patch.object(lobby, "OPEN_WAIT_ATTEMPTS", 1),
              mock.patch.object(lobby, "identify",
                                side_effect=(None, None, None, None, None,
                                             GiftScreen.SUPER_VALUE_RETURN)),
              mock.patch.object(lobby, "find_valuable_event",
                                return_value=None) as finder,
              mock.patch.object(lobby, "find", return_value=(30, 560)),
              mock.patch.object(lobby, "swipe_around"),
              mock.patch.object(lobby, "_switch_parent_carousel",
                                return_value=True) as switch):
            self.assertTrue(lobby.open_named(bot, GiftScreen.VALUABLE_EVENT))

        self.assertEqual(lobby.VALUABLE_LAUNCH_ATTEMPTS, finder.call_count)
        switch.assert_called_once_with(bot, GiftScreen.VALUABLE_EVENT)
        self.assertTrue(any(
            "thử mở qua SuperValueReturn" in call.args[0]
            for call in bot.record.call_args_list))
        self.assertTrue(any(
            "đã chuyển SuperValueReturn -> ValuableEvent" in call.args[0]
            for call in bot.record.call_args_list))

    @staticmethod
    def _daily_bot():
        done = {}
        bot = mock.Mock()
        bot.is_daily_done.side_effect = done.__contains__
        bot.mark_daily_done.side_effect = lambda key: done.__setitem__(key, "now")
        bot.done_at.side_effect = done.get
        bot.forget_daily.side_effect = lambda key: done.pop(key, None)
        return bot, done

    @staticmethod
    def _passes_seeing(*per_pass):
        """search_pass giả: lượt thứ i coi như thấy (bấm vào) các event per_pass[i]."""
        passes = iter(per_pass)

        def search(_bot, _pending, attempted):
            attempted.update(next(passes, ()))
            return True
        return search

    def test_valuable_zone_new_event_resets_pass_count(self):
        # Lượt 1 không thấy gì; lượt 2 thấy A (mới) -> lượt 2 tính lại là lượt 1; thêm 2 lượt trống nữa mới đủ 3.
        bot, done = self._daily_bot()
        with (mock.patch.object(valuable_event_zone, "search_pass",
                                side_effect=self._passes_seeing((), ("A",), (), ())) as search,
              mock.patch.object(valuable_event_zone, "return_home", return_value=True)):
            self.assertTrue(valuable_event_zone.run(bot))
        self.assertEqual(4, search.call_count)
        self.assertIn(valuable_event_zone.KEY, done)

    def test_valuable_zone_remembers_seen_events_after_interruption(self):
        # Lần chạy 1: lượt 1 thấy A, lượt 2 trống, lượt 3 dở (bị ngắt). Lần chạy 2 thấy lại A: A đã thấy hôm nay (nhớ trên
        # context) nên không reset, xong lượt 3 luôn.
        bot, done = self._daily_bot()
        bot.server_time.return_value = "14:00"
        sees = iter([("A",), (), None, ("A",)])

        def search(_bot, _pending, attempted):
            seen = next(sees)
            if seen is None:
                return False
            attempted.update(seen)
            return True
        with (mock.patch.object(valuable_event_zone, "search_pass", side_effect=search) as search_pass,
              mock.patch.object(valuable_event_zone, "return_home", return_value=True)):
            self.assertFalse(valuable_event_zone.run(bot))
            self.assertTrue(valuable_event_zone.run(bot))
        self.assertEqual(4, search_pass.call_count)
        self.assertIn(valuable_event_zone.KEY, done)

    def test_seen_today_lives_on_context_and_clears_at_new_reset(self):
        bot = mock.Mock()
        bot.server_time.return_value = "14:00"
        valuable_event_zone.seen_today(bot).add("A")
        self.assertIn("A", valuable_event_zone.seen_today(bot))
        with mock.patch.object(valuable_event_zone, "last_reset", return_value="ngày mới"):
            self.assertEqual(set(), valuable_event_zone.seen_today(bot))

    def test_valuable_zone_same_event_every_pass_resets_only_once(self):
        # A lượt nào cũng thấy mà chưa DONE: chỉ reset lần đầu thấy, không lặp mãi.
        bot, done = self._daily_bot()
        with (mock.patch.object(valuable_event_zone, "search_pass",
                                side_effect=self._passes_seeing(("A",), ("A",), ("A",))) as search,
              mock.patch.object(valuable_event_zone, "return_home", return_value=True)):
            self.assertTrue(valuable_event_zone.run(bot))
        self.assertEqual(3, search.call_count)

    def test_valuable_zone_three_passes_then_marks_every_event_done(self):
        bot, done = self._daily_bot()
        with (mock.patch.object(valuable_event_zone, "search_pass", return_value=True) as search,
              mock.patch.object(valuable_event_zone, "return_home", return_value=True)):
            self.assertTrue(valuable_event_zone.run(bot))

        self.assertEqual(3, search.call_count)
        self.assertEqual(3, bot.back.call_count)          # Back sau mỗi lượt rồi làm lại từ màn chính
        for number in (1, 2, 3):
            self.assertIn(f"gift_valuable_event_pass_{number}", done)
        for task in valuable_event_zone.TASKS:
            self.assertIn(task.key, done)
        self.assertIn(valuable_event_zone.KEY, done)

    def test_valuable_zone_continues_counting_passes_from_db(self):
        bot, done = self._daily_bot()
        done.update({"gift_valuable_event_pass_1": "x", "gift_valuable_event_pass_2": "x"})
        with (mock.patch.object(valuable_event_zone, "search_pass", return_value=True) as search,
              mock.patch.object(valuable_event_zone, "return_home", return_value=True)):
            self.assertTrue(valuable_event_zone.run(bot))
        self.assertEqual(1, search.call_count)

    def test_valuable_zone_unfinished_pass_is_not_counted(self):
        bot, done = self._daily_bot()
        with (mock.patch.object(valuable_event_zone, "search_pass", return_value=False),
              mock.patch.object(valuable_event_zone, "return_home", return_value=True)):
            self.assertFalse(valuable_event_zone.run(bot))
        self.assertNotIn("gift_valuable_event_pass_1", done)
        self.assertNotIn(valuable_event_zone.KEY, done)

    def _visible_spec_patches(self, spec, opened):
        return (mock.patch.object(valuable_event_zone, "back_if_close_x", return_value=False),
                mock.patch.object(valuable_event_zone, "_tab",
                                  side_effect=lambda _b, s, _screen: (120, 80) if s is spec else None),
                mock.patch.object(valuable_event_zone, "open_tab", return_value=opened),
                mock.patch.object(valuable_event_zone, "process_exact", return_value=True))

    def test_do_visible_opens_tab_then_runs_event_flow(self):
        bot, done = self._daily_bot()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        spec = valuable_event_zone.SPECS[0]
        back, tab, opened, flow = self._visible_spec_patches(spec, opened=True)
        with back, tab, opened as open_tab, flow as process:
            valuable_event_zone.do_visible(bot, {spec.task.key}, set())
        open_tab.assert_called_once_with(bot, (120, 80))
        process.assert_called_once_with(bot, spec.flow)
        self.assertIn(spec.task.key, done)

    def test_do_visible_skips_event_when_tab_never_opens(self):
        bot, done = self._daily_bot()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        spec = valuable_event_zone.SPECS[0]
        pending, attempted = {spec.task.key}, set()
        back, tab, opened, flow = self._visible_spec_patches(spec, opened=False)
        with back, tab, opened, flow as process:
            valuable_event_zone.do_visible(bot, pending, attempted)
        process.assert_not_called()
        self.assertIn(spec.task.key, pending)       # vẫn PENDING: lượt sau làm tiếp
        self.assertIn(spec.task.key, attempted)     # không bấm lại trong lượt này
        self.assertNotIn(spec.task.key, done)

    def test_open_tab_taps_tab_and_top_center_then_waits_for_page_change(self):
        rng = np.random.default_rng(4)
        same = rng.integers(0, 255, (704, 396, 3), dtype=np.uint8)
        changed = same.copy()
        changed[140:211, 8:118] = rng.integers(0, 255, (71, 110, 3), dtype=np.uint8)   # ô PAGE_PROBE đổi
        bot = mock.Mock()
        calls = []
        bot.tap.side_effect = lambda *a, **k: calls.append(("tap", a))
        bot.tap_percent.side_effect = lambda *a, **k: calls.append(("tap_percent", a))
        bot.screenshot.side_effect = (same, same, same, changed)     # trước bấm, 1s, 2s, 3s đã sang
        with mock.patch.object(valuable_event_zone, "tab_selected", return_value=False):
            self.assertTrue(valuable_event_zone.open_tab(bot, (120, 80)))
        self.assertEqual([("tap", (120, 80)), ("tap_percent", (50, 5))], calls)
        self.assertEqual(3, bot.sleep.call_count)

    def test_tab_uses_text_free_icon_or_text_for_events_without_icon(self):
        icon_spec = next(s for s in valuable_event.SPECS if "/LimitedOffer/" in s.tab)
        text_spec = next(s for s in valuable_event.SPECS if "/TombExpedition/" in s.tab)
        self.assertEqual("ValuableEvent/LimitedOffer/tab_icon", icon_spec.tab)
        self.assertEqual("ValuableEvent/TombExpedition/tab", text_spec.tab)     # chưa có icon: ảnh có chữ
        calls = []

        def find(_b, name, _screen, threshold, region):
            calls.append((name, threshold))
            return (178, 77)
        with mock.patch.object(valuable_event, "find", side_effect=find):
            self.assertEqual((178, 77), valuable_event._tab(self.bot, icon_spec, None))
            self.assertEqual((178, 77), valuable_event._tab(self.bot, text_spec, None))
        self.assertEqual([("ValuableEvent/LimitedOffer/tab_icon", valuable_event.ICON_TAB_THRESHOLD),
                          ("ValuableEvent/TombExpedition/tab", valuable_event.TASK_TAB_THRESHOLD)], calls)

    def test_every_specs_tab_image_exists(self):
        for spec in valuable_event.SPECS:
            with self.subTest(tab=spec.tab):
                self.assertTrue((IMAGES / "GiftClaims" / f"{spec.tab}.png").exists())

    def test_super_blazon_icon_needs_its_label_in_same_column(self):
        # Icon Super Blazon Sale giống hệt Journey to Glory: chỉ nhận khi chữ tên Super Blazon nằm cùng cột.
        spec = next(s for s in valuable_event.SPECS if "/SuperBlazonSale/" in s.tab)
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        for label, expected in (((221, 85), (221, 77)), (None, None), ((90, 85), None)):
            hits = {"ValuableEvent/SuperBlazonSale/tab_icon": (221, 77),
                    "ValuableEvent/SuperBlazonSale/tab_current": label}
            with self.subTest(label=label), mock.patch.object(
                    valuable_event, "find", side_effect=lambda _b, name, *a, **k: hits.get(name)):
                self.assertEqual(expected, valuable_event._tab(self.bot, spec, screen))

    def test_find_notice_x_only_on_marquee_close_button(self):
        screens = Path(__file__).parent / "screens"
        marquee = cv2.imread(str(screens / "valuable_event_notice_marquee.png"))
        x, y = valuable_event_zone.find_notice_x(marquee)
        self.assertAlmostEqual(321, x, delta=3)
        self.assertAlmostEqual(104, y, delta=3)
        for clean in ("valuable_event_tab_limited_offer_selected.png", "valuable_event_tab_general_vault_selected.png",
                      "lobby_valuable_event_done.png"):
            with self.subTest(screen=clean):
                self.assertIsNone(valuable_event_zone.find_notice_x(cv2.imread(str(screens / clean))))

    def test_settled_screenshot_taps_notice_x_after_swipe(self):
        marquee = cv2.imread(str(Path(__file__).parent / "screens" / "valuable_event_notice_marquee.png"))
        cleared = np.zeros_like(marquee)
        bot = mock.Mock()
        bot.screenshot.side_effect = (marquee, cleared)
        self.assertIs(cleared, valuable_event_zone._settled_screenshot(bot))
        (x, y), _ = bot.tap.call_args
        self.assertAlmostEqual(321, x, delta=3)
        self.assertEqual(2, bot.sleep.call_count)                 # nghỉ 1s sau cú kéo + 1s sau khi bấm X

    def test_tab_selected_reads_lighter_background_on_real_screens(self):
        screens = Path(__file__).parent / "screens"
        limited = cv2.imread(str(screens / "valuable_event_tab_limited_offer_selected.png"))
        vault = cv2.imread(str(screens / "valuable_event_tab_general_vault_selected.png"))
        self.assertTrue(valuable_event_zone.tab_selected(limited, (174, 85)))      # Limited Offer đang chọn
        self.assertFalse(valuable_event_zone.tab_selected(limited, (72, 94)))      # Speedup Sprint
        self.assertTrue(valuable_event_zone.tab_selected(vault, (310, 85)))        # General Vault đang chọn
        self.assertFalse(valuable_event_zone.tab_selected(vault, (210, 85)))       # All-Out Preparation

    def test_open_tab_does_not_tap_already_selected_tab(self):
        screen = cv2.imread(str(Path(__file__).parent / "screens" /
                                "valuable_event_tab_limited_offer_selected.png"))
        bot = mock.Mock()
        bot.screenshot.return_value = screen
        self.assertTrue(valuable_event_zone.open_tab(bot, (174, 85)))
        bot.tap.assert_not_called()
        bot.sleep.assert_not_called()

    def test_open_tab_retaps_once_then_gives_up(self):
        same = np.random.default_rng(5).integers(0, 255, (704, 396, 3), dtype=np.uint8)
        bot = mock.Mock()
        bot.screenshot.return_value = same
        with mock.patch.object(valuable_event_zone, "tab_selected", return_value=False):
            self.assertFalse(valuable_event_zone.open_tab(bot, (120, 80)))
        self.assertEqual(2, bot.tap.call_count)                       # bấm + bấm lại 1 lần
        self.assertEqual(2 * 5, bot.sleep.call_count)                 # mỗi lần chờ tối đa 5 x 1s

    def test_search_pass_order_visible_then_long_swipe_then_short_scan(self):
        bot = mock.Mock()
        calls = []
        with (mock.patch.object(valuable_event_zone, "open_valuable_event",
                                side_effect=lambda b: calls.append("open") or True),
              mock.patch.object(valuable_event_zone, "capture_title",
                                side_effect=lambda b: calls.append("title")),
              mock.patch.object(valuable_event_zone, "do_visible",
                                side_effect=lambda *a: calls.append("visible")),
              mock.patch.object(valuable_event_zone, "swipe_to_left_edge",
                                side_effect=lambda *a: calls.append("long") or True),
              mock.patch.object(valuable_event_zone, "scan_to_right_edge",
                                side_effect=lambda *a: calls.append("short") or True)):
            self.assertTrue(valuable_event_zone.search_pass(bot, {"gift_limited_offer"}, set()))
        # Vừa vào màn thì cắt thanh tiêu đề làm mốc, trước mọi cú kéo.
        self.assertEqual(["open", "title", "visible", "long", "visible", "short"], calls)

    def test_scan_to_right_edge_stops_only_when_leftmost_icon_stays_in_place(self):
        # Mỗi cú: (chụp trước, chụp sau). Cú 1: khác hẳn -> kéo tiếp; cú 2: chỉ dịch 10 px (icon ĐỔI CHỖ) -> chưa phải giới hạn;
        # cú 3, 4: đứng nguyên chỗ 2 cú liên tiếp -> chạm bên phải.
        rng = np.random.default_rng(3)
        frame_a = rng.integers(0, 255, (704, 396, 3), dtype=np.uint8)
        frame_b = rng.integers(0, 255, (704, 396, 3), dtype=np.uint8)
        frame_c = np.roll(frame_b, 10, axis=1)
        bot = mock.Mock()
        bot.screenshot.side_effect = (frame_a, frame_b, frame_b, frame_c, frame_c, frame_c, frame_c, frame_c)
        with (mock.patch.object(valuable_event_zone, "do_visible") as visible,
              mock.patch.object(valuable_event_zone, "wait_title_clear", return_value=True) as clear):
            self.assertTrue(valuable_event_zone.scan_to_right_edge(bot, set(), set(), np.zeros((42, 396, 3), dtype=np.uint8)))
        self.assertEqual(4, bot.swipe_percent.call_count)
        bot.swipe_percent.assert_called_with(
            60, 12, 5, 12, duration=valuable_event_zone.SLOW_SWIPE_DURATION)
        self.assertEqual(5, visible.call_count)            # trước mỗi cú + một lần ở biên phải
        self.assertEqual(4, clear.call_count)              # chờ tiêu đề rõ trước mỗi cú

    def test_scan_to_right_edge_one_stuck_swipe_is_not_the_edge(self):
        # Cú 1 không dịch (VD popup sau khi nhận quà chặn), cú 2 lại dịch: chưa phải biên, quét tiếp; cú 3, 4 không dịch -> biên.
        rng = np.random.default_rng(6)
        frame_a = rng.integers(0, 255, (704, 396, 3), dtype=np.uint8)
        frame_b = rng.integers(0, 255, (704, 396, 3), dtype=np.uint8)
        bot = mock.Mock()
        bot.screenshot.side_effect = (frame_a, frame_a, frame_a, frame_b, frame_b, frame_b, frame_b, frame_b)
        with (mock.patch.object(valuable_event_zone, "do_visible"),
              mock.patch.object(valuable_event_zone, "wait_title_clear", return_value=True)):
            self.assertTrue(valuable_event_zone.scan_to_right_edge(bot, set(), set(), np.zeros((42, 396, 3), dtype=np.uint8)))
        self.assertEqual(4, bot.swipe_percent.call_count)

    def test_open_valuable_event_taps_found_caption_and_waits_for_title(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(valuable_event_zone, "on_main", return_value=True),
              mock.patch.object(valuable_event_zone, "to_city", return_value=False),
              mock.patch.object(valuable_event_zone, "find_valuable_event",
                                return_value=(260, 590)),
              mock.patch.object(valuable_event_zone, "identify",
                                side_effect=(None, None, GiftScreen.VALUABLE_EVENT))):
            self.assertTrue(valuable_event_zone.open_valuable_event(bot))

        bot.tap.assert_called_once_with(260, 560)
        self.assertEqual(3, bot.sleep.call_count)
        bot.swipe_percent.assert_not_called()              # kéo dài nằm trong search_pass, sau khi làm event đang thấy

    def test_swipe_to_left_edge_stops_when_cut_icon_is_still_visible(self):
        # Cú 1 -> khung A; cú 2 -> hàng tab khác hẳn (icon cắt từ A mất): kéo tiếp; cú 3 -> hàng tab chỉ dịch 10 px (icon cắt
        # từ B vẫn thấy, lệch chỗ cũng được) = giới hạn.
        rng = np.random.default_rng(1)
        frame_a = rng.integers(0, 255, (704, 396, 3), dtype=np.uint8)
        frame_b = rng.integers(0, 255, (704, 396, 3), dtype=np.uint8)
        bot = mock.Mock()
        bot.screenshot.side_effect = (frame_a, frame_b, np.roll(frame_b, 10, axis=1))
        with mock.patch.object(valuable_event_zone, "wait_title_clear", return_value=True):
            self.assertTrue(valuable_event_zone.swipe_to_left_edge(bot, np.zeros((42, 396, 3), dtype=np.uint8)))
        duration = valuable_event_zone.SLOW_SWIPE_DURATION
        # Cú đầu kéo dài 5% -> 1000%, từ cú thứ 2 kéo ngắn 5% -> 95%.
        self.assertEqual([mock.call(5, 12, 1000, 12, duration=duration),
                          mock.call(5, 12, 95, 12, duration=duration),
                          mock.call(5, 12, 95, 12, duration=duration)],
                         bot.swipe_percent.call_args_list)
        # Mỗi cú kéo nghỉ 1s rồi mới chụp cắt / kiểm tra icon.
        self.assertEqual([mock.call(1.0)] * 3, bot.sleep.call_args_list)

    def test_swipe_to_left_edge_gives_up_after_eight_swipes(self):
        rng = np.random.default_rng(2)
        bot = mock.Mock()
        bot.screenshot.side_effect = [rng.integers(0, 255, (704, 396, 3), dtype=np.uint8) for _ in range(8)]
        with mock.patch.object(valuable_event_zone, "wait_title_clear", return_value=True):
            self.assertFalse(valuable_event_zone.swipe_to_left_edge(bot, np.zeros((42, 396, 3), dtype=np.uint8)))
        self.assertEqual(8, bot.swipe_percent.call_count)

    def test_title_matches_captured_title_but_not_dark_overlay(self):
        screens = Path(__file__).parent / "screens"
        entered = cv2.imread(str(screens / "valuable_event_tab_general_vault_selected.png"))
        later = cv2.imread(str(screens / "valuable_event_tab_limited_offer_selected.png"))   # tab khác, lúc khác
        bot = SimpleNamespace()
        title = valuable_event_zone.capture_title(bot, entered)
        self.assertFalse(hasattr(bot, "_valuable_event_title"))   # chỉ là biến của lượt, không gắn lên bot
        self.assertTrue(valuable_event_zone.title_matches(later, title))
        # Phủ tối chỉ 10% đã không khớp (so chênh lệch điểm ảnh, nhạy độ sáng).
        dimmed = (later.astype(np.float32) * 0.9).astype(np.uint8)
        self.assertFalse(valuable_event_zone.title_matches(dimmed, title))

    def test_wait_title_clear_waits_up_to_five_seconds_without_back(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with mock.patch.object(valuable_event_zone, "title_matches", side_effect=(False, False, True)):
            self.assertTrue(valuable_event_zone.wait_title_clear(bot, None))
        self.assertEqual(2, bot.sleep.call_count)
        bot.back.assert_not_called()

    def test_wait_title_clear_backs_after_five_misses(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with mock.patch.object(valuable_event_zone, "title_matches", side_effect=[False] * 5 + [True]):
            self.assertTrue(valuable_event_zone.wait_title_clear(bot, None))
        self.assertEqual(5, bot.sleep.call_count)
        bot.back.assert_called_once()

    def test_scan_to_right_edge_stops_pass_when_title_stays_covered(self):
        bot = mock.Mock()
        with (mock.patch.object(valuable_event_zone, "do_visible"),
              mock.patch.object(valuable_event_zone, "wait_title_clear", return_value=False)):
            self.assertFalse(valuable_event_zone.scan_to_right_edge(bot, set(), set(), np.zeros((42, 396, 3), dtype=np.uint8)))
        bot.swipe_percent.assert_not_called()

    def test_open_valuable_event_gives_up_for_this_run_after_three_tries(self):
        bot = mock.Mock(spec=["screenshot", "tap", "sleep", "check", "record", "is_daily_done"])
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.is_daily_done.return_value = False
        with (mock.patch.object(valuable_event_zone, "on_main", return_value=True),
              mock.patch.object(valuable_event_zone, "to_city", return_value=False),
              mock.patch.object(valuable_event_zone, "find_valuable_event",
                                return_value=(260, 590)),
              mock.patch.object(valuable_event_zone, "identify", return_value=None)):
            self.assertFalse(valuable_event_zone.open_valuable_event(bot))

        self.assertEqual(3, bot.tap.call_count)
        self.assertEqual(3 * 8, bot.sleep.call_count)
        self.assertTrue(common.skipped_for_run(bot, valuable_event_zone.KEY))
        job = gift_claims.job(gift_claims.valuable_event)
        self.assertTrue(job["done"](bot, {}))

    def test_empire_depot_uses_approved_fixed_fallback_and_verifies_title(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(lobby, "return_home", return_value=True),
              mock.patch.object(lobby, "find", return_value=None),
              mock.patch.object(lobby, "identify",
                                side_effect=(None,
                                             GiftScreen.SUPER_VALUE_RETURN))):
            self.assertTrue(lobby.open_named(bot, GiftScreen.SUPER_VALUE_RETURN))

        bot.tap.assert_called_once_with(30, 560, delay=1)

    def test_lobby_skips_facebook_follow_us_before_opening_next_dot(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.screenshot.return_value = screen
        attempted = []
        with (mock.patch.object(lobby, "return_home", return_value=True),
              mock.patch.object(lobby, "red_dots",
                                return_value=[(380, 200), (380, 235),
                                              (380, 275)]),
              mock.patch.object(lobby, "find_all", return_value=[(360, 215)]),
              mock.patch.object(lobby, "identify",
                                return_value=GiftScreen.EVENT_CENTER)):
            result = lobby.open_next(bot, lobby.RIGHT, attempted)

        self.assertEqual(GiftScreen.EVENT_CENTER, result)
        self.assertEqual([(380, 200), (380, 235), (380, 275)], attempted)

    def test_zone_two_prioritizes_event_center_badge(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.screenshot.return_value = screen
        attempted = []

        def find_all_named(_bot, name, *_args, **_kwargs):
            if name == "EventCenter/launcher_side":
                return [(350, 270)]
            return []

        with (mock.patch.object(lobby, "return_home", return_value=True),
              mock.patch.object(lobby, "red_dots",
                                return_value=[(380, 180), (380, 275)]),
              mock.patch.object(lobby, "find_all", side_effect=find_all_named),
              mock.patch.object(lobby, "identify",
                                return_value=GiftScreen.EVENT_CENTER)):
            result = lobby.open_next(bot, lobby.RIGHT, attempted)

        self.assertEqual(GiftScreen.EVENT_CENTER, result)
        self.assertEqual((380, 275), attempted[0])
        bot.tap.assert_called_once_with(355, 291, delay=1)

    def test_red_dot_detector_separates_bottom_then_right(self):
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        cv2.circle(screen, (60, 530), 10, (0, 40, 190), thickness=-1)
        cv2.circle(screen, (380, 200), 10, (0, 40, 190), thickness=-1)
        cv2.circle(screen, (295, 40), 10, (0, 40, 190), thickness=-1)
        self.assertEqual([(60, 530)], lobby.red_dots(screen, lobby.BOTTOM))
        self.assertEqual([(380, 200)], lobby.red_dots(screen, lobby.RIGHT))

    def test_right_rail_merges_artwork_fragment_with_real_badge(self):
        points = [(361, 142), (382, 137), (382, 275)]
        self.assertEqual([(382, 137), (382, 275)],
                         lobby._dedupe_right_dots(points, 1.0))

    def test_valuable_event_has_one_standard_spec_per_child_module(self):
        expected = {
            "gift_resource_consumption_sprint",
            "gift_runestone_consumption_sprint",
            "gift_ancient_dynasty_treasury",
            "gift_general_vault",
            "gift_refining_stone_sprint", "gift_strategic_stockpile",
            "gift_limited_offer", "gift_speedup_sprint", "gift_super_blazon_sale",
            "gift_sulis_wishing", "gift_super_value_weekly_card",
            "gift_successive_purchase_benefits", "gift_optional_package",
            "gift_active_monthly_card", "gift_tomb_expedition",
            "gift_wheel_of_dragon_war",
        }
        self.assertEqual(expected, valuable_event.KEYS)
        self.assertTrue(all(spec.tab.split("/", 1)[0] for spec in valuable_event.SPECS))

    def test_valuable_flow_does_not_depend_on_notification_dots(self):
        self.assertFalse(hasattr(valuable_event, "_dots"))
        self.assertFalse(hasattr(valuable_event, "REWARD_DOT"))
        self.assertEqual((0, 7, 100, 19), valuable_named_flow.TOP_CAROUSEL)
        self.assertEqual(18, valuable_named_flow.LOWER_CONTENT[1])

    def test_carousel_edge_detection_ignores_static_animated_frame(self):
        frame = np.zeros((704, 396, 3), dtype=np.uint8)
        cv2.rectangle(frame, (40, 55), (115, 115), (255, 255, 255), 2)
        shifted = np.roll(frame, 30, axis=1)
        self.assertFalse(valuable_named_flow.carousel_moved(frame, frame.copy()))
        self.assertTrue(valuable_named_flow.carousel_moved(frame, shifted))

    def test_exact_flow_marks_absent_claim_done_only_in_lower_region(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        flow = valuable_named_flow.ExactFlow(
            claims=("ValuableEvent/LimitedOffer/button_free_current",), absence_done=True)
        with mock.patch.object(valuable_named_flow, "find", return_value=None) as find:
            self.assertTrue(valuable_named_flow.process_exact(bot, flow))
        self.assertTrue(find.call_args_list)
        self.assertTrue(all(call.kwargs["region"][1] >= 18
                            for call in find.call_args_list))

    def test_valuable_known_controls_are_checked_before_each_sparkle(self):
        bot = mock.Mock()
        order = []

        def fixed(*_args, **_kwargs):
            order.append("fixed")
            return common.ClaimReport()

        def sparkle(*_args, **_kwargs):
            order.append("sparkle")
            return common.ClaimReport()

        with (mock.patch.object(valuable_named_flow, "claim_fixed_controls",
                                side_effect=fixed) as fixed_claims,
              mock.patch.object(valuable_named_flow, "claim_sparkles",
                                side_effect=sparkle),
              mock.patch.object(valuable_named_flow, "back_if_close_x",
                                return_value=False)):
            report, navigated = valuable_named_flow.process_lower(
                bot, (), ("ValuableEvent/ResourceConsumptionSprint/button_free",))

        self.assertEqual(common.ClaimReport(), report)
        self.assertEqual(0, navigated)
        self.assertEqual(["fixed", "sparkle"] * 3, order)
        controls = fixed_claims.call_args_list[0].args[1]
        self.assertEqual("ValuableEvent/ResourceConsumptionSprint/button_free", controls[0])
        self.assertTrue(all(name in controls for name in common.TEXT_CLAIM_CONTROLS))

    def test_valuable_verified_claim_resets_three_empty_rounds(self):
        bot = mock.Mock()
        reports = [common.ClaimReport(1, 1)] + [common.ClaimReport()] * 3
        with (mock.patch.object(valuable_named_flow, "claim_fixed_controls",
                                side_effect=reports) as fixed,
              mock.patch.object(valuable_named_flow, "claim_sparkles",
                                return_value=common.ClaimReport()),
              mock.patch.object(valuable_named_flow, "back_if_close_x",
                                return_value=False)):
            report, _ = valuable_named_flow.process_lower(bot, (), ())

        self.assertEqual(common.ClaimReport(1, 1), report)
        self.assertEqual(4, fixed.call_count)

    def test_valuable_unfinished_task_stays_pending_without_blocking_scan(self):
        bot = mock.Mock()
        bot.is_daily_done.return_value = False
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.screenshot.return_value = screen
        spec = valuable_event.SPECS[0]

        def find_named(_bot, name, *_args, **_kwargs):
            if name == valuable_event.PAGE:
                return (198, 25)
            if name == spec.tab:
                return (70, 70)
            return None

        handled = set()
        with (mock.patch.object(valuable_event, "SPECS", (spec,)),
              mock.patch.object(valuable_event, "MAX_SWIPES", 0),
              mock.patch.object(valuable_event, "find", side_effect=find_named),
              mock.patch.object(valuable_event, "process_exact",
                                return_value=False) as lower):
            _, clean = valuable_event.run_opened(
                bot, {spec.task.key}, handled=handled)

        self.assertTrue(clean)
        lower.assert_called_once_with(bot, spec.flow)
        bot.mark_daily_done.assert_not_called()
        self.assertNotIn(spec.task.key, handled)

    def test_valuable_unfinished_task_does_not_block_next_visible_task(self):
        bot = mock.Mock()
        bot.is_daily_done.return_value = False
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.screenshot.return_value = screen
        first, second = valuable_event.SPECS[:2]
        events = []

        def find_named(_bot, name, *_args, **_kwargs):
            if name == valuable_event.PAGE:
                return (198, 25)
            if name == first.tab:
                return (70, 70)
            if name == second.tab:
                return (170, 70)
            return None

        def process(_bot, flow):
            events.append("first" if flow is first.flow else "second")
            return flow is second.flow

        bot.sleep.side_effect = lambda *_args, **_kwargs: events.append("settle")
        bot.swipe_percent.side_effect = (
            lambda *_args, **_kwargs: events.append("swipe"))

        with (mock.patch.object(valuable_event, "SPECS", (first, second)),
              mock.patch.object(valuable_event, "MAX_SWIPES", 2),
              mock.patch.object(valuable_event, "find", side_effect=find_named),
              mock.patch.object(valuable_event, "process_exact",
                                side_effect=process) as lower,
              mock.patch.object(valuable_event, "carousel_moved",
                                return_value=True),
              mock.patch.object(valuable_event, "mark_task_done") as mark):
            results, clean = valuable_event.run_opened(
                bot, {first.task.key, second.task.key})

        self.assertTrue(clean)
        self.assertEqual(2, lower.call_count)
        self.assertEqual("terminal_not_found", results[first.task.key])
        self.assertEqual("done", results[second.task.key])
        mark.assert_called_once_with(bot, second.task.key)
        self.assertLess(events.index("first"), events.index("settle"))
        self.assertLess(events.index("settle"), events.index("swipe"))
        self.assertLess(events.index("swipe"), events.index("second"))

    def test_valuable_full_pass_searches_name_without_red_dot(self):
        bot = mock.Mock()
        bot.is_daily_done.return_value = False
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.screenshot.return_value = screen
        spec = valuable_event.SPECS[0]

        def find_named(_bot, name, *_args, **_kwargs):
            return (198, 25) if name == valuable_event.PAGE else None

        with (mock.patch.object(valuable_event, "SPECS", (spec,)),
              mock.patch.object(valuable_event, "MAX_SWIPES", 0),
              mock.patch.object(valuable_event, "find", side_effect=find_named)):
            results, clean = valuable_event.run_opened(bot, {spec.task.key})

        self.assertTrue(clean)
        self.assertEqual("not_present", results[spec.task.key])
        bot.mark_daily_done.assert_not_called()

    def test_ancient_dynasty_treasury_requires_opened_chest_done(self):
        flow = ancient_dynasty_treasury.FLOW
        done = cv2.imread(str(
            IMAGES / "GiftClaims" / "ValuableEvent" / "AncientDynastyTreasury" /
            "status_done.png"))
        label = cv2.imread(str(
            IMAGES / "GiftClaims" / "ValuableEvent" / "AncientDynastyTreasury" /
            "label_daily_free.png"))
        self.assertEqual(
            ("ValuableEvent/AncientDynastyTreasury/label_daily_free",
             "ValuableEvent/AncientDynastyTreasury/button_daily_free"), flow.navigation)
        self.assertEqual(((0, -24), (0, 0)), flow.navigation_offsets)
        self.assertTrue(flow.navigation_first_match)
        self.assertEqual(common.TEXT_CLAIM_CONTROLS, flow.claims)
        self.assertEqual(("ValuableEvent/AncientDynastyTreasury/status_done",), flow.done)
        self.assertFalse(flow.absence_done)
        self.assertEqual((34, 43), done.shape[:2])
        self.assertEqual((13, 57), label.shape[:2])

    def test_navigation_text_anchor_taps_configured_offset(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        flow = valuable_named_flow.ExactFlow(
            navigation=("Task/label", "Task/full_button"),
            navigation_offsets=((0, -24), (0, 0)),
            navigation_first_match=True)
        with mock.patch.object(
                valuable_named_flow, "_wait_any",
                return_value=("Task/label", (200, 300))) as wait:
            self.assertTrue(valuable_named_flow._tap_navigation(bot, flow))

        bot.tap.assert_called_once_with(200, 276, delay=1.0)
        wait.assert_called_once()

    def test_named_task_tabs_require_high_confidence(self):
        self.assertEqual(0.82, valuable_named_flow.TASK_TAB_THRESHOLD)
        self.assertEqual(1.0, valuable_named_flow.SLOW_SWIPE_DURATION)

    def test_requested_free_tasks_have_explicit_absence_done_rules(self):
        by_key = {spec.task.key: spec.flow for spec in valuable_event.SPECS}
        self.assertTrue(by_key[limited_offer.KEY].absence_done)
        self.assertTrue(by_key[super_blazon_sale.KEY].absence_done)
        self.assertIn("ValuableEvent/ResourceConsumptionSprint/sold_out",
                      by_key[resource_consumption_sprint.KEY].done)

    def test_strict_terminal_tasks_never_finish_from_missing_claim_button(self):
        valuable = {spec.task.key: spec.flow for spec in valuable_event.SPECS}
        super_value = {spec.task.key: spec.flow
                       for spec in super_value_return.SPECS}
        strict = {
            "gift_resource_consumption_sprint": valuable,
            "gift_optional_package": valuable,
            "gift_successive_purchase_benefits": valuable,
            "gift_tomb_expedition": valuable,
            "gift_general_vault": valuable,
            "gift_empire_depot": super_value,
            "gift_lucky_raffle": super_value,
        }
        for key, flows in strict.items():
            self.assertFalse(flows[key].absence_done, key)

        self.assertTrue(valuable["gift_resource_consumption_sprint"].congratulations_done)
        self.assertEqual(("ValuableEvent/OptionalPackage/chest_open",),
                         valuable["gift_optional_package"].done)
        self.assertEqual(("ValuableEvent/SuccessivePurchaseBenefits/chest_open",),
                         valuable["gift_successive_purchase_benefits"].done)
        self.assertEqual(("ValuableEvent/TombExpedition/quests_done",),
                         valuable["gift_tomb_expedition"].done)
        self.assertTrue(valuable["gift_general_vault"].congratulations_done)
        self.assertEqual(("SuperValueReturn/EmpireDepot/chest_open",),
                         super_value["gift_empire_depot"].done)
        self.assertTrue(super_value["gift_lucky_raffle"].congratulations_done)
        self.assertEqual(("SuperValueReturn/LuckyRaffle/chest_open",),
                         super_value["gift_lucky_raffle"].done)

    def test_horizontal_carousels_have_twelve_swipe_safety_ceiling(self):
        self.assertEqual(12, valuable_event.MAX_SWIPES)
        self.assertEqual(12, super_value_return.MAX_SWIPES)

    def test_gift_zone_priorities_put_event_center_before_outside_zones(self):
        from bot.worker.priority import DATA

        priorities = {
            item["key"]: item["priority"]
            for item in DATA["Gift Claims"]
        }
        self.assertGreater(priorities["gift_event_center"],
                           priorities["gift_valuable_event"])
        self.assertGreater(priorities["gift_valuable_event"],
                           priorities["gift_super_value_return"])
        self.assertLess(priorities["gift_event_center"], 10)

    def test_gift_zones_are_tail_tasks_after_all_daily_work(self):
        from bot.worker.priority import DATA

        for row in DATA["Gift Claims"]:
            with self.subTest(key=row["key"]):
                self.assertEqual("Daily Activities", row["group"])
                self.assertTrue(row.get("tail"))

    def test_strategic_stockpile_uses_free_offset_and_claimed_chest(self):
        flow = strategic_stockpile.FLOW
        self.assertEqual(("ValuableEvent/StrategicStockpile/title",), flow.opened)
        self.assertEqual(("ValuableEvent/StrategicStockpile/button_free_text",), flow.claims)
        self.assertEqual(("ValuableEvent/StrategicStockpile/chest_claimed",), flow.done)
        self.assertEqual((10, -10), flow.claim_offset)

    def test_runestone_consumption_sprint_has_explicit_done_rules(self):
        flow = runestone_consumption_sprint.FLOW
        self.assertEqual(("ValuableEvent/RunestoneConsumptionSprint/subtab_sprint_package",),
                         flow.navigation)
        self.assertEqual(("ValuableEvent/RunestoneConsumptionSprint/button_free",), flow.claims)
        self.assertEqual(("ValuableEvent/RunestoneConsumptionSprint/sold_out",), flow.done)
        self.assertTrue(flow.congratulations_done)

    def test_speedup_sprint_only_taps_free_and_requires_sold_out(self):
        flow = speedup_sprint.FLOW
        self.assertEqual(("ValuableEvent/SpeedupSprint/subtab_package",), flow.navigation)
        self.assertEqual(("ValuableEvent/SpeedupSprint/button_free",), flow.claims)
        self.assertEqual(0.95, flow.claim_threshold)
        self.assertEqual(("ValuableEvent/SpeedupSprint/status_sold_out",), flow.done)
        self.assertFalse(flow.absence_done)
        self.assertFalse(flow.congratulations_done)

    def test_wheel_of_dragon_war_flow_uses_skip_then_free_disappearance(self):
        flow = wheel_of_dragon_war.FLOW
        self.assertIs(flow.prepare, wheel_of_dragon_war.ensure_skip_animation)
        self.assertEqual(("ValuableEvent/WheelOfDragonWar/button_spin_once_free",),
                         flow.claims)
        self.assertTrue(flow.absence_done)
        self.assertEqual(0.86, flow.claim_threshold)

    def test_wheel_skip_animation_taps_and_verifies_green_check(self):
        blank = np.zeros((704, 396, 3), dtype=np.uint8)
        checked = blank.copy()
        checked[578:590, 259:271] = (0, 255, 0)
        bot = mock.Mock()
        bot.screenshot.side_effect = (blank, blank, blank, checked)

        self.assertTrue(wheel_of_dragon_war.ensure_skip_animation(bot))

        bot.tap.assert_called_once_with(267, 584, delay=1.0)

    def test_wheel_skip_animation_does_not_toggle_existing_green_check(self):
        checked = np.zeros((704, 396, 3), dtype=np.uint8)
        checked[578:590, 259:271] = (0, 255, 0)
        bot = mock.Mock()
        bot.screenshot.return_value = checked

        self.assertTrue(wheel_of_dragon_war.ensure_skip_animation(bot))

        bot.tap.assert_not_called()

    def test_exact_flow_uses_configured_claim_threshold(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        thresholds = []

        def find_named(_bot, name, *_args, **kwargs):
            if name == "claim":
                thresholds.append(kwargs.get("threshold"))
            return None

        flow = valuable_named_flow.ExactFlow(
            claims=("claim",), claim_threshold=0.95, absence_done=True)
        with mock.patch.object(valuable_named_flow, "find",
                               side_effect=find_named):
            self.assertTrue(valuable_named_flow.process_exact(bot, flow))

        self.assertTrue(thresholds)
        self.assertTrue(all(value == 0.95 for value in thresholds))
        bot.tap.assert_not_called()

    def test_unrecognized_nested_task_backs_once_without_return_home(self):
        bot = mock.Mock()
        flow = valuable_named_flow.ExactFlow(
            navigation=("SomeTask/subpage",),
            claims=("SomeTask/button_free",),
            done=("SomeTask/status_done",),
        )
        with (mock.patch.object(valuable_named_flow, "_done", return_value=False),
              mock.patch.object(valuable_named_flow, "_tap_navigation", return_value=True),
              mock.patch.object(valuable_named_flow, "find_any", return_value=None),
              mock.patch.object(valuable_named_flow, "return_home") as home):
            self.assertFalse(valuable_named_flow.process_exact(bot, flow))
        bot.back.assert_called_once_with(delay=valuable_named_flow.STEP_DELAY)
        home.assert_not_called()

    def test_unrecognized_carousel_task_backs_once_without_return_home(self):
        bot = mock.Mock()
        flow = valuable_named_flow.ExactFlow()
        with (mock.patch.object(valuable_named_flow, "open_named", return_value=True),
              mock.patch.object(valuable_named_flow, "select_carousel_tab", return_value=False),
              mock.patch.object(valuable_named_flow, "return_home") as home):
            self.assertFalse(valuable_named_flow.run_carousel_exact(
                bot, GiftScreen.VALUABLE_EVENT, "ValuableEvent/title",
                "MissingTask/tab", flow))
        bot.back.assert_called_once_with(delay=valuable_named_flow.STEP_DELAY)
        home.assert_not_called()

    def test_valuable_rewind_does_not_reverse_at_false_halfway_boundary(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.screenshot.return_value = screen
        spec = valuable_event.SPECS[0]

        def find_named(_bot, name, *_args, **_kwargs):
            return (198, 25) if name == valuable_event.PAGE else None

        with (mock.patch.object(valuable_event, "SPECS", (spec,)),
              mock.patch.object(valuable_event, "MAX_SWIPES", 4),
              mock.patch.object(valuable_event, "find", side_effect=find_named),
              mock.patch.object(valuable_event, "carousel_moved",
                                return_value=False)):
            results, clean = valuable_event.run_opened(bot, {spec.task.key})

        self.assertTrue(clean)
        self.assertEqual("not_present", results[spec.task.key])
        swipes = bot.swipe_percent.call_args_list
        self.assertEqual(6, len(swipes))
        self.assertTrue(all(call.args[:4] == (20, 14, 85, 14)
                            for call in swipes[:4]))
        self.assertTrue(all(call.args[:4] == (85, 14, 55, 14)
                            for call in swipes[4:]))

    def test_super_value_return_has_one_standard_spec_per_child_module(self):
        expected = {
            "gift_empire_depot", "gift_lucky_raffle", "gift_city_growth_plan",
            "gift_login_gifts", "gift_refining_weekly_card",
        }
        self.assertEqual(expected, super_value_return.KEYS)
        self.assertTrue(all(spec.tab.split("/", 1)[0] for spec in super_value_return.SPECS))
        self.assertTrue(all(hasattr(spec, "flow") for spec in super_value_return.SPECS))

    def test_super_value_return_is_an_independent_five_task_zone(self):
        self.assertEqual("gift_super_value_return", super_value_zone.KEY)
        self.assertEqual(
            ["gift_login_gifts", "gift_empire_depot", "gift_lucky_raffle",
             "gift_city_growth_plan", "gift_refining_weekly_card"],
            [task.key for task in super_value_zone.TASKS])
        self.assertTrue(all(task.key not in {
            item.key for item in valuable_event_zone.TASKS
        } for task in super_value_zone.TASKS))

    def test_super_value_settles_lower_task_before_scrolling_to_next_tab(self):
        bot = mock.Mock()
        bot.is_daily_done.return_value = False
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.screenshot.return_value = screen
        first, second = (super_value_return.SPECS[0],
                         super_value_return.SPECS[2])
        events = []

        def find_named(_bot, name, *_args, **_kwargs):
            if name == super_value_return.PAGE:
                return (198, 25)
            if name == first.tab:
                return (70, 70)
            if name == second.tab:
                return (170, 70)
            return None

        def process(_bot, flow):
            events.append("first" if flow is first.flow else "second")
            return flow is second.flow

        bot.sleep.side_effect = lambda *_args, **_kwargs: events.append("settle")
        bot.swipe_percent.side_effect = (
            lambda *_args, **_kwargs: events.append("swipe"))
        with (mock.patch.object(super_value_return, "SPECS", (first, second)),
              mock.patch.object(super_value_return, "MAX_SWIPES", 2),
              mock.patch.object(super_value_return, "find",
                                side_effect=find_named),
              mock.patch.object(super_value_return, "process_exact",
                                side_effect=process),
              mock.patch.object(super_value_return, "carousel_moved",
                                return_value=True),
              mock.patch.object(super_value_return, "mark_task_done")):
            results, clean = super_value_return.run_opened(
                bot, {first.task.key, second.task.key})

        self.assertTrue(clean)
        self.assertEqual("terminal_not_found", results[first.task.key])
        self.assertEqual("done", results[second.task.key])
        self.assertLess(events.index("first"), events.index("settle"))
        self.assertLess(events.index("settle"), events.index("swipe"))
        self.assertLess(events.index("swipe"), events.index("second"))

    def test_city_growth_done_requires_level_15_and_claimed_tick_crop(self):
        marker = cv2.imread(str(IMAGES / "GiftClaims" /
                                "SuperValueReturn" / "CityGrowthPlan" /
                                "level_15_claimed.png"))
        self.assertIsNotNone(marker)
        self.assertGreater(marker.shape[1], 100)
        city = next(spec for spec in super_value_return.SPECS
                    if spec.task.key == "gift_city_growth_plan")
        self.assertEqual(("SuperValueReturn/CityGrowthPlan/level_15_claimed",), city.flow.done)

    def test_refining_weekly_card_does_not_treat_go_as_done(self):
        self.assertEqual((), refining_weekly_card.FLOW.done)
        self.assertEqual((refining_weekly_card.CLAIM,),
                         refining_weekly_card.FLOW.claims)

    def test_refining_weekly_card_swipes_only_inside_green_reward_frame(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.screenshot.return_value = screen

        with (mock.patch.object(refining_weekly_card, "find",
                                return_value=None),
              mock.patch.object(refining_weekly_card,
                                "EDGE_CONFIRMATIONS", 1)):
            self.assertTrue(refining_weekly_card.claim_opened(bot))

        self.assertGreater(bot.swipe_percent.call_count, 0)
        allowed = {refining_weekly_card.SCAN_SWIPE,
                   refining_weekly_card.RETURN_TOP_SWIPE}
        for call in bot.swipe_percent.call_args_list:
            self.assertIn(call.args[:4], allowed)
            self.assertTrue(67 <= call.args[1] <= 98)
            self.assertTrue(67 <= call.args[3] <= 98)

    def test_refining_weekly_card_requires_clean_followup_pass(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.screenshot.return_value = screen

        with (mock.patch.object(refining_weekly_card, "_swipe_to_top"),
              mock.patch.object(refining_weekly_card, "_scan_full_list",
                                side_effect=[(True, False), (False, False)]) as scan):
            self.assertTrue(refining_weekly_card.claim_opened(bot))

        self.assertEqual(2, scan.call_count)
        bot.sleep.assert_called_once_with(refining_weekly_card.STEP_DELAY)

    def test_login_gifts_uses_fixed_fallback_when_reward_image_is_missing(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)

        def find_page(_bot, name, *_args, **_kwargs):
            return (40, 140) if name == login_gifts.PAGE else None

        with (mock.patch.object(login_gifts, "find", side_effect=find_page),
              mock.patch.object(login_gifts, "_tap_reward",
                                return_value=False) as tap):
            self.assertFalse(login_gifts.claim_opened(bot))

        tap.assert_called_once_with(bot, (45, 190))

    def test_login_gifts_uses_captured_reward_button_before_fallback(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)

        def find_page(_bot, name, *_args, **_kwargs):
            if name == login_gifts.PAGE:
                return (40, 140)
            if name == login_gifts.REWARD_BUTTON:
                return (51, 192)
            return None

        with (mock.patch.object(login_gifts, "find", side_effect=find_page),
              mock.patch.object(login_gifts, "_tap_reward",
                                return_value=True) as tap):
            self.assertTrue(login_gifts.claim_opened(bot))

        tap.assert_called_once_with(bot, (51, 192))

    def test_shared_reward_chest_uses_measured_full_crop_and_threshold(self):
        chest = cv2.imread(str(IMAGES / "GiftClaims" / "Common" /
                              "button_reward_chest.png"))
        self.assertEqual((47, 47), chest.shape[:2])
        self.assertEqual("Common/button_reward_chest",
                         login_gifts.REWARD_BUTTON)
        self.assertEqual(0.80, login_gifts.REWARD_THRESHOLD)

        flows = {spec.task.key: spec.flow for spec in valuable_event.SPECS}
        for key in ("gift_super_value_weekly_card",
                    "gift_active_monthly_card"):
            self.assertEqual(("Common/button_reward_chest",),
                             flows[key].navigation)
            self.assertEqual(0.80, flows[key].navigation_threshold)

    def test_login_gift_confirms_and_closes_congratulations(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)

        def find_popup(_bot, name, *_args, **_kwargs):
            return (198, 319) if name == login_gifts.CONGRATULATIONS else None

        with mock.patch.object(login_gifts, "find", side_effect=find_popup):
            self.assertTrue(login_gifts._tap_reward(bot, (123, 470)))

        bot.tap.assert_called_once_with(123, 470, delay=1)
        bot.back.assert_called_once_with(delay=1)

    def test_login_gift_is_done_when_fresh_screenshot_has_no_chest(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)

        def find_state(_bot, name, *_args, **_kwargs):
            if name == login_gifts.PAGE:
                return (40, 140)
            return None

        with mock.patch.object(login_gifts, "find", side_effect=find_state):
            self.assertTrue(login_gifts._tap_reward(bot, (45, 190)))

        bot.tap.assert_called_once_with(45, 190, delay=1)
        bot.back.assert_not_called()

    def test_back_to_territory_claims_congratulations_day(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(back_to_territory, "claim_fixed_controls",
                                return_value=common.ClaimReport()),
              mock.patch.object(back_to_territory, "_claim_visible_login_rewards",
                                return_value=common.ClaimReport()),
              mock.patch.object(back_to_territory, "_inner_dots", return_value=[]),
              mock.patch.object(back_to_territory, "back_if_close_x",
                                return_value=False),
              mock.patch.object(back_to_territory, "claim_sparkles",
                                return_value=common.ClaimReport(2, 2)) as sparkle):
            self.assertEqual(2, back_to_territory.claim_opened(bot))

        sparkle.assert_called_once_with(bot, region=back_to_territory.SPARKLE_REWARDS,
                                        attempts=4)

    def test_back_to_territory_detects_red_tabs_below_carousel(self):
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        cv2.circle(screen, (78, 333), 5, (0, 40, 190), thickness=-1)
        cv2.circle(screen, (254, 380), 5, (0, 40, 190), thickness=-1)
        self.assertEqual([(78, 333), (254, 380)],
                         back_to_territory._inner_dots(screen))

    def test_back_to_territory_claims_multiple_identical_buttons(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(back_to_territory, "find_all",
                                side_effect=([(333, 477), (333, 584)],
                                             [(333, 584)], [])),
              mock.patch.object(back_to_territory, "close_congratulations",
                                side_effect=(True, True))):
            report = back_to_territory._claim_visible_login_rewards(bot)

        self.assertEqual(common.ClaimReport(2, 2), report)
        self.assertEqual(2, bot.tap.call_count)


    def test_event_center_finds_inner_red_tab_and_excludes_purchase_edge(self):
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        cv2.circle(screen, (313, 68), 8, (0, 40, 190), thickness=-1)
        cv2.circle(screen, (365, 110), 8, (0, 40, 190), thickness=-1)
        self.assertEqual([(313, 68)], event_center._inner_red_dots(screen))

        after = screen.copy()
        after[575:583, 364:372] = 255
        self.assertIsNone(common.sparkle_point(
            screen, after, region=event_center.SPARKLE_SAFE))

    def test_legion_hunting_assets_and_limited_registration(self):
        for name in ("list_row.png", "title.png", "button_claim.png"):
            self.assertTrue((IMAGES / "GiftClaims" / "EventCenter" / "LegionHunting" /
                             name).is_file())
        legion = next(policy for policy in event_center.EVENT_POLICIES
                      if policy.key == "gift_legion_hunting")
        self.assertEqual(GiftScreen.LEGION_HUNTING, legion.screen)
        self.assertNotIn(legion.key, event_center.POLICY_CATEGORIES)
        self.assertTrue(any(row[0] == "EventCenter/LegionHunting/list_row"
                            and row[2] == GiftScreen.LEGION_HUNTING
                            for row in event_center.FORCED_LIMITED_ROWS))

    def test_legion_hunting_title_identifies_opened_page(self):
        title = cv2.imread(str(IMAGES / "GiftClaims" / "EventCenter" / "LegionHunting" /
                               "title.png"))
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        height, width = title.shape[:2]
        screen[5:5 + height, 100:100 + width] = title
        self.assertEqual(GiftScreen.LEGION_HUNTING,
                         identify(CvBot(), screen))

    def test_legion_hunting_done_only_after_full_claim_free_pass(self):
        bot = mock.Mock()
        with (mock.patch.object(event_center, "_legion_swipe_to_top",
                                return_value=True),
              mock.patch.object(event_center, "_scan_legion_once",
                                side_effect=[
                                    (common.ClaimReport(1, 1), True, False),
                                    (common.ClaimReport(), True, False),
                                ]) as scan):
            report, done = event_center._handle_legion_hunting(bot)

        self.assertTrue(done)
        self.assertEqual(common.ClaimReport(1, 1), report)
        self.assertEqual(2, scan.call_count)
        bot.sleep.assert_called_once_with(event_center.UI_SETTLE_SECONDS)

    def test_legion_hunting_keeps_pending_when_claim_does_not_disappear(self):
        bot = mock.Mock()
        with (mock.patch.object(event_center, "_legion_swipe_to_top",
                                return_value=True),
              mock.patch.object(event_center, "_scan_legion_once",
                                return_value=(common.ClaimReport(1, 0),
                                              False, True))):
            _, done = event_center._handle_legion_hunting(bot)

        self.assertFalse(done)

    def test_event_center_persistent_inner_badge_is_processed_once(self):
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot = mock.Mock()
        bot.screenshot.return_value = screen
        with (mock.patch.object(event_center, "identify",
                                return_value=GiftScreen.UNKNOWN),
              mock.patch.object(event_center, "_inner_red_dots",
                                return_value=[(313, 68)]),
              mock.patch.object(event_center, "_inner_tab_signature",
                                side_effect=(f"animated-{i}".encode()
                                             for i in range(100))),
              mock.patch.object(event_center, "_process_current_event_content",
                                return_value=(common.ClaimReport(), False)) as process):
            event_center._process_opened_event(bot)

        process.assert_called_once_with(bot)
        self.assertEqual(2, bot.swipe_percent.call_count)

    def test_event_center_tab_signature_tolerates_small_animation_changes(self):
        original = bytes([0b10101010] * 16)
        animated = bytearray(original)
        animated[0] ^= 0b00000111
        animated[5] ^= 0b00000001
        self.assertTrue(event_center._signature_seen(bytes(animated), {original}))

        different = bytes([0b01010101] * 16)
        self.assertFalse(event_center._signature_seen(different, {original}))

    def test_event_center_row_signature_ignores_animated_right_artwork(self):
        first = np.zeros((704, 396, 3), dtype=np.uint8)
        second = first.copy()
        first[200:264, 280:396] = 255
        second[200:264, 280:396] = (0, 0, 180)
        self.assertEqual(event_center._row_signature(first, 232),
                         event_center._row_signature(second, 232))

    def test_event_center_category_row_tolerates_small_animation_changes(self):
        original = bytes([0b11001100] * 24)
        animated = bytearray(original)
        animated[2] ^= 0b00000111
        animated[11] ^= 0b00000001
        visited = {event_center._category_signature("competition", original)}
        self.assertTrue(event_center._category_seen(
            "competition", bytes(animated), visited))
        self.assertFalse(event_center._category_seen(
            "limited", bytes(animated), visited))

    def test_event_center_special_rewards_is_tapped_and_verified(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)

        def find_named(_bot, name, *_args, **_kwargs):
            if name == "EventCenter/PreciousBlazonExchange/button_rewards_text":
                return (49, 235)
            return None

        with (mock.patch.object(event_center, "identify",
                                return_value=GiftScreen.PRECIOUS_BLAZON_EXCHANGE),
              mock.patch.object(event_center, "find", side_effect=find_named),
              mock.patch.object(event_center, "close_congratulations",
                                return_value=True)):
            report = event_center._tap_special_navigation(bot)

        self.assertEqual(common.ClaimReport(1, 1), report)
        bot.tap.assert_called_once_with(
            49, 235, delay=event_center.UI_SETTLE_SECONDS)

    def test_named_event_without_special_control_stops_immediately(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(event_center, "identify",
                                return_value=GiftScreen.GRACE_OF_STAR_TRAIL),
              mock.patch.object(event_center, "find", return_value=None)):
            report = event_center._tap_special_navigation(bot, attempts=4)

        self.assertEqual(common.ClaimReport(), report)
        self.assertEqual(1, bot.screenshot.call_count)
        bot.sleep.assert_not_called()
        bot.tap.assert_not_called()

    def test_unknown_event_checks_special_control_four_times(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(event_center, "identify", return_value=None),
              mock.patch.object(event_center, "find", return_value=None)):
            report = event_center._tap_special_navigation(bot, attempts=4)

        self.assertEqual(common.ClaimReport(), report)
        self.assertEqual(4, bot.screenshot.call_count)
        self.assertEqual(3, bot.sleep.call_count)
        bot.tap.assert_not_called()

    def test_event_center_unresponsive_rewards_is_tapped_only_four_times(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(event_center, "identify",
                                return_value=GiftScreen.HYPNOS_DREAM),
              mock.patch.object(event_center, "find", return_value=(357, 164)),
              mock.patch.object(event_center, "close_congratulations",
                                return_value=False)):
            report = event_center._tap_special_navigation(bot, attempts=4)

        self.assertEqual(common.ClaimReport(4, 0), report)
        self.assertEqual(4, bot.tap.call_count)

    def test_event_center_disappearing_rewards_is_verified(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(event_center, "identify",
                                return_value=GiftScreen.HYPNOS_DREAM),
              mock.patch.object(event_center, "find",
                                side_effect=((357, 164), None)),
              mock.patch.object(event_center, "close_congratulations",
                                return_value=False)):
            report = event_center._tap_special_navigation(bot, attempts=4)

        self.assertEqual(common.ClaimReport(1, 1), report)
        bot.tap.assert_called_once_with(
            357, 164, delay=event_center.UI_SETTLE_SECONDS)

    def test_named_navigation_event_never_falls_through_to_sparkles(self):
        bot = mock.Mock()
        expected = common.ClaimReport(1, 1)
        with (mock.patch.object(event_center, "identify",
                                return_value=GiftScreen.DWARFS_TREASURE),
              mock.patch.object(event_center, "_tap_special_navigation",
                                return_value=expected),
              mock.patch.object(event_center, "_tap_reward_navigation") as reward,
              mock.patch.object(event_center, "claim_fixed_controls") as fixed,
              mock.patch.object(event_center, "claim_sparkles") as sparkle):
            report, closed = event_center._process_current_event_content(bot)

        self.assertEqual(expected, report)
        self.assertFalse(closed)
        reward.assert_not_called()
        fixed.assert_not_called()
        sparkle.assert_not_called()

    def test_unverified_exact_event_stays_pending(self):
        bot = mock.Mock()
        bot.is_daily_done.return_value = False
        unresolved = common.ClaimReport(4, 0)
        with (mock.patch.object(event_center, "identify",
                                return_value=GiftScreen.PRECIOUS_BLAZON_EXCHANGE),
              mock.patch.object(event_center, "_handle_precious",
                                return_value=(unresolved, False)),
              mock.patch.dict(event_center.EXACT_HANDLERS,
                              {GiftScreen.PRECIOUS_BLAZON_EXCHANGE:
                               event_center._handle_precious})):
            self.assertEqual(unresolved,
                             event_center._process_opened_event(bot))

        bot.mark_daily_done.assert_not_called()

    def test_dwarf_daily_free_disappearance_is_verified_during_transition(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(event_center, "identify",
                               side_effect=(GiftScreen.DWARFS_TREASURE, None)),
              mock.patch.object(event_center, "find",
                                side_effect=((356, 180), None)),
              mock.patch.object(event_center, "close_congratulations",
                                return_value=False)):
            report = event_center._tap_special_navigation(bot, attempts=4)

        self.assertEqual(common.ClaimReport(1, 1), report)
        bot.tap.assert_called_once_with(
            356, 180, delay=event_center.UI_SETTLE_SECONDS)

    def test_poseidon_opens_captured_tab_then_claims_daily_free(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)

        def find_named(_bot, name, *_args, **_kwargs):
            calls[name] = calls.get(name, 0) + 1
            if name == "EventCenter/PoseidonsDay/tab_packages_red_dot":
                return (34, 78)
            if (name == "EventCenter/PoseidonsDay/button_daily_free_text" and
                    calls[name] >= 2):
                return (355, 155)
            return None

        calls = {}
        with (mock.patch.object(event_center, "identify",
                                return_value=GiftScreen.POSEIDONS_DAY),
              mock.patch.object(event_center, "find", side_effect=find_named),
              mock.patch.object(event_center, "close_congratulations",
                                return_value=True)):
            report = event_center._tap_special_navigation(bot)

        self.assertEqual(common.ClaimReport(2, 1), report)
        self.assertEqual([mock.call(34, 78,
                                    delay=event_center.UI_SETTLE_SECONDS),
                          mock.call(355, 155,
                                    delay=event_center.UI_SETTLE_SECONDS)],
                         bot.tap.call_args_list)

    def test_star_trail_gift_is_tapped_and_verified(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(event_center, "find",
                                side_effect=((360, 90), (40, 240), None)),
              mock.patch.object(event_center, "close_congratulations",
                                return_value=False)):
            report = event_center._tap_reward_navigation(bot)

        self.assertEqual(common.ClaimReport(2, 1), report)
        self.assertEqual([mock.call(360, 90,
                                    delay=event_center.UI_SETTLE_SECONDS),
                          mock.call(40, 240,
                                    delay=event_center.UI_SETTLE_SECONDS)],
                         bot.tap.call_args_list)

    def test_wishful_uses_one_second_settle_time(self):
        self.assertEqual(1.5, event_center.UI_SETTLE_SECONDS)
        self.assertEqual(1.0, event_center.WISHFUL_SETTLE_SECONDS)
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with mock.patch.object(event_center, "find", return_value=None):
            self.assertIsNone(event_center._wait_for(
                bot, "EventCenter/WishfulWindmillFestival/button_claim", attempts=3,
                delay=event_center.WISHFUL_SETTLE_SECONDS))
        self.assertEqual(
            [mock.call(event_center.WISHFUL_SETTLE_SECONDS)] * 2,
            bot.sleep.call_args_list)

    def test_wishful_searches_wind_blessings_across_content_not_right_only(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(event_center, "_wishful_panel_open",
                                side_effect=(False, True)),
              mock.patch.object(event_center, "find",
                                return_value=(35, 260)) as find_entry):
            self.assertTrue(event_center._wishful_open_blessings(bot))

        entry_call = find_entry.call_args_list[0]
        self.assertEqual("EventCenter/WishfulWindmillFestival/button_wind_blessings",
                         entry_call.args[1])
        self.assertEqual((0, 12, 100, 85), entry_call.kwargs["region"])
        bot.tap.assert_called_once_with(
            35, 260, delay=event_center.WISHFUL_SETTLE_SECONDS)

    def test_wishful_reward_chest_opens_done_one_panel(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(event_center, "_wishful_panel_open",
                                side_effect=(False, True)),
              mock.patch.object(event_center, "find",
                                side_effect=(None, (62, 248))) as find_entry):
            self.assertTrue(event_center._wishful_open_blessings(bot))

        chest_call = find_entry.call_args_list[1]
        self.assertEqual("EventCenter/WishfulWindmillFestival/button_reward_chest_wind",
                         chest_call.args[1])
        self.assertEqual(0.86, chest_call.kwargs["threshold"])
        self.assertEqual((0, 12, 100, 85), chest_call.kwargs["region"])
        bot.tap.assert_called_once_with(
            62, 248, delay=event_center.WISHFUL_SETTLE_SECONDS)

    def test_wishful_retries_only_after_refinding_same_launcher(self):
        bot = mock.Mock()
        with (mock.patch.object(event_center, "_wishful_panel_open",
                                side_effect=(False, False, True)),
              mock.patch.object(
                  event_center, "_wishful_find_entry",
                  return_value=((35, 260),
                                "EventCenter/WishfulWindmillFestival/button_wind_blessings",
                                0.68, "Wind Blessings")),
              mock.patch.object(event_center, "_wait_for",
                                return_value=(36, 261))):
            self.assertTrue(event_center._wishful_open_blessings(bot))

        self.assertEqual(
            [mock.call(35, 260, delay=event_center.WISHFUL_SETTLE_SECONDS),
             mock.call(36, 261, delay=event_center.WISHFUL_SETTLE_SECONDS)],
            bot.tap.call_args_list)

    def test_wishful_new_crops_have_the_exact_supplied_dimensions(self):
        chest = cv2.imread(str(
            IMAGES / "GiftClaims" / "EventCenter" / "WishfulWindmillFestival" /
            "button_reward_chest_wind.png"))
        title = cv2.imread(str(
            IMAGES / "GiftClaims" / "EventCenter" / "WishfulWindmillFestival" /
            "title_wind_blessings_text.png"))
        limit = cv2.imread(str(
            IMAGES / "GiftClaims" / "EventCenter" / "WishfulWindmillFestival" /
            "status_done_one_claim_limit.png"))
        claimed = cv2.imread(str(
            IMAGES / "GiftClaims" / "EventCenter" / "WishfulWindmillFestival" /
            "status_claimed.png"))
        self.assertEqual((32, 39), chest.shape[:2])
        self.assertEqual((18, 131), title.shape[:2])
        self.assertEqual((20, 233), limit.shape[:2])
        self.assertEqual((28, 77), claimed.shape[:2])

    def test_wishful_claim_limit_toast_finishes_done_one_immediately(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(event_center, "_wishful_done_one_limit",
                                return_value=True),
              mock.patch.object(event_center,
                                "_close_wishful_congratulations") as close):
            result = event_center._tap_wishful_claim(
                bot, (330, 245), "DONE 1")

        self.assertEqual((1, True, True), result)
        close.assert_not_called()
        bot.tap.assert_called_once_with(
            330, 245, delay=event_center.WISHFUL_SETTLE_SECONDS)

    def test_wishful_claim_limit_is_not_done_for_challenge_quest(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(event_center, "_wishful_done_one_limit",
                                return_value=True) as limit,
              mock.patch.object(event_center, "_wishful_claims",
                                return_value=[]),
              mock.patch.object(event_center, "_wishful_claimed_near",
                                return_value=False),
              mock.patch.object(event_center,
                                "_close_wishful_congratulations",
                                return_value=True)):
            result = event_center._tap_wishful_claim(
                bot, (330, 245), "Challenge Quest")

        self.assertEqual((1, True, False), result)
        limit.assert_not_called()

    def test_wishful_claim_changing_to_claimed_finishes_phase(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(event_center, "_wishful_done_one_limit",
                                return_value=False),
              mock.patch.object(event_center, "_wishful_claimed_near",
                                return_value=True),
              mock.patch.object(event_center,
                                "_close_wishful_congratulations") as close):
            result = event_center._tap_wishful_claim(
                bot, (330, 245), "Challenge Quest")

        self.assertEqual((1, True, True), result)
        close.assert_not_called()

    def test_wishful_panel_with_only_claimed_is_done(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(event_center, "_wishful_panel_open",
                                return_value=True),
              mock.patch.object(event_center, "_wishful_claims",
                                return_value=[]),
              mock.patch.object(event_center, "_wishful_claimed",
                                return_value=[(330, 245)])):
            report, done = event_center._claim_wishful_panel(bot, "DONE 1")

        self.assertTrue(done)
        self.assertEqual(common.ClaimReport(0, 1), report)
        bot.swipe_percent.assert_not_called()

    def test_wishful_panel_stops_scrolling_on_done_one_limit(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(event_center, "_wishful_panel_open",
                                return_value=True),
              mock.patch.object(event_center, "_wishful_claims",
                                return_value=[(330, 245)]),
              mock.patch.object(event_center, "_tap_wishful_claim",
                                return_value=(1, True, True))):
            report, done = event_center._claim_wishful_panel(bot, "DONE 1")

        self.assertTrue(done)
        self.assertEqual(common.ClaimReport(1, 1), report)
        bot.swipe_percent.assert_not_called()

    def test_wishful_panel_claims_without_back_or_reopening(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        calls = {"count": 0}

        def claims(_bot, _screen):
            calls["count"] += 1
            return [(330, 245)] if calls["count"] == 1 else []

        with (mock.patch.object(event_center, "_wishful_panel_open",
                                return_value=True),
              mock.patch.object(event_center, "_wishful_claims",
                                side_effect=claims),
              mock.patch.object(event_center, "_wishful_done_one_limit",
                                return_value=False),
              mock.patch.object(event_center, "_wishful_claimed_near",
                                return_value=False),
              mock.patch.object(event_center, "_wishful_claimed",
                                return_value=[]),
              mock.patch.object(event_center,
                                "_close_wishful_congratulations",
                                return_value=True)):
            report, done = event_center._claim_wishful_panel(bot, "DONE 1")

        self.assertTrue(done)
        self.assertEqual(common.ClaimReport(1, 1), report)
        bot.tap.assert_called_once_with(
            330, 245, delay=event_center.WISHFUL_SETTLE_SECONDS)
        self.assertEqual(2, bot.swipe_percent.call_count)
        bot.back.assert_not_called()

    def test_wishful_handle_finishes_each_panel_before_next_phase(self):
        bot = mock.Mock()
        first = common.ClaimReport(2, 2)
        second = common.ClaimReport(3, 3)
        with (mock.patch.object(event_center, "_wishful_open_blessings",
                                return_value=True) as open_first,
              mock.patch.object(event_center, "_claim_wishful_panel",
                                side_effect=((first, True), (second, True))) as claim,
              mock.patch.object(event_center, "_wait_for",
                                side_effect=((190, 80), (198, 620)))):
            report, done = event_center._handle_wishful(bot)

        self.assertTrue(done)
        self.assertEqual(common.ClaimReport(5, 5), report)
        open_first.assert_called_once_with(bot)
        self.assertEqual([mock.call(bot, "DONE 1"),
                          mock.call(bot, "Challenge Quest")],
                         claim.call_args_list)
        bot.back.assert_called_once_with(
            delay=event_center.WISHFUL_SETTLE_SECONDS)

    def test_event_row_wait_does_not_treat_loading_frame_as_opened(self):
        bot = mock.Mock()
        with mock.patch.object(
                event_center, "identify",
                side_effect=(None, None,
                             GiftScreen.WISHFUL_WINDMILL_FESTIVAL)) as identify_page:
            opened = event_center._wait_event_row_open(
                bot, GiftScreen.WISHFUL_WINDMILL_FESTIVAL)

        self.assertEqual(GiftScreen.WISHFUL_WINDMILL_FESTIVAL, opened)
        self.assertEqual(3, identify_page.call_count)
        self.assertEqual([mock.call(event_center.UI_SETTLE_SECONDS)] * 2,
                         bot.sleep.call_args_list)

    def test_star_trail_coin_claim_uses_exact_user_crop(self):
        claim = cv2.imread(str(IMAGES / "GiftClaims" / "EventCenter" / "GraceOfStarTrail" /
                               "button_claim.png"))
        self.assertEqual((49, 41), claim.shape[:2])

    def test_star_trail_opened_without_claim_is_done(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(event_center, "find",
                                side_effect=[(360, 90), None, None, None, None]),
              mock.patch.object(event_center, "close_congratulations",
                                return_value=False)):
            report = event_center._tap_reward_navigation(bot)

        self.assertEqual(common.ClaimReport(1, 1), report)

    def test_giant_requires_no_items_after_exact_tile(self):
        bot = mock.Mock()
        with (mock.patch.object(event_center, "_ensure_skip_animation",
                                return_value=True),
              mock.patch.object(event_center, "_wait_for",
                                side_effect=(None, (150, 419), None, (70, 174))),
              mock.patch.object(event_center, "_close_exact_congratulations",
                                return_value=False)):
            report, done = event_center._handle_giant(bot)

        self.assertTrue(done)
        self.assertEqual(common.ClaimReport(1, 1), report)
        bot.tap.assert_called_once_with(
            150, 419, delay=event_center.LIST_SCROLL_SETTLE_SECONDS)

    def test_giant_event_ended_is_done_without_tapping(self):
        bot = mock.Mock()
        with (mock.patch.object(event_center, "_wait_for",
                                return_value=(196, 240)),
              mock.patch.object(event_center, "_ensure_skip_animation") as skip):
            report, done = event_center._handle_giant(bot)

        self.assertTrue(done)
        self.assertEqual(common.ClaimReport(0, 1), report)
        skip.assert_not_called()
        bot.tap.assert_not_called()

    def test_dwarf_daily_free_congratulations_is_done(self):
        bot = mock.Mock()
        with (mock.patch.object(event_center, "_ensure_skip_animation",
                                return_value=True),
              mock.patch.object(event_center, "_wait_for",
                                return_value=(355, 180)),
              mock.patch.object(event_center, "_close_exact_congratulations",
                                return_value=True)):
            report, done = event_center._handle_dwarf(bot)

        self.assertTrue(done)
        self.assertEqual(common.ClaimReport(1, 1), report)

    def test_dwarf_missing_daily_free_after_loaded_page_is_done(self):
        bot = mock.Mock()
        with (mock.patch.object(event_center, "_ensure_skip_animation",
                                return_value=True),
              mock.patch.object(event_center, "_wait_for", return_value=None)):
            report, done = event_center._handle_dwarf(bot)

        self.assertTrue(done)
        self.assertEqual(common.ClaimReport(0, 1), report)
        bot.tap.assert_not_called()

    def test_lucky_apple_cannot_shortcut_red_done_before_green_phases(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(event_center, "_apple_button_state",
                                return_value=("done", (300, 620))) as state,
              mock.patch.object(event_center, "_wait_for_any", return_value=None)):
            report, done = event_center._handle_dwarfs_lucky_apple(bot)

        self.assertFalse(done)
        self.assertEqual(common.ClaimReport(), report)
        state.assert_not_called()
        bot.tap.assert_not_called()

    def test_lucky_apple_active_orange_button_wins_ambiguous_match(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.best_match.side_effect = ((0.94, (300, 620)),
                                      (0.92, (300, 620)))
        with (mock.patch.object(event_center, "_scaled_template",
                                side_effect=lambda _bot, name, _screen: name),
              mock.patch.object(event_center, "_apple_button_color_band",
                                return_value=(190.0, 0.75))):
            state, position = event_center._apple_button_state(
                bot, screen,
                "EventCenter/DwarfsLuckyApple/button_red_wish_x10",
                "EventCenter/DwarfsLuckyApple/status_red_wish_x10_done")

        self.assertEqual("active", state)
        self.assertEqual((300, 620), position)

    def test_lucky_apple_disabled_button_requires_clear_score_margin(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.best_match.side_effect = ((0.68, (300, 620)),
                                      (0.95, (300, 620)))
        with (mock.patch.object(event_center, "_scaled_template",
                                side_effect=lambda _bot, name, _screen: name),
              mock.patch.object(event_center, "_apple_button_color_band",
                                return_value=(25.0, 0.06)),
              mock.patch.object(event_center, "_apple_done_ornament_matches",
                                return_value=(True, (0.95, 0.96)))):
            state, _ = event_center._apple_button_state(
                bot, screen,
                "EventCenter/DwarfsLuckyApple/button_red_wish_x10",
                "EventCenter/DwarfsLuckyApple/status_red_wish_x10_done")

        self.assertEqual("done", state)

    def test_lucky_apple_red_post_tap_gray_accepts_live_low_score_layout(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.best_match.return_value = (0.507, (250, 520))
        with (mock.patch.object(event_center, "_scaled_template",
                                return_value=np.zeros((38, 151, 3),
                                                      dtype=np.uint8)),
              mock.patch.object(event_center, "_apple_button_color_band",
                                return_value=(21.3, 0.05)),
              mock.patch.object(event_center, "_apple_special_state",
                                return_value=("red-once", (250, 620)))):
            done = event_center._apple_red_x10_post_tap_done(bot, screen)

        self.assertTrue(done)

    def test_lucky_apple_red_post_tap_gray_still_requires_red_once(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.best_match.return_value = (0.507, (250, 520))
        with (mock.patch.object(event_center, "_scaled_template",
                                return_value=np.zeros((38, 151, 3),
                                                      dtype=np.uint8)),
              mock.patch.object(event_center, "_apple_button_color_band",
                                return_value=(21.3, 0.05)),
              mock.patch.object(event_center, "_apple_special_state",
                                return_value=None)):
            done = event_center._apple_red_x10_post_tap_done(bot, screen)

        self.assertFalse(done)

    def test_lucky_apple_red_phase_uses_gray_fallback_only_after_tap(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(event_center, "_apple_congratulations_hit",
                                return_value=None),
              mock.patch.object(event_center, "_apple_button_state",
                                side_effect=(("active", (250, 520)),
                                             (None, None))),
              mock.patch.object(event_center,
                                "_apple_red_x10_post_tap_done",
                                return_value=True) as gray_done,
              mock.patch.object(event_center, "_close_apple_congratulations",
                                return_value=True)):
            report, done = event_center._apple_phase(
                bot, "EventCenter/DwarfsLuckyApple/button_red_wish_x10",
                "EventCenter/DwarfsLuckyApple/status_red_wish_x10_done")

        self.assertTrue(done)
        self.assertEqual(common.ClaimReport(1, 1), report)
        gray_done.assert_called_once()

    def test_lucky_apple_gray_button_is_done_even_without_both_ornaments(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.best_match.side_effect = ((0.60, (300, 620)),
                                      (0.95, (300, 620)))
        with (mock.patch.object(event_center, "_scaled_template",
                                side_effect=lambda _bot, name, _screen: name),
              mock.patch.object(event_center, "_apple_button_color_band",
                                return_value=(25.0, 0.06)),
              mock.patch.object(event_center, "_apple_done_ornament_matches",
                                return_value=(False, (0.92, 0.31)))):
            state, position = event_center._apple_button_state(
                bot, screen,
                "EventCenter/DwarfsLuckyApple/button_red_wish_x10",
                "EventCenter/DwarfsLuckyApple/status_red_wish_x10_done")

        self.assertEqual("done", state)
        self.assertEqual((300, 620), position)

    def test_lucky_apple_live_low_done_score_uses_located_gray_band(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        # Values captured from the stuck live log: the shared active artwork
        # locates the x-control, but it is visually grey and the DONE crop is
        # a weaker match because this account renders a different border.
        bot.best_match.side_effect = ((0.742, (300, 620)),
                                      (0.560, (300, 620)))
        with (mock.patch.object(event_center, "_scaled_template",
                                side_effect=lambda _bot, name, _screen: name),
              mock.patch.object(event_center, "_apple_button_color_band",
                                return_value=(26.0, 0.07)),
              mock.patch.object(event_center, "_apple_done_ornament_matches")
              as ornament):
            state, position = event_center._apple_button_state(
                bot, screen,
                "EventCenter/DwarfsLuckyApple/button_red_wish_x10",
                "EventCenter/DwarfsLuckyApple/status_red_wish_x10_done")

        self.assertEqual("done", state)
        self.assertEqual((300, 620), position)
        ornament.assert_not_called()

    def test_lucky_apple_low_animated_active_wins_when_done_lacks_ornaments(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.best_match.side_effect = ((0.772, (300, 620)),
                                      (0.994, (300, 620)))
        with (mock.patch.object(event_center, "_scaled_template",
                                side_effect=lambda _bot, name, _screen: name),
              mock.patch.object(event_center, "_apple_button_color_band",
                                return_value=(195.0, 0.78)),
              mock.patch.object(event_center, "_apple_done_ornament_matches",
                                return_value=(False, (0.256, 0.132)))):
            state, position = event_center._apple_button_state(
                bot, screen,
                "EventCenter/DwarfsLuckyApple/button_green_wish_x10",
                "EventCenter/DwarfsLuckyApple/status_green_wish_x10_done")

        self.assertEqual("active", state)
        self.assertEqual((300, 620), position)

    def test_lucky_apple_real_templates_have_separate_gray_yellow_bands(self):
        folder = IMAGES / "GiftClaims" / "EventCenter" / "DwarfsLuckyApple"
        active = cv2.imread(str(folder / "button_red_wish_x10.png"))
        done = cv2.imread(str(folder / "status_red_wish_x10_done.png"))

        def centered(template):
            screen = np.zeros((704, 396, 3), dtype=np.uint8)
            top, left = 500, 140
            height, width = template.shape[:2]
            screen[top:top + height, left:left + width] = template
            return screen, (left + width // 2, top + height // 2)

        active_band = event_center._apple_button_color_band(*centered(active))
        done_band = event_center._apple_button_color_band(*centered(done))

        self.assertGreaterEqual(active_band[0],
                                event_center.APPLE_ACTIVE_SATURATION_MIN)
        self.assertGreaterEqual(active_band[1],
                                event_center.APPLE_ACTIVE_COLOR_RATIO_MIN)
        self.assertLessEqual(done_band[0],
                             event_center.APPLE_DONE_SATURATION_MAX)
        self.assertLessEqual(done_band[1],
                             event_center.APPLE_DONE_COLOR_RATIO_MAX)

    def test_lucky_apple_yellow_band_overrides_high_gray_template_score(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.best_match.side_effect = ((0.68, (300, 620)),
                                      (0.99, (300, 620)))
        with (mock.patch.object(event_center, "_scaled_template",
                                side_effect=lambda _bot, name, _screen: name),
              mock.patch.object(event_center, "_apple_button_color_band",
                                return_value=(190.0, 0.75)),
              mock.patch.object(event_center, "_apple_done_ornament_matches")
              as ornament):
            state, position = event_center._apple_button_state(
                bot, screen,
                "EventCenter/DwarfsLuckyApple/button_red_wish_x10",
                "EventCenter/DwarfsLuckyApple/status_red_wish_x10_done")

        self.assertEqual("active", state)
        self.assertEqual((300, 620), position)
        ornament.assert_not_called()

    def test_lucky_apple_ornament_check_uses_both_template_edges(self):
        template = cv2.imread(str(IMAGES / "GiftClaims" /
                                  "EventCenter" / "DwarfsLuckyApple" /
                                  "status_red_wish_x10_done.png"))
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        top, left = 500, 140
        height, width = template.shape[:2]
        screen[top:top + height, left:left + width] = template
        center = (left + width // 2, top + height // 2)

        matched, scores = event_center._apple_done_ornament_matches(
            screen, template, center)

        self.assertTrue(matched)
        self.assertGreaterEqual(min(scores), event_center.APPLE_ORNAMENT_THRESHOLD)

    def test_lucky_apple_ornament_check_reverses_odd_template_center_exactly(self):
        template = cv2.imread(str(IMAGES / "GiftClaims" /
                                  "EventCenter" / "DwarfsLuckyApple" /
                                  "status_green_wish_x10_done.png"))
        self.assertEqual(1, template.shape[1] % 2)
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        # Odd top-left reproduces the live case where round(x - 111 / 2)
        # shifted the crop one pixel left despite a 0.994 full-image match.
        top, left = 501, 139
        height, width = template.shape[:2]
        screen[top:top + height, left:left + width] = template
        center = (left + width // 2, top + height // 2)

        matched, scores = event_center._apple_done_ornament_matches(
            screen, template, center)

        self.assertTrue(matched)
        self.assertGreaterEqual(min(scores), event_center.APPLE_ORNAMENT_THRESHOLD)

    def test_lucky_apple_closes_congratulations_by_tap_never_back(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)

        def find_named(_bot, name, *_args, **_kwargs):
            if name == event_center.CONGRATULATIONS:
                return (198, 350)
            return None

        with mock.patch.object(event_center, "find", side_effect=find_named):
            closed = event_center._close_apple_congratulations(bot)

        self.assertTrue(closed)
        bot.tap.assert_called_once_with(195, 20,
                                        delay=event_center.UI_SETTLE_SECONDS)
        bot.back.assert_not_called()

    def test_lucky_apple_safe_taps_title_when_popup_template_misses(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with mock.patch.object(event_center, "_apple_congratulations_hit",
                               return_value=None):
            closed = event_center._close_apple_congratulations(
                bot, attempts=1, safe_tap_after_reward=True)

        self.assertTrue(closed)
        bot.tap.assert_called_once_with(195, 20,
                                        delay=event_center.UI_SETTLE_SECONDS)
        bot.back.assert_not_called()

    def test_lucky_apple_never_compares_state_while_congratulations_visible(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(event_center, "_apple_congratulations_hit",
                                side_effect=((198, 350), None)),
              mock.patch.object(event_center, "_close_apple_congratulations",
                                return_value=True) as close_popup,
              mock.patch.object(event_center, "_apple_button_state",
                                return_value=("done", (200, 500))) as state):
            _report, done = event_center._apple_phase(
                bot, "active.png", "done.png", max_taps=1)

        self.assertTrue(done)
        close_popup.assert_called_once_with(bot, attempts=1)
        state.assert_called_once()
        bot.sleep.assert_called_once_with(event_center.UI_SETTLE_SECONDS)

    def test_lucky_apple_three_unreadable_frames_stay_in_same_phase(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        states = ((None, None), (None, None), (None, None),
                  ("done", (200, 500)))
        with (mock.patch.object(event_center, "_apple_congratulations_hit",
                                return_value=None),
              mock.patch.object(event_center, "_apple_button_state",
                                side_effect=states) as state):
            _report, done = event_center._apple_phase(
                bot, "active.png", "done.png", max_taps=1)

        self.assertTrue(done)
        self.assertEqual(4, state.call_count)
        bot.back.assert_not_called()

    def test_lucky_apple_immediately_propagates_worker_120s_timeout(self):
        bot = mock.Mock()
        bot.check.side_effect = TimedOut()

        with self.assertRaises(TimedOut):
            event_center._apple_phase(
                bot, "active.png", "done.png", max_taps=100)

        bot.screenshot.assert_not_called()

    def test_lucky_apple_runs_three_phases_continuously_before_done(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        reports = ((common.ClaimReport(2, 2), True, True),
                   (common.ClaimReport(3, 3), True, True),
                   (common.ClaimReport(4, 4), True, True))
        with (mock.patch.object(event_center, "_wait_for_any",
                                side_effect=((300, 300), (100, 300))),
              mock.patch.object(event_center, "_wait_apple_special_state",
                                return_value=("green-once", (250, 540))),
              mock.patch.object(event_center, "_run_optional_apple_phase",
                                side_effect=reports) as phase):
            report, done = event_center._handle_dwarfs_lucky_apple(bot)

        self.assertTrue(done)
        self.assertEqual(common.ClaimReport(9, 9), report)
        self.assertEqual(
            [("EventCenter/DwarfsLuckyApple/button_green_wish_x100",
              "EventCenter/DwarfsLuckyApple/status_green_wish_x100_done"),
             ("EventCenter/DwarfsLuckyApple/button_green_wish_x10",
              "EventCenter/DwarfsLuckyApple/status_green_wish_x10_done"),
             ("EventCenter/DwarfsLuckyApple/button_red_wish_x10",
              "EventCenter/DwarfsLuckyApple/status_red_wish_x10_done")],
            [call.args[1:3] for call in phase.call_args_list])
        self.assertEqual(2, bot.tap.call_count)

    def test_lucky_apple_only_once_on_both_tabs_is_done(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        green_state = ("EventCenter/DwarfsLuckyApple/status_green_wish_once", (250, 540))
        red_state = ("EventCenter/DwarfsLuckyApple/status_red_wish_once", (250, 540))
        with (mock.patch.object(event_center, "_wait_for_any",
                                side_effect=((300, 300), (100, 300))),
              mock.patch.object(event_center, "_wait_apple_special_state",
                                side_effect=(green_state, red_state)),
              mock.patch.object(event_center, "_run_optional_apple_phase",
                                side_effect=((common.ClaimReport(), True, False),
                                             (common.ClaimReport(), True, False),
                                             (common.ClaimReport(), True, False))) as phase):
            report, done = event_center._handle_dwarfs_lucky_apple(bot)

        self.assertTrue(done)
        self.assertEqual(common.ClaimReport(0, 1), report)
        self.assertEqual(3, phase.call_count)
        self.assertEqual(2, bot.tap.call_count)

    def test_lucky_apple_green_x10_without_x100_is_finished_before_red(self):
        bot = mock.Mock()
        with (mock.patch.object(event_center, "_wait_for_any",
                                side_effect=((300, 300), (100, 300))),
              mock.patch.object(event_center, "_wait_apple_special_state",
                                return_value=("green-once", (250, 540))),
              mock.patch.object(event_center, "_run_optional_apple_phase",
                                side_effect=(
                                    (common.ClaimReport(), True, False),
                                    (common.ClaimReport(3, 3), True, True),
                                    (common.ClaimReport(2, 2), True, True),
                                )) as phase):
            report, done = event_center._handle_dwarfs_lucky_apple(bot)

        self.assertTrue(done)
        self.assertEqual(common.ClaimReport(5, 5), report)
        self.assertIn("button_green_wish_x10", phase.call_args_list[1].args[1])
        self.assertIn("button_red_wish_x10", phase.call_args_list[2].args[1])

    def test_lucky_apple_red_x10_takes_priority_over_red_once(self):
        bot = mock.Mock()
        with (mock.patch.object(event_center, "_wait_for_any",
                                side_effect=((300, 300), (100, 300))),
              mock.patch.object(event_center, "_wait_apple_special_state",
                                return_value=("green-once", (250, 540))) as once,
              mock.patch.object(event_center, "_run_optional_apple_phase",
                                side_effect=(
                                    (common.ClaimReport(), True, False),
                                    (common.ClaimReport(), True, False),
                                    (common.ClaimReport(4, 4), True, True),
                                ))):
            report, done = event_center._handle_dwarfs_lucky_apple(bot)

        self.assertTrue(done)
        self.assertEqual(common.ClaimReport(4, 4), report)
        once.assert_called_once()

    def test_lucky_apple_new_state_crops_match_supplied_files(self):
        folder = IMAGES / "GiftClaims" / "EventCenter" / "DwarfsLuckyApple"
        self.assertEqual((37, 106), cv2.imread(str(
            folder / "status_green_wish_once.png")).shape[:2])
        self.assertEqual((40, 147), cv2.imread(str(
            folder / "status_green_wish_once_gray.png")).shape[:2])
        self.assertEqual((38, 151), cv2.imread(str(
            folder / "status_red_wish_once.png")).shape[:2])
        self.assertEqual((41, 154), cv2.imread(str(
            folder / "status_red_wish_once_gray.png")).shape[:2])

    def test_lucky_apple_green_done_never_finishes_whole_task(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(event_center, "_wait_for_any",
                                return_value=(300, 300)),
              mock.patch.object(event_center, "_run_optional_apple_phase",
                                side_effect=((common.ClaimReport(2, 2), True, True),
                                             (common.ClaimReport(1, 0), False, True)))):
            _report, done = event_center._handle_dwarfs_lucky_apple(bot)

        self.assertFalse(done)

    def test_lucky_apple_tab_variants_use_the_same_tap_position(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)

        def find_variant(_bot, template, *_args, **_kwargs):
            if template.endswith("tab_green_apple_1"):
                return (287, 319)
            return None

        with mock.patch.object(event_center, "find", side_effect=find_variant):
            position = event_center._wait_for_any(
                bot,
                ("EventCenter/DwarfsLuckyApple/tab_green_apple",
                 "EventCenter/DwarfsLuckyApple/tab_green_apple_1"),
                attempts=4, threshold=0.70, region=(45, 40, 100, 68))

        self.assertEqual((287, 319), position)
        bot.screenshot.assert_called_once()

    def test_dwarfs_lucky_apple_policy_belongs_to_activities(self):
        self.assertEqual(
            "activities",
            event_center.POLICY_CATEGORIES["gift_dwarfs_lucky_apple"])
        self.assertIn(("activities", 49), event_center.CATEGORIES)

    def test_lucky_apple_list_scans_down_then_up_at_point_eight_seconds(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        # Two misses while scanning down, one miss while reversing, then the
        # exact row appears on the upward pass.
        with (mock.patch.object(event_center, "find",
                                side_effect=(None, None, None, (144, 320))),
              mock.patch.object(event_center, "_same_list_position",
                                return_value=True)):
            self.assertTrue(event_center._find_dwarfs_lucky_apple_row(bot))

        directions = [(call.args[1], call.args[3])
                      for call in bot.swipe_percent.call_args_list]
        self.assertEqual([(32, 86), (32, 86),
                          (86, 32), (86, 32),
                          (32, 86)], directions)
        self.assertTrue(all(
            call.kwargs["delay"] == event_center.APPLE_LIST_SETTLE_SECONDS
            for call in bot.swipe_percent.call_args_list))
        self.assertEqual(0.8, event_center.APPLE_LIST_SETTLE_SECONDS)
        bot.sleep.assert_not_called()

    def test_activities_tab_uses_fast_apple_settle(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with mock.patch.object(event_center, "find",
                               side_effect=((190, 75), (198, 25))):
            self.assertTrue(event_center._select_category(bot, "activities", 49))

        bot.tap.assert_called_once_with(
            190, 75, delay=event_center.APPLE_LIST_SETTLE_SECONDS)

    def test_event_center_scans_at_most_four_list_positions(self):
        self.assertEqual(3, event_center.MAX_SCROLLS)

    def test_eagle_of_freedom_no_claim_after_full_scroll_is_done(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(event_center, "find", return_value=None),
              mock.patch.object(event_center, "find_all", return_value=[])):
            report, done = event_center._handle_eagle_of_freedom(bot)

        self.assertTrue(done)
        self.assertEqual(common.ClaimReport(0, 1), report)
        self.assertEqual(2, bot.swipe_percent.call_count)
        bot.tap.assert_not_called()

    def test_eagle_claimed_prefix_is_not_treated_as_claim(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)

        def matches(_bot, name, *_args, **_kwargs):
            if name == "EventCenter/EagleOfFreedom/status_claimed":
                return [(330, 350)]
            if name == "EventCenter/EagleOfFreedom/button_claim":
                # The shorter Claim template matches inside Claimed.
                return [(318, 350)]
            return []

        with mock.patch.object(event_center, "find_all", side_effect=matches):
            self.assertEqual([], event_center._eagle_active_claims(bot, screen))

    def test_eagle_content_positions_stop_at_real_bottom(self):
        base = np.zeros((704, 396, 3), dtype=np.uint8)
        moved = base.copy()
        cv2.rectangle(moved, (20, 200), (370, 600), (255, 255, 255), -1)
        self.assertFalse(event_center._eagle_content_moved(base, base.copy()))
        self.assertTrue(event_center._eagle_content_moved(base, moved))

    def test_hypnos_is_done_only_after_rewards_is_absent(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with mock.patch.object(event_center, "find", return_value=None):
            report, done = event_center._handle_hypnos(bot)

        self.assertTrue(done)
        self.assertEqual(common.ClaimReport(0, 1), report)
        self.assertEqual(3, bot.sleep.call_count)

    def test_grace_row_is_checked_without_an_outer_red_dot(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.screenshot.return_value = screen
        visited = set()
        with (mock.patch.object(event_center, "find",
                                side_effect=lambda _bot, name, *_args, **_kwargs:
                                (120, 220) if name.startswith("EventCenter/GraceOfStarTrail/")
                                else None),
              mock.patch.object(event_center, "_row_dots", return_value=[]),
              mock.patch.object(event_center, "identify",
                                return_value=GiftScreen.GRACE_OF_STAR_TRAIL),
              mock.patch.object(event_center, "_process_opened_event") as process,
              mock.patch.object(event_center, "_back_to_list", return_value=True),
              mock.patch.object(event_center, "_list_signature", return_value=b"same"),
              mock.patch.object(event_center, "_verify_clean", return_value=True)):
            self.assertTrue(event_center._scan_category(bot, "limited", visited))

        process.assert_called_once_with(bot)
        self.assertIn(event_center.FORCED_EVENT_PREFIX + b"grace_of_star_trail",
                      visited)

    def test_dwarf_row_is_checked_without_an_outer_red_dot(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.screenshot.return_value = screen
        visited = {event_center.FORCED_EVENT_PREFIX + b"grace_of_star_trail"}
        with (mock.patch.object(event_center, "find",
                                side_effect=lambda _bot, name, *_args, **_kwargs:
                                (120, 220) if name.startswith("EventCenter/DwarfsTreasure/")
                                else None),
              mock.patch.object(event_center, "_row_dots", return_value=[]),
              mock.patch.object(event_center, "identify",
                                return_value=GiftScreen.DWARFS_TREASURE),
              mock.patch.object(event_center, "_process_opened_event") as process,
              mock.patch.object(event_center, "_back_to_list", return_value=True),
              mock.patch.object(event_center, "_list_signature", return_value=b"same"),
              mock.patch.object(event_center, "_verify_clean", return_value=True)):
            self.assertTrue(event_center._scan_category(bot, "limited", visited))

        process.assert_called_once_with(bot)
        self.assertIn(event_center.FORCED_EVENT_PREFIX + b"dwarfs_treasure",
                      visited)

    def test_grace_opened_page_uses_exact_star_trail_control(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        expected = common.ClaimReport(1, 1)
        with (mock.patch.object(event_center, "identify",
                               return_value=GiftScreen.GRACE_OF_STAR_TRAIL),
              mock.patch.object(event_center, "_handle_grace",
                                return_value=(expected, True)) as process,
              mock.patch.dict(event_center.EXACT_HANDLERS,
                              {GiftScreen.GRACE_OF_STAR_TRAIL:
                               event_center._handle_grace})):
            self.assertEqual(expected, event_center._process_opened_event(bot))
        process.assert_called_once_with(bot)

    def test_grace_without_opened_gift_stays_pending(self):
        bot = mock.Mock()
        bot.is_daily_done.return_value = False
        unresolved = common.ClaimReport(1, 0)
        with (mock.patch.object(event_center, "identify",
                                return_value=GiftScreen.GRACE_OF_STAR_TRAIL),
              mock.patch.object(event_center, "_handle_grace",
                                return_value=(unresolved, False)),
              mock.patch.dict(event_center.EXACT_HANDLERS,
                              {GiftScreen.GRACE_OF_STAR_TRAIL:
                               event_center._handle_grace})):
            self.assertEqual(unresolved,
                             event_center._process_opened_event(bot))

        bot.mark_daily_done.assert_not_called()

    def test_grace_claim_search_includes_top_right_control(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        seen_regions = []

        def find_named(_bot, name, *_args, **kwargs):
            seen_regions.append((name, kwargs.get("region")))
            if name.endswith("button_star_trail_gift_current"):
                return (360, 90)
            if name == "EventCenter/GraceOfStarTrail/button_claim":
                return (355, 116)
            return None

        with (mock.patch.object(event_center, "find", side_effect=find_named),
              mock.patch.object(event_center, "close_congratulations",
                                side_effect=(False, True))):
            report = event_center._tap_reward_navigation(bot)

        self.assertEqual(common.ClaimReport(2, 1), report)
        self.assertIn(("EventCenter/GraceOfStarTrail/button_claim",
                       event_center.REWARD_NAV_REGION), seen_regions)

    def test_event_center_scans_limited_then_activities(self):
        bot = mock.Mock()
        bot.is_daily_done.return_value = True
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.screenshot.return_value = screen
        with (mock.patch.object(event_center, "find", return_value=(198, 25)),
              mock.patch.object(event_center, "_select_category",
                                return_value=True) as select,
              mock.patch.object(event_center, "_scan_category",
                                return_value=True) as scan,
              mock.patch.object(event_center, "_category_db_done",
                                side_effect=(False, True, False, True)),
              mock.patch.object(event_center, "return_home")):
            self.assertTrue(event_center.run_opened(bot, set()))

        self.assertEqual([mock.call(bot, "limited", 18),
                          mock.call(bot, "activities", 49)],
                         select.call_args_list)
        self.assertEqual([call.args[1] for call in scan.call_args_list],
                         ["limited", "activities"])

    def test_event_center_selects_limited_by_its_exact_button_before_scan(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.screenshot.return_value = screen
        with mock.patch.object(event_center, "find",
                               side_effect=((72, 78), (198, 25))) as find:
            self.assertTrue(event_center._select_category(bot, "limited", 18))

        self.assertEqual("EventCenter/tab_limited", find.call_args_list[0].args[1])
        bot.tap.assert_called_once_with(72, 78,
                                        delay=event_center.UI_SETTLE_SECONDS)

    def test_event_center_continues_activities_while_limited_is_pending(self):
        bot = mock.Mock()
        bot.is_daily_done.return_value = False
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(event_center, "find", return_value=(198, 25)),
              mock.patch.object(event_center, "_select_category",
                                return_value=True) as select,
              mock.patch.object(event_center, "_scan_category",
                                return_value=True) as scan,
              mock.patch.object(event_center, "return_home")):
            self.assertFalse(event_center.run_opened(bot, set()))

        self.assertEqual([mock.call(bot, "limited", 18),
                          mock.call(bot, "activities", 49)],
                         select.call_args_list)
        self.assertEqual(["limited", "activities"],
                         [call.args[1] for call in scan.call_args_list])

    def test_event_center_exact_pending_is_remembered_for_current_window(self):
        bot = mock.Mock()
        setattr(bot, event_center.PENDING_THIS_RUN_ATTR, set())
        policy = next(policy for policy in event_center.EVENT_POLICIES
                      if policy.key == "gift_wishful_windmill_festival")
        with mock.patch.dict(event_center.EXACT_HANDLERS,
                             {policy.screen: lambda _bot:
                              (common.ClaimReport(), False)}):
            event_center._process_known_event(bot, policy)

        self.assertIn(policy.key,
                      getattr(bot, event_center.PENDING_THIS_RUN_ATTR))

    def test_limited_scan_never_counts_lucky_apple_as_missing(self):
        bot = mock.Mock()
        bot.is_daily_done.return_value = False
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        dragon = "gift_dragon_battle"
        apple = "gift_dwarfs_lucky_apple"

        def scanned_limited(_bot, _handled):
            setattr(bot, event_center.SCANNED_CATEGORIES_ATTR, {"limited"})
            setattr(bot, event_center.SCAN_COMPLETE_ATTR, True)
            return False

        with (mock.patch.object(event_center_zone, "identify",
                                return_value=GiftScreen.EVENT_CENTER),
              mock.patch.object(event_center_zone, "run_opened",
                                side_effect=scanned_limited)):
            inspected = event_center_zone._sweep(bot, [dragon, apple])

        self.assertIn(dragon, inspected)
        self.assertNotIn(apple, inspected)

    def test_event_center_skips_categories_completed_before_boss_yield(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        handled = {event_center._category_done_key("limited"),
                   event_center._category_done_key("activities")}
        with (mock.patch.object(event_center, "find", return_value=(198, 25)),
              mock.patch.object(event_center, "_select_category",
                                return_value=True) as select,
              mock.patch.object(event_center, "_scan_category",
                                return_value=True) as scan,
              mock.patch.object(event_center, "return_home")):
            self.assertTrue(event_center.run_opened(bot, handled))

        select.assert_not_called()
        scan.assert_not_called()

    def test_event_center_special_templates_are_tightly_cropped(self):
        rewards = cv2.imread(str(IMAGES / "GiftClaims" /
                                 "EventCenter" / "PreciousBlazonExchange" / "button_rewards_text.png"))
        daily = cv2.imread(str(IMAGES / "GiftClaims" /
                               "EventCenter" / "DwarfsTreasure" / "button_daily_free_chest.png"))
        hypnos = cv2.imread(str(IMAGES / "GiftClaims" /
                                "EventCenter" / "HypnosDream" / "button_rewards_text.png"))
        self.assertLessEqual(rewards.shape[0], 22)
        self.assertLessEqual(hypnos.shape[0], 18)
        self.assertLessEqual(daily.shape[0], 50)
        self.assertLessEqual(daily.shape[1], 50)

    def test_star_trail_current_icon_is_a_clickable_crop(self):
        icon = cv2.imread(str(IMAGES / "GiftClaims" / "EventCenter" / "GraceOfStarTrail" /
                              "button_star_trail_gift_current.png"))
        self.assertEqual((75, 68), icon.shape[:2])
        self.assertEqual("EventCenter/GraceOfStarTrail/button_star_trail_gift_current",
                         event_center.REWARD_NAVIGATION[0])

    def test_revelation_and_sealed_treasury_are_immediate_skips(self):
        bot = mock.Mock()
        for name in (GiftScreen.REVELATION_OF_HORUS,
                     GiftScreen.SEALED_IMPERIAL_TREASURY):
            with (self.subTest(screen=name),
                  mock.patch.object(event_center, "identify", return_value=name),
                  mock.patch.object(event_center, "_process_current_event_content") as process):
                self.assertEqual(common.ClaimReport(),
                                 event_center._process_opened_event(bot))
                process.assert_not_called()

    def test_missing_event_center_labels_are_reported_not_done_on_first_pass(self):
        bot = mock.Mock()
        bot.is_daily_done.return_value = False
        pallas_key = "gift_blessing_of_pallas"

        missing = event_center._record_missing_event_policies(bot, {pallas_key})

        self.assertIn("gift_dragon_battle", missing)
        self.assertIn("gift_poseidons_day", missing)
        self.assertIn("gift_hypnos_dream", missing)
        self.assertNotIn(pallas_key, missing)
        bot.mark_daily_done.assert_not_called()

    def test_found_but_unfinished_event_is_not_closed_as_missing(self):
        bot = mock.Mock()
        bot.is_daily_done.return_value = False
        dragon_key = "gift_dragon_battle"

        missing = event_center._record_missing_event_policies(bot, {dragon_key})

        self.assertNotIn(dragon_key, missing)
        bot.mark_daily_done.assert_not_called()

    def test_generic_claim_templates_are_text_only(self):
        for name in common.TEXT_CLAIM_CONTROLS:
            image = cv2.imread(str(IMAGES / "GiftClaims" / f"{name}.png"))
            with self.subTest(template=name):
                self.assertIsNotNone(image)
                self.assertLessEqual(image.shape[0], 35)
                self.assertLessEqual(image.shape[1], 110)

    def test_activities_has_no_red_dot_shortcut(self):
        self.assertFalse(hasattr(event_center, "_activities_facebook_red"))
        bot = mock.Mock()
        self.assertTrue(event_center._verify_clean(bot, "activities"))
        bot.screenshot.assert_not_called()
        bot.record.assert_called_once()

    def test_event_center_checkpointed_persistent_badge_is_skip_done(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        signature = bytes([0] * 24)
        visited = {event_center._category_signature("limited", signature)}
        with (mock.patch.object(event_center, "_row_dots", return_value=[]),
              mock.patch.object(event_center, "_verify_clean", return_value=False)):
            clean = event_center._scan_category(bot, "limited", visited)

        self.assertTrue(clean)
        self.assertTrue(any("skip/done" in call.args[0]
                            for call in bot.record.call_args_list))

    def test_each_child_module_owns_its_image_folder(self):
        folders = {
            spec.task.key: spec.tab.split("/", 1)[0]
            for spec in (*valuable_event.SPECS, *super_value_return.SPECS)
        }
        for key, folder in folders.items():
            with self.subTest(task=key):
                self.assertTrue((IMAGES / "GiftClaims" / folder).is_dir())
                self.assertTrue(any((IMAGES / "GiftClaims" / folder).glob("*.png")))

    def test_common_claim_text_matches_claim_and_claim_free_prefix(self):
        claim = cv2.imread(str(IMAGES / "GiftClaims" / "EventCenter" / "BackToTerritory" /
                              "button_claim.png"))
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        screen[400:400 + claim.shape[0], 200:200 + claim.shape[1]] = claim
        self.assertIsNotNone(common.find(
            self.bot, "Common/button_claim_text", screen, threshold=0.76))

        for collection in (valuable_event.COMMON_LOWER_CLAIMS,
                           super_value_return.COMMON_LOWER_CLAIMS,
                           event_center.FIXED_CLAIMS,
                           back_to_territory.FIXED_CLAIMS):
            self.assertIn("Common/button_claim_text", collection)


if __name__ == "__main__":
    unittest.main()
