import unittest
from importlib import import_module
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import cv2
import numpy as np

from bot.activities import gift_claims
from bot.activities.gift_claims import common, lobby, scan as gift_scan
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
general_vault = import_module("bot.activities.gift_claims.valuable_event.general_vault.run")
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
golden_tree_rewards = import_module(
    "bot.activities.gift_claims.valuable_event.golden_tree_rewards.run")
refining_weekly_card = import_module(
    "bot.activities.gift_claims.super_value_return.refining_weekly_card.run")
active_monthly_card = import_module(
    "bot.activities.gift_claims.valuable_event.active_monthly_card.run")
hall_of_historic_generals = import_module(
    "bot.activities.gift_claims.valuable_event.hall_of_historic_generals.run")
soul_of_spiritual_beast = import_module(
    "bot.activities.gift_claims.valuable_event.soul_of_spiritual_beast.run")
super_value_weekly_card = import_module(
    "bot.activities.gift_claims.valuable_event.super_value_weekly_card.run")
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
    def test_gift_claim_images_are_split_into_three_event_families(self):
        root = IMAGES / "GiftClaims"
        self.assertEqual(
            {"Common", "Event", "EventCenter", "FollowUs", "Lobby",
             "SuperValueReturn", "ValuableEvent"},
            {path.name for path in root.iterdir() if path.is_dir()})
        self.assertEqual(
            {"RevelryCarnival"},
            {path.name for path in (root / "Event").iterdir()
             if path.is_dir()})
        self.assertEqual(17, len([
            path for path in (root / "EventCenter").iterdir()
            if path.is_dir()]))
        self.assertEqual(18, len([
            path for path in (root / "ValuableEvent").iterdir()
            if path.is_dir()]))
        self.assertEqual(8, len([
            path for path in (root / "SuperValueReturn").iterdir()
            if path.is_dir()]))

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

    def test_dragon_battle_reward_and_claimed_images_are_supplied(self):
        reward = cv2.imread(str(
            IMAGES / "GiftClaims" / "EventCenter" / "DragonBattle" /
            "reward.png"))
        claimed = cv2.imread(str(
            IMAGES / "GiftClaims" / "EventCenter" / "DragonBattle" /
            "status_reward_claimed.png"))
        self.assertEqual((42, 52), reward.shape[:2])
        self.assertEqual((34, 40), claimed.shape[:2])

    def test_dragon_battle_is_done_after_congratulations(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(dragon_battle, "_reward_claimed",
                                return_value=False),
              mock.patch.object(dragon_battle, "_find_reward_chest",
                                return_value=(370, 229)),
              mock.patch.object(dragon_battle, "close_congratulations",
                                return_value=True)):
            report, done = event_center._handle_dragon_battle(bot)

        self.assertTrue(done)
        self.assertEqual(common.ClaimReport(1, 1), report)
        bot.tap.assert_called_once_with(
            370, 229, delay=dragon_battle.STEP_DELAY)

    def test_dragon_battle_stays_pending_without_terminal_state(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(dragon_battle, "_reward_claimed",
                                return_value=False),
              mock.patch.object(dragon_battle, "_find_reward_chest",
                                return_value=(370, 229)),
              mock.patch.object(dragon_battle, "close_congratulations",
                                return_value=False)):
            report, done = event_center._handle_dragon_battle(bot)

        self.assertFalse(done)
        self.assertEqual(common.ClaimReport(1, 0), report)

    def test_dragon_battle_missing_chest_is_pending_without_tapping(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(dragon_battle, "_reward_claimed",
                                return_value=False),
              mock.patch.object(dragon_battle, "_find_reward_chest",
                                return_value=None)):
            report, done = event_center._handle_dragon_battle(bot)

        self.assertFalse(done)
        self.assertEqual(common.ClaimReport(), report)
        bot.tap.assert_not_called()

    def test_dragon_battle_opened_chest_is_done_without_tapping(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with mock.patch.object(dragon_battle, "_reward_claimed",
                               return_value=True):
            report, done = dragon_battle.claim_opened(bot)

        self.assertTrue(done)
        self.assertEqual(common.ClaimReport(0, 1), report)
        bot.tap.assert_not_called()

    def test_dragon_battle_standalone_tap_requires_terminal_state(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(dragon_battle, "open_event_center_event",
                                return_value=True),
              mock.patch.object(dragon_battle, "_reward_claimed",
                                return_value=False),
              mock.patch.object(dragon_battle, "_find_reward_chest",
                                return_value=(370, 229)),
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

    def test_valuable_event_finder_accepts_name_median(self):
        template = cv2.imread(str(
            IMAGES / "GiftClaims" / "ValuableEvent" /
            "launcher_name_median.png"))
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        height, width = template.shape[:2]
        screen[577:577 + height, 232:232 + width] = template
        self.assertEqual(
            (232 + width // 2, 577 + height // 2),
            common.find_valuable_event(self.bot, screen))

    def test_lobby_valuable_event_finder_uses_ocr_caption(self):
        # Hàm cũ (ảnh launcher_*) đã xoá: lobby dùng bot/ocr/find_valuable_event, quy về chỗ cao hơn tâm chữ "Event" 10 px.
        screen = cv2.imread(str(Path(__file__).parent / "screens" / "lobby_valuable_event_done.png"))
        x, y = lobby.find_valuable_event(self.bot, screen)
        self.assertAlmostEqual(260, x, delta=4)
        self.assertAlmostEqual(580, y, delta=4)

    def test_valuable_event_launcher_template_contains_only_name(self):
        template = cv2.imread(str(
            IMAGES / "GiftClaims" / "ValuableEvent" /
            "launcher_name_median.png"))
        self.assertIsNotNone(template)
        self.assertEqual((25, 54), template.shape[:2])

    def test_super_value_return_finder_uses_login_gifts_launcher_median(self):
        template = cv2.imread(str(
            IMAGES / "GiftClaims" / "SuperValueReturn" /
            "launcher_login_gifts_median.png"))
        self.assertEqual((67, 71), template.shape[:2])
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        height, width = template.shape[:2]
        left, top = 7, 538
        screen[top:top + height, left:left + width] = template
        self.assertEqual(
            (left + width // 2, top + height // 2 - 15),
            common.find_super_value_return(self.bot, screen))

    def test_super_value_return_finder_accepts_first_purchase_median(self):
        template = cv2.imread(str(
            IMAGES / "GiftClaims" / "SuperValueReturn" /
            "launcher_first_purchase_median.png"))
        self.assertEqual((76, 70), template.shape[:2])
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        height, width = template.shape[:2]
        left, top = 8, 528
        screen[top:top + height, left:left + width] = template
        self.assertEqual(
            (left + width // 2, top + height // 2),
            common.find_super_value_return(self.bot, screen))

    def test_super_value_return_finder_accepts_192710_gold_artwork(self):
        template = cv2.imread(str(
            IMAGES / "GiftClaims" / "SuperValueReturn" /
            "launcher_super_value_return_192710.png"))
        self.assertEqual((18, 50), template.shape[:2])
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        height, width = template.shape[:2]
        left, top = 8, 555
        screen[top:top + height, left:left + width] = template
        self.assertEqual(
            (left + width // 2, top + height // 2),
            common.find_super_value_return(self.bot, screen))

    def test_super_value_return_finder_rejects_blank_city_region(self):
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        self.assertIsNone(common.find_super_value_return(self.bot, screen))

    def test_super_value_return_empire_fallback_uses_measured_threshold(self):
        self.assertEqual(0.62,
                         common.SUPER_VALUE_RETURN_EMPIRE_THRESHOLD)

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

        bot.tap.assert_called_once_with(256, 260, delay=1)
        self.assertTrue(any(
            "bấm fallback x=256 y=260" in call.args[0]
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
              mock.patch.object(lobby, "find_super_value_return",
                                return_value=(30, 560)),
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

    def test_open_tab_taps_tab_waits_for_page_change_then_taps_title(self):
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
        self.assertEqual([("tap", (120, 92)), ("tap_percent", (50, 5))], calls)   # bấm tab ở y 13% (92 / 704), không ở tâm icon
        self.assertEqual(3 + 1, bot.sleep.call_count)                 # chờ sang trang 3 x 1s, bấm tiêu đề rồi nghỉ 1s

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

    def test_open_tab_does_not_tap_already_selected_tab_but_taps_title(self):
        screen = cv2.imread(str(Path(__file__).parent / "screens" /
                                "valuable_event_tab_limited_offer_selected.png"))
        bot = mock.Mock()
        bot.screenshot.return_value = screen
        self.assertTrue(valuable_event_zone.open_tab(bot, (174, 85)))
        bot.tap.assert_not_called()
        bot.tap_percent.assert_called_once_with(50, 5)
        bot.sleep.assert_called_once_with(1)

    def test_open_tab_retaps_once_then_gives_up(self):
        same = np.random.default_rng(5).integers(0, 255, (704, 396, 3), dtype=np.uint8)
        bot = mock.Mock()
        bot.screenshot.return_value = same
        with mock.patch.object(valuable_event_zone, "tab_selected", return_value=False):
            self.assertFalse(valuable_event_zone.open_tab(bot, (120, 80)))
        self.assertEqual(2, bot.tap.call_count)                       # bấm + bấm lại 1 lần
        bot.tap_percent.assert_not_called()                           # chưa sang trang: không bấm tiêu đề
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

    def test_open_valuable_event_falls_back_to_ocr_when_name_median_is_missing(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(valuable_event_zone, "on_main", return_value=True),
              mock.patch.object(valuable_event_zone, "to_city", return_value=False),
              mock.patch.object(valuable_event_zone, "find_valuable_event_median",
                                return_value=None) as median,
              mock.patch.object(valuable_event_zone, "find_valuable_event",
                                return_value=(260, 590)),
              mock.patch.object(valuable_event_zone, "identify",
                                side_effect=(None, None, GiftScreen.VALUABLE_EVENT))):
            self.assertTrue(valuable_event_zone.open_valuable_event(bot))

        bot.tap.assert_called_once_with(260, 560)
        median.assert_called_once_with(bot, bot.screenshot.return_value)
        self.assertEqual(3, bot.sleep.call_count)
        bot.swipe_percent.assert_not_called()              # kéo dài nằm trong search_pass, sau khi làm event đang thấy

    def test_open_valuable_event_uses_name_median_before_ocr(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.screenshot.return_value = screen
        with (mock.patch.object(valuable_event_zone, "on_main", return_value=True),
              mock.patch.object(valuable_event_zone, "to_city", return_value=False),
              mock.patch.object(valuable_event_zone, "find_valuable_event",
                                return_value=None) as ocr,
              mock.patch.object(valuable_event_zone, "find_valuable_event_median",
                                return_value=(260, 590)) as median,
              mock.patch.object(valuable_event_zone, "identify",
                                return_value=GiftScreen.VALUABLE_EVENT)):
            self.assertTrue(valuable_event_zone.open_valuable_event(bot))

        median.assert_called_once_with(bot, screen)
        ocr.assert_not_called()
        bot.tap.assert_called_once_with(260, 560)

    def test_open_valuable_event_uses_user_fallback_when_no_image_matches(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(valuable_event_zone, "on_main", return_value=True),
              mock.patch.object(valuable_event_zone, "to_city", return_value=False),
              mock.patch.object(valuable_event_zone, "find_valuable_event_median",
                                return_value=None),
              mock.patch.object(valuable_event_zone, "find_valuable_event",
                                return_value=None),
              mock.patch.object(valuable_event_zone, "identify",
                                return_value=GiftScreen.VALUABLE_EVENT)):
            self.assertTrue(valuable_event_zone.open_valuable_event(bot))

        bot.tap.assert_called_once_with(256, 260)

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

    def test_open_valuable_event_gives_up_after_three_tries(self):
        bot = mock.Mock(spec=["screenshot", "tap", "sleep", "check", "record", "is_daily_done"])
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.is_daily_done.return_value = False
        with (mock.patch.object(valuable_event_zone, "on_main", return_value=True),
              mock.patch.object(valuable_event_zone, "to_city", return_value=False),
              mock.patch.object(valuable_event_zone, "find_valuable_event_median",
                                return_value=None),
              mock.patch.object(valuable_event_zone, "find_valuable_event",
                                return_value=(260, 590)),
              mock.patch.object(valuable_event_zone, "identify", return_value=None)):
            self.assertFalse(valuable_event_zone.open_valuable_event(bot))

        self.assertEqual(3, bot.tap.call_count)
        self.assertEqual(3 * 8, bot.sleep.call_count)

    def test_zone_marks_absent_db_task_done_only_after_three_full_sweeps(self):
        done = set()
        bot = mock.Mock()
        bot.is_daily_done.side_effect = lambda key: key in done
        bot.mark_daily_done.side_effect = done.add
        bot.done_at.side_effect = lambda key: "today" if key in done else None
        bot.forget_daily.side_effect = done.discard
        task_key = "gift_missing_test"
        sweep = mock.Mock(return_value={task_key})

        self.assertTrue(gift_scan.run_zone(
            bot, "gift_zone_test", [(task_key, "Missing Test")], sweep))

        self.assertEqual(3, sweep.call_count)
        self.assertTrue({f"{task_key}_miss_{index}" for index in range(1, 4)}
                        .issubset(done))
        self.assertIn(task_key, done)
        self.assertIn("gift_zone_test", done)

    def test_super_value_return_uses_dedicated_image_finder(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(lobby, "return_home", return_value=True),
              mock.patch.object(lobby, "find_super_value_return",
                                return_value=(34, 555)) as finder,
              mock.patch.object(lobby, "identify",
                                side_effect=(None,
                                             GiftScreen.SUPER_VALUE_RETURN))):
            self.assertTrue(lobby.open_named(bot, GiftScreen.SUPER_VALUE_RETURN))

        finder.assert_called_once()
        bot.tap.assert_called_once_with(34, 555, delay=1)

    def test_super_value_return_uses_fixed_fallback_when_images_are_missing(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(lobby, "return_home", return_value=True),
              mock.patch.object(lobby, "SUPER_VALUE_LAUNCH_ATTEMPTS", 1),
              mock.patch.object(lobby, "find_super_value_return",
                                return_value=None) as finder,
              mock.patch.object(lobby, "find_valuable_event",
                                return_value=None),
              mock.patch.object(lobby, "identify",
                                side_effect=(None,
                                             GiftScreen.SUPER_VALUE_RETURN))):
            self.assertTrue(lobby.open_named(bot, GiftScreen.SUPER_VALUE_RETURN))

        finder.assert_called_once()
        bot.tap.assert_called_once_with(35, 560, delay=1)
        self.assertTrue(any("bấm fallback x=35 y=560" in call.args[0]
                            for call in bot.record.call_args_list))

    def test_super_value_return_does_not_route_through_valuable_event(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(lobby, "return_home", return_value=True),
              mock.patch.object(lobby, "SUPER_VALUE_LAUNCH_ATTEMPTS", 1),
              mock.patch.object(lobby, "find_super_value_return",
                                return_value=None),
              mock.patch.object(lobby, "find_valuable_event") as valuable,
              mock.patch.object(lobby, "identify", return_value=None),
              mock.patch.object(lobby, "_switch_parent_carousel") as switch):
            self.assertFalse(lobby.open_named(
                bot, GiftScreen.SUPER_VALUE_RETURN))

        valuable.assert_not_called()
        switch.assert_not_called()
        bot.tap.assert_called_once_with(35, 560, delay=1)

    def test_parent_switch_confirms_both_edges_without_swipe_ceiling(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.screenshot.return_value = screen
        with (mock.patch.object(lobby, "identify",
                                return_value=GiftScreen.VALUABLE_EVENT),
              mock.patch.object(lobby, "find", return_value=None)):
            self.assertFalse(lobby._switch_parent_carousel(
                bot, GiftScreen.SUPER_VALUE_RETURN))

        swipes = bot.swipe_percent.call_args_list
        self.assertEqual(4, len(swipes))
        self.assertTrue(all(call.args[:4] == (20, 14, 85, 14)
                            for call in swipes[:2]))
        self.assertTrue(all(call.args[:4] == (85, 14, 55, 14)
                            for call in swipes[2:]))

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
            "gift_super_value_weekly_card",
            "gift_successive_purchase_benefits", "gift_optional_package",
            "gift_active_monthly_card", "gift_tomb_expedition",
            "gift_wheel_of_dragon_war", "gift_golden_tree_rewards",
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

    def test_carousel_edge_detection_ignores_artwork_above_name_band(self):
        before = np.zeros((704, 396, 3), dtype=np.uint8)
        after = before.copy()
        # Animated task artwork is above y=84 (12%); tab labels are below it.
        after[50:80, 120:180] = (255, 255, 255)
        self.assertFalse(valuable_named_flow.carousel_moved(before, after))

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
              mock.patch.object(valuable_event, "find", side_effect=find_named),
              mock.patch.object(valuable_event, "process_exact",
                                return_value=False) as lower,
              mock.patch.object(valuable_event, "carousel_moved",
                                return_value=False)):
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
              mock.patch.object(valuable_event, "find", side_effect=find_named),
              mock.patch.object(valuable_event, "process_exact",
                                side_effect=process) as lower,
              mock.patch.object(valuable_event, "carousel_moved",
                                return_value=False),
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

    def test_valuable_uses_visible_screen_order_not_spec_priority(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.screenshot.return_value = screen
        first, second = valuable_event.SPECS[:2]
        processed = []

        def find_named(_bot, name, *_args, **_kwargs):
            if name == valuable_event.PAGE:
                return (198, 25)
            if name == first.tab:
                return (180, 70)
            if name == second.tab:
                return (60, 70)
            return None

        def process(_bot, flow):
            processed.append(flow)
            return True

        with (mock.patch.object(valuable_event, "SPECS", (first, second)),
              mock.patch.object(valuable_event, "find", side_effect=find_named),
              mock.patch.object(valuable_event, "process_exact",
                                side_effect=process)):
            _, clean = valuable_event.run_opened(
                bot, {first.task.key, second.task.key})

        self.assertTrue(clean)
        self.assertEqual([second.flow, first.flow], processed)

    def test_valuable_absent_task_requires_both_confirmed_edges(self):
        bot = mock.Mock()
        bot.is_daily_done.return_value = False
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.screenshot.return_value = screen
        spec = valuable_event.SPECS[0]

        def find_named(_bot, name, *_args, **_kwargs):
            return (198, 25) if name == valuable_event.PAGE else None

        with (mock.patch.object(valuable_event, "SPECS", (spec,)),
              mock.patch.object(valuable_event, "find", side_effect=find_named),
              mock.patch.object(valuable_event, "carousel_moved",
                                return_value=False)):
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

    def test_general_vault_no_button_in_upper_half_is_done(self):
        bot = mock.Mock()
        with mock.patch.object(general_vault, "find_any", return_value=None) as find_any:
            self.assertTrue(general_vault.claim_daily_free(bot))
        self.assertEqual((0, 18, 100, 50), find_any.call_args.kwargs["region"])
        bot.tap.assert_not_called()

    def test_general_vault_taps_then_waits_for_congratulations(self):
        bot = mock.Mock()
        with (mock.patch.object(general_vault, "find_any",
                                return_value=("ValuableEvent/GeneralVault/button_daily_free", (200, 300))),
              mock.patch.object(general_vault, "close_congratulations",
                                side_effect=(False, False, True)) as congrats):
            self.assertTrue(general_vault.claim_daily_free(bot))
        bot.tap.assert_called_once_with(200, 300)
        self.assertEqual(3, congrats.call_count)            # 1s, 2s, 3s: thấy Congratulations
        self.assertEqual(3, bot.sleep.call_count)

    def test_general_vault_retries_once_then_pending(self):
        bot = mock.Mock()
        with (mock.patch.object(general_vault, "find_any",
                                return_value=("ValuableEvent/GeneralVault/button_daily_free", (200, 300))),
              mock.patch.object(general_vault, "close_congratulations", return_value=False)):
            self.assertFalse(general_vault.claim_daily_free(bot))
        self.assertEqual(2, bot.tap.call_count)              # bước 3 tối đa 2 lần
        self.assertEqual(2 * 5, bot.sleep.call_count)        # mỗi lần chờ Congratulations tối đa 5 x 1s

    def test_general_vault_button_gone_after_first_tap_is_done(self):
        bot = mock.Mock()
        with (mock.patch.object(general_vault, "find_any",
                                side_effect=(("ValuableEvent/GeneralVault/button_daily_free", (200, 300)), None)),
              mock.patch.object(general_vault, "close_congratulations", return_value=False)):
            self.assertTrue(general_vault.claim_daily_free(bot))
        bot.tap.assert_called_once_with(200, 300)

    def test_strict_terminal_tasks_never_finish_from_missing_claim_button(self):
        valuable = {spec.task.key: spec.flow for spec in valuable_event.SPECS}
        super_value = {spec.task.key: spec.flow
                       for spec in super_value_return.SPECS}
        strict = {
            "gift_resource_consumption_sprint": valuable,
            "gift_optional_package": valuable,
            "gift_successive_purchase_benefits": valuable,
            "gift_tomb_expedition": valuable,
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
        self.assertIs(general_vault.claim_daily_free, valuable["gift_general_vault"].handler)
        self.assertEqual(("SuperValueReturn/EmpireDepot/chest_open",),
                         super_value["gift_empire_depot"].done)
        self.assertTrue(super_value["gift_lucky_raffle"].congratulations_done)
        self.assertEqual(("SuperValueReturn/LuckyRaffle/chest_open",),
                         super_value["gift_lucky_raffle"].done)

    def test_horizontal_carousels_have_no_local_swipe_ceiling(self):
        self.assertFalse(hasattr(valuable_event, "MAX_SWIPES"))
        self.assertFalse(hasattr(super_value_return, "MAX_SWIPES"))
        self.assertFalse(hasattr(back_to_territory, "MAX_SWIPES"))

    def test_back_to_territory_clean_check_confirms_both_edges(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.screenshot.return_value = screen
        with (mock.patch.object(back_to_territory, "_dots", return_value=[]),
              mock.patch.object(back_to_territory, "carousel_moved",
                                return_value=False)):
            self.assertTrue(back_to_territory._verify_clean(bot))

        self.assertEqual(4, bot.swipe_percent.call_count)

    def test_gift_priorities_put_revelry_after_event_center(self):
        from bot.worker.priority import DATA

        priorities = {
            item["key"]: item["priority"]
            for item in DATA["Gift Claims"]
        }
        self.assertGreater(priorities["gift_event_center"],
                           priorities["revelry_carnival"])
        self.assertGreater(priorities["revelry_carnival"],
                           priorities["gift_valuable_event"])
        self.assertGreater(priorities["gift_valuable_event"],
                           priorities["gift_super_value_return"])
        self.assertLess(priorities["gift_event_center"], 10)

    def test_revelry_uses_claim_gifts_toggle(self):
        from bot.worker.priority import DATA

        row = next(item for item in DATA["Gift Claims"]
                   if item["key"] == "revelry_carnival")
        self.assertTrue(row["run"]["enabled"]({}))
        self.assertFalse(row["run"]["enabled"](
            {"General": {"gift_claims": False},
             "revelry_carnival": {"enabled": True}}))

    def test_revelry_runs_after_one_event_center_window(self):
        from bot.worker.priority import DATA

        row = next(item for item in DATA["Gift Claims"]
                   if item["key"] == "revelry_carnival")
        bot = mock.Mock()
        bot.done_at.return_value = None
        bot.daily_keys.return_value = []
        bot.is_daily_done.return_value = False
        with mock.patch.object(gift_claims.time, "monotonic", return_value=100.0):
            # Event Center has not run yet: Revelry remains locked.
            self.assertTrue(row["run"]["done"](bot, {}))
            setattr(bot, gift_claims.RETRY_AFTER_ATTR,
                    {gift_claims.event_center.KEY: 220.0})
            # Event Center just yielded PENDING for 120 seconds: Revelry is
            # now the next eligible Gift Claims task.
            self.assertFalse(row["run"]["done"](bot, {}))

        bot.is_daily_done.side_effect = (
            lambda key: key == gift_claims.event_center.KEY)
        self.assertFalse(row["run"]["done"](bot, {}))

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

    @staticmethod
    def _golden_tree_screens():
        screens = Path(__file__).parent / "screens"
        page = cv2.imread(str(screens / "valuable_event_golden_tree_rewards.png"))        # chưa chọn quà, đã tích Skip
        popup = cv2.imread(str(screens / "valuable_event_golden_tree_rewards_popup.png"))
        chosen = page.copy()                                    # đã chọn vàng: ô quà mục tiêu hết dấu +
        chosen[244:282, 34:76] = popup[222:260, 76:118]
        unchecked = page.copy()                                 # chưa tích Skip animation
        unchecked[562:584, 279:304] = 30
        return page, popup, chosen, unchecked

    @staticmethod
    def _golden_tree_congrats(screen):
        """`screen` có popup chữ "Congratulations!" (Images/Event/congratulations.png) giữa màn."""
        out = screen.copy()
        text = cv2.imread(str(IMAGES / "Event" / "congratulations.png"))
        out[300:300 + text.shape[0], 132:132 + text.shape[1]] = text
        return out

    @staticmethod
    def _golden_tree_bot(screen, on_tap=None):
        bot = CvBot()
        bot.current = screen
        bot.screenshot = lambda: bot.current
        bot.sleep = mock.Mock()
        bot.check = mock.Mock()
        bot.record = mock.Mock()
        bot.back = mock.Mock()
        bot.tap = mock.Mock(side_effect=on_tap)
        return bot

    def test_golden_tree_rewards_tab_found_on_real_screen(self):
        page, _popup, _chosen, _unchecked = self._golden_tree_screens()
        spec = next(s for s in valuable_event.SPECS if s.task.key == golden_tree_rewards.KEY)
        self.assertIs(golden_tree_rewards.claim, spec.flow.handler)
        pos = valuable_event._tab(self._golden_tree_bot(page), spec, page)
        self.assertIsNotNone(pos)
        self.assertAlmostEqual(185, pos[0], delta=3)

    def test_golden_tree_rewards_ticks_skip_then_selects_gold(self):
        page, popup, chosen, unchecked = self._golden_tree_screens()

        def on_tap(x, y, **_kwargs):
            if bot.current is unchecked and abs(x - 291) <= 3 and abs(y - 573) <= 3:
                bot.current = page                              # tích Skip animation
            elif bot.current is page and abs(x - 55) <= 5 and abs(y - 263) <= 5:
                bot.current = popup                             # dấu + -> popup Rewards
            elif bot.current is popup and abs(x - 198) <= 5 and abs(y - 552) <= 5:
                bot.current = chosen                            # Confirm -> về trang

        bot = self._golden_tree_bot(unchecked, on_tap)
        self.assertTrue(golden_tree_rewards.claim(bot))
        taps = [call.args for call in bot.tap.call_args_list]
        self.assertEqual(4, len(taps))                          # Skip, dấu +, vàng, Confirm
        self.assertAlmostEqual(100, taps[2][0], delta=5)        # ô vàng 1M
        self.assertAlmostEqual(242, taps[2][1], delta=5)
        bot.back.assert_not_called()

    def test_golden_tree_rewards_already_chosen_is_done_without_tapping(self):
        _page, _popup, chosen, _unchecked = self._golden_tree_screens()
        bot = self._golden_tree_bot(chosen)
        self.assertTrue(valuable_named_flow.process_exact(bot, golden_tree_rewards.FLOW))
        bot.tap.assert_not_called()

    @staticmethod
    def _golden_tree_whiten(screen, *xs):
        """Số giá dưới các nút tâm `xs` thành màu trắng (đủ xu)."""
        out = screen.copy()
        for x in xs:
            area = out[640:657, x - 12:x + 12]
            hsv = cv2.cvtColor(area, cv2.COLOR_BGR2HSV)
            red = ((hsv[..., 0] <= 10) | (hsv[..., 0] >= 170)) & (hsv[..., 1] > 120) & (hsv[..., 2] > 90)
            area[red] = 255
        return out

    def test_golden_tree_rewards_numbers_red_at_zero_coins(self):
        _page, _popup, chosen, _unchecked = self._golden_tree_screens()
        self.assertIsNone(golden_tree_rewards.affordable(chosen))
        self.assertEqual((5, 199), golden_tree_rewards.affordable(self._golden_tree_whiten(chosen, 199, 73)))
        self.assertEqual((10, 325), golden_tree_rewards.affordable(self._golden_tree_whiten(chosen, 325, 199, 73)))

    def test_golden_tree_rewards_real_screen_with_5_coins_taps_pest_control(self):
        # Screenshot_20261025-224503: 5 xu, đã chọn vàng; số 1 và 5 trắng, số 10 đỏ.
        screens = Path(__file__).parent / "screens"
        rich = cv2.imread(str(screens / "valuable_event_golden_tree_rewards_coins_5.png"))
        _page, _popup, chosen, _unchecked = self._golden_tree_screens()
        self.assertEqual((5, 199), golden_tree_rewards.affordable(rich))
        spec = next(s for s in valuable_event.SPECS if s.task.key == golden_tree_rewards.KEY)
        self.assertIsNotNone(valuable_event._tab(self._golden_tree_bot(rich), spec, rich))   # có chấm đỏ thông báo

        def on_tap(x, y, **_kwargs):
            bot.current = self._golden_tree_congrats(rich)      # bấm nút xu -> popup Congratulations

        bot = self._golden_tree_bot(rich, on_tap)
        bot.back.side_effect = lambda **_kwargs: setattr(bot, "current", chosen)   # Back đóng popup; hết xu
        self.assertTrue(golden_tree_rewards.claim(bot))
        bot.tap.assert_called_once_with(199, 620)               # không bấm Skip / dấu +, chỉ bấm Pest Control
        bot.back.assert_called_once()

    def test_golden_tree_rewards_spends_big_to_small_until_all_red(self):
        _page, _popup, chosen, _unchecked = self._golden_tree_screens()
        # Đủ xu cho 10 và 5: bấm 10 -> còn 5 -> bấm 5 -> hết (cả ba đỏ).
        rich = self._golden_tree_whiten(chosen, 325, 199, 73)
        some = self._golden_tree_whiten(chosen, 199, 73)
        left = self._golden_tree_whiten(chosen, 73)
        after = {325: some, 199: left, 73: chosen}
        closed = []

        def on_tap(x, y, **_kwargs):
            self.assertEqual(620, y)
            closed.append(after[x])
            bot.current = self._golden_tree_congrats(after[x])  # mỗi lần bấm ra popup Congratulations

        bot = self._golden_tree_bot(rich, on_tap)
        bot.back.side_effect = lambda **_kwargs: setattr(bot, "current", closed[-1])
        self.assertTrue(golden_tree_rewards.spend_coins(bot))
        self.assertEqual([325, 199, 73], [call.args[0] for call in bot.tap.call_args_list])
        self.assertEqual(3, bot.back.call_count)                # Back đóng popup sau mỗi lần bấm

    def test_golden_tree_rewards_no_popup_goes_back_to_search_without_back(self):
        _page, _popup, chosen, _unchecked = self._golden_tree_screens()
        rich = self._golden_tree_whiten(chosen, 199)

        def on_tap(x, y, **_kwargs):
            bot.current = chosen                                # không ra popup, số đã đỏ

        bot = self._golden_tree_bot(rich, on_tap)
        self.assertTrue(golden_tree_rewards.spend_coins(bot))
        bot.tap.assert_called_once_with(199, 620)
        self.assertEqual(golden_tree_rewards.WAITS, bot.sleep.call_count)   # chờ popup 1s x 5 rồi quay lại bước tìm
        bot.back.assert_not_called()

    def test_golden_tree_rewards_one_coin_waits_three_times_for_popup(self):
        _page, _popup, chosen, _unchecked = self._golden_tree_screens()
        rich = self._golden_tree_whiten(chosen, 73)

        def on_tap(x, y, **_kwargs):
            bot.current = chosen                                # không ra popup, số đã đỏ

        bot = self._golden_tree_bot(rich, on_tap)
        self.assertTrue(golden_tree_rewards.spend_coins(bot))
        bot.tap.assert_called_once_with(73, 620)
        self.assertEqual(3, bot.sleep.call_count)               # nút 1 xu: chờ popup 1s x 3 rồi quay lại bước tìm
        bot.back.assert_not_called()

    def test_golden_tree_rewards_ticks_skip_on_real_unchecked_screen(self):
        # Ảnh máy 21913: ô Skip animation chưa tích.
        unchecked = cv2.imread(str(Path(__file__).parent / "screens" /
                                   "valuable_event_golden_tree_rewards_skip_unchecked.png"))
        page = self._golden_tree_screens()[0]
        bot = self._golden_tree_bot(unchecked, lambda x, y, **_kwargs: setattr(bot, "current", page))
        self.assertTrue(wheel_of_dragon_war.ensure_skip_animation(
            bot, golden_tree_rewards.SKIP_TAP, golden_tree_rewards.SKIP_BOX, "Golden Tree Rewards"))
        bot.tap.assert_called_once_with(291, 573, delay=1.0)

    def test_golden_tree_rewards_restarts_when_popup_never_opens(self):
        page, _popup, _chosen, _unchecked = self._golden_tree_screens()
        bot = self._golden_tree_bot(page)
        self.assertFalse(golden_tree_rewards.select_reward(bot))
        # Mỗi lượt bấm dấu + rồi chờ 5 lần; không thấy popup thì làm lại từ đầu, tối đa 3 lượt.
        self.assertEqual(golden_tree_rewards.ATTEMPTS, bot.tap.call_count)
        self.assertEqual(golden_tree_rewards.ATTEMPTS * golden_tree_rewards.WAITS, bot.sleep.call_count)

    def test_golden_tree_rewards_stays_pending_off_its_page(self):
        screen = cv2.imread(str(Path(__file__).parent / "screens" /
                                "valuable_event_tab_limited_offer_selected.png"))
        bot = self._golden_tree_bot(screen)
        spec = next(s for s in valuable_event.SPECS if s.task.key == golden_tree_rewards.KEY)
        self.assertIsNone(valuable_event._tab(bot, spec, screen))
        self.assertFalse(valuable_named_flow.process_exact(bot, golden_tree_rewards.FLOW))

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

    def test_valuable_confirms_both_edges_after_two_unchanged_swipes(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.screenshot.return_value = screen
        spec = valuable_event.SPECS[0]

        def find_named(_bot, name, *_args, **_kwargs):
            return (198, 25) if name == valuable_event.PAGE else None

        with (mock.patch.object(valuable_event, "SPECS", (spec,)),
              mock.patch.object(valuable_event, "find", side_effect=find_named),
              mock.patch.object(valuable_event, "carousel_moved",
                                return_value=False)):
            results, clean = valuable_event.run_opened(bot, {spec.task.key})

        self.assertTrue(clean)
        self.assertEqual("not_present", results[spec.task.key])
        swipes = bot.swipe_percent.call_args_list
        self.assertEqual(4, len(swipes))
        self.assertTrue(all(call.args[:4] == (20, 14, 85, 14)
                            for call in swipes[:2]))
        self.assertTrue(all(call.args[:4] == (85, 14, 55, 14)
                            for call in swipes[2:]))

    def test_super_value_return_has_one_standard_spec_per_child_module(self):
        expected = {
            "gift_empire_depot", "gift_lucky_raffle", "gift_city_growth_plan",
            "gift_login_gifts", "gift_refining_weekly_card",
            "gift_hall_of_historic_generals", "gift_soul_of_spiritual_beast",
        }
        self.assertEqual(expected, super_value_return.KEYS)
        self.assertTrue(all(spec.tab.split("/", 1)[0] for spec in super_value_return.SPECS))
        self.assertTrue(all(hasattr(spec, "flow") for spec in super_value_return.SPECS))

    def test_super_value_return_is_an_independent_seven_task_zone(self):
        self.assertEqual("gift_super_value_return", super_value_zone.KEY)
        self.assertEqual(
            ["gift_login_gifts", "gift_empire_depot",
             "gift_hall_of_historic_generals", "gift_soul_of_spiritual_beast",
             "gift_lucky_raffle", "gift_city_growth_plan",
             "gift_refining_weekly_card"],
            [task.key for task in super_value_zone.TASKS])
        self.assertTrue(all(task.key not in {
            item.key for item in valuable_event_zone.TASKS
        } for task in super_value_zone.TASKS))

    def test_hall_claim_and_claimed_require_opposite_colour_bands(self):
        claim = cv2.imread(str(
            IMAGES / "GiftClaims" / "SuperValueReturn" / "HallOfHistoricGenerals" /
            "button_claim.png"))
        claimed = cv2.imread(str(
            IMAGES / "GiftClaims" / "SuperValueReturn" / "HallOfHistoricGenerals" /
            "status_claimed.png"))

        claim_center = (claim.shape[1] // 2, claim.shape[0] // 2)
        claimed_center = (claimed.shape[1] // 2, claimed.shape[0] // 2)
        self.assertTrue(hall_of_historic_generals._is_green_claim(
            claim, claim_center))
        self.assertFalse(hall_of_historic_generals._is_gray_claimed(
            claim, claim_center))
        self.assertFalse(hall_of_historic_generals._is_green_claim(
            claimed, claimed_center))
        self.assertTrue(hall_of_historic_generals._is_gray_claimed(
            claimed, claimed_center))

    def test_hall_retries_a_stalled_claim_only_after_other_claims(self):
        bot = mock.Mock()
        first = (120, 220)
        second = (260, 220)
        # The first Claim stays green after its first tap.  The second must be
        # handled before retrying the first; the viewport is not abandoned.
        visible = ([first, second], [first, second], [first, second],
                   [first], [first], [], [])
        with (mock.patch.object(hall_of_historic_generals, "_green_claims",
                                side_effect=visible),
              mock.patch.object(hall_of_historic_generals,
                                "_gray_claimed", return_value=[]),
              mock.patch.object(hall_of_historic_generals,
                                "_pending_controls", return_value=False),
              mock.patch.object(hall_of_historic_generals,
                                "close_congratulations", return_value=False)):
            claimed, stuck, _saw_claimed, _pending = (
                hall_of_historic_generals._claim_current_view(bot))

        self.assertTrue(claimed)
        self.assertFalse(stuck)
        self.assertEqual([mock.call(*first,
                                    delay=hall_of_historic_generals.STEP_DELAY),
                          mock.call(*second,
                                    delay=hall_of_historic_generals.STEP_DELAY),
                          mock.call(*first,
                                    delay=hall_of_historic_generals.STEP_DELAY)],
                         bot.tap.call_args_list)

    def test_hall_full_claimed_scan_is_done_without_new_claim(self):
        bot = mock.Mock()
        views = (
            (False, False, True, False),
            (False, False, True, False),
            (False, False, True, False),
        )
        with (mock.patch.object(hall_of_historic_generals, "_swipe_to_top"),
              mock.patch.object(hall_of_historic_generals,
                                "_claim_current_view", side_effect=views),
              mock.patch.object(hall_of_historic_generals, "_swipe",
                                side_effect=(0, 0))):
            outcome = hall_of_historic_generals._scan_rewards(bot)

        self.assertEqual(hall_of_historic_generals.DONE, outcome)

    def test_hall_done_1_requires_a_second_full_pass_without_claim(self):
        bot = mock.Mock()
        views = (
            (True, False, True, False),
            (False, False, True, False),
            (False, False, True, False),
            (False, False, True, False),
            (False, False, True, False),
            (False, False, True, False),
        )
        with (mock.patch.object(hall_of_historic_generals,
                                "_swipe_to_top") as to_top,
              mock.patch.object(hall_of_historic_generals,
                                "_claim_current_view", side_effect=views),
              mock.patch.object(hall_of_historic_generals, "_swipe",
                                side_effect=(0, 0, 0, 0))):
            outcome = hall_of_historic_generals._scan_rewards(bot)

        self.assertEqual(hall_of_historic_generals.DONE_1, outcome)
        self.assertEqual(2, to_top.call_count)

    def test_hall_done_1_is_not_written_as_db_done(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.screenshot.return_value = screen
        spec = next(spec for spec in super_value_return.SPECS
                    if spec.task.key == hall_of_historic_generals.KEY)

        def find_named(_bot, name, *_args, **_kwargs):
            if name == super_value_return.PAGE:
                return (198, 25)
            if name == spec.tab:
                return (100, 70)
            return None

        with (mock.patch.object(super_value_return, "SPECS", (spec,)),
              mock.patch.object(super_value_return, "find",
                                side_effect=find_named),
              mock.patch.object(super_value_return, "carousel_moved",
                                return_value=False),
              mock.patch.object(
                  super_value_return.hall_of_historic_generals,
                  "claim_opened",
                  return_value=hall_of_historic_generals.DONE_1),
              mock.patch.object(super_value_return, "mark_task_done") as mark):
            results, clean = super_value_return.run_opened(
                bot, {hall_of_historic_generals.KEY})

        self.assertTrue(clean)
        self.assertEqual(hall_of_historic_generals.DONE_1,
                         results[hall_of_historic_generals.KEY])
        mark.assert_not_called()

    def test_hall_claim_cycle_backs_then_claims_main_chests(self):
        bot = mock.Mock()
        with (mock.patch.object(hall_of_historic_generals, "_open_scores",
                                return_value=True),
              mock.patch.object(hall_of_historic_generals, "_scan_rewards",
                                return_value=hall_of_historic_generals.DONE_1),
              mock.patch.object(hall_of_historic_generals, "_main_open",
                                return_value=True),
              mock.patch.object(hall_of_historic_generals,
                                "_claim_main_chests", return_value=True) as chests):
            outcome = hall_of_historic_generals.claim_opened(bot)

        self.assertEqual(hall_of_historic_generals.DONE_1, outcome)
        bot.back.assert_called_once_with(
            delay=hall_of_historic_generals.STEP_DELAY)
        chests.assert_called_once_with(bot)

    def test_hall_without_new_claim_does_not_check_main_chests(self):
        bot = mock.Mock()
        with (mock.patch.object(hall_of_historic_generals, "_open_scores",
                                return_value=True),
              mock.patch.object(hall_of_historic_generals, "_scan_rewards",
                                return_value=hall_of_historic_generals.DONE),
              mock.patch.object(hall_of_historic_generals,
                                "_claim_main_chests") as chests):
            outcome = hall_of_historic_generals.claim_opened(bot)

        self.assertEqual(hall_of_historic_generals.DONE, outcome)
        chests.assert_not_called()

    def test_hall_missing_congratulations_accepts_chest_absence(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.screenshot.return_value = screen
        with (mock.patch.object(hall_of_historic_generals, "_main_open",
                                return_value=True),
              mock.patch.object(hall_of_historic_generals,
                                "find_reward_chest",
                                side_effect=[(50, 243), None, None]),
              mock.patch.object(hall_of_historic_generals, "find",
                                return_value=None)):
            complete = hall_of_historic_generals._claim_main_chests(bot)

        self.assertTrue(complete)
        bot.tap.assert_called_once_with(
            50, 243, delay=hall_of_historic_generals.STEP_DELAY)

    def test_hall_done_1_is_deferred_until_next_claim_gifts_run(self):
        bot = mock.Mock()
        deferred = set()
        result = {hall_of_historic_generals.KEY:
                  hall_of_historic_generals.DONE_1}

        with (mock.patch.object(super_value_zone, "identify",
                                return_value=GiftScreen.SUPER_VALUE_RETURN),
              mock.patch.object(super_value_zone, "run_opened",
                                return_value=(result, True)) as opened):
            inspected = super_value_zone._sweep(
                bot, [hall_of_historic_generals.KEY], deferred)
            second = super_value_zone._sweep(
                bot, [hall_of_historic_generals.KEY], deferred)

        self.assertEqual(set(), inspected)
        self.assertEqual(set(), second)
        self.assertEqual({hall_of_historic_generals.KEY}, deferred)
        opened.assert_called_once()

    def test_soul_claim_and_claimed_require_opposite_colour_bands(self):
        claim = cv2.imread(str(
            IMAGES / "GiftClaims" / "SuperValueReturn" /
            "SoulOfSpiritualBeast" / "button_claim.png"))
        claimed = cv2.imread(str(
            IMAGES / "GiftClaims" / "SuperValueReturn" /
            "SoulOfSpiritualBeast" / "status_claimed.png"))

        claim_screen = np.zeros((704, 396, 3), dtype=np.uint8)
        claimed_screen = np.zeros((704, 396, 3), dtype=np.uint8)
        claim_screen[200:200 + claim.shape[0],
                     250:250 + claim.shape[1]] = claim
        claimed_screen[200:200 + claimed.shape[0],
                       250:250 + claimed.shape[1]] = claimed
        claim_center = (250 + claim.shape[1] // 2,
                        200 + claim.shape[0] // 2)
        claimed_center = (250 + claimed.shape[1] // 2,
                          200 + claimed.shape[0] // 2)
        self.assertTrue(soul_of_spiritual_beast._is_green_claim(
            claim_screen, claim_center))
        self.assertFalse(soul_of_spiritual_beast._is_gray_claimed(
            claim_screen, claim_center))
        self.assertFalse(soul_of_spiritual_beast._is_green_claim(
            claimed_screen, claimed_center))
        self.assertTrue(soul_of_spiritual_beast._is_gray_claimed(
            claimed_screen, claimed_center))

    def test_soul_all_claimed_in_both_tabs_is_done(self):
        bot = mock.Mock()
        with (mock.patch.object(soul_of_spiritual_beast, "_main_open",
                                return_value=True),
              mock.patch.object(soul_of_spiritual_beast,
                                "_claim_main_chests", return_value=True),
              mock.patch.object(soul_of_spiritual_beast, "_open_quests",
                                return_value=True),
              mock.patch.object(soul_of_spiritual_beast,
                                "_select_quest_tab", return_value=True),
              mock.patch.object(soul_of_spiritual_beast, "_scan_quest_tab",
                                side_effect=[(False, False, True, False),
                                             (False, False, True, False)])):
            outcome = soul_of_spiritual_beast.claim_opened(bot)

        self.assertEqual(soul_of_spiritual_beast.DONE, outcome)
        bot.back.assert_called_once()

    def test_soul_failed_initial_chest_still_opens_challenge_quest(self):
        bot = mock.Mock()
        with (mock.patch.object(soul_of_spiritual_beast, "_main_open",
                                return_value=True),
              mock.patch.object(soul_of_spiritual_beast,
                                "_claim_main_chests", return_value=False),
              mock.patch.object(soul_of_spiritual_beast,
                                "_open_quests", return_value=True) as quests,
              mock.patch.object(soul_of_spiritual_beast,
                                "_select_quest_tab", return_value=True),
              mock.patch.object(soul_of_spiritual_beast, "_scan_quest_tab",
                                side_effect=[(False, False, True, False),
                                             (False, False, True, False)])):
            outcome = soul_of_spiritual_beast.claim_opened(bot)

        self.assertEqual(soul_of_spiritual_beast.DONE, outcome)
        quests.assert_called_once_with(bot)

    def test_soul_claims_both_tabs_then_checks_main_chests_and_defers(self):
        bot = mock.Mock()
        with (mock.patch.object(soul_of_spiritual_beast, "_main_open",
                                return_value=True),
              mock.patch.object(soul_of_spiritual_beast,
                                "_claim_main_chests",
                                side_effect=[True, True]) as chests,
              mock.patch.object(soul_of_spiritual_beast, "_open_quests",
                                return_value=True),
              mock.patch.object(soul_of_spiritual_beast,
                                "_select_quest_tab", return_value=True),
              mock.patch.object(soul_of_spiritual_beast, "_scan_quest_tab",
                                side_effect=[(True, False, True, False),
                                             (False, False, True, False)])):
            outcome = soul_of_spiritual_beast.claim_opened(bot)

        self.assertEqual(soul_of_spiritual_beast.DONE_1, outcome)
        self.assertEqual(2, chests.call_count)
        bot.sleep.assert_any_call(1)
        bot.back.assert_called_once()

    def test_soul_without_claim_skips_post_claim_chest_sequence(self):
        bot = mock.Mock()
        with (mock.patch.object(soul_of_spiritual_beast, "_main_open",
                                return_value=True),
              mock.patch.object(soul_of_spiritual_beast,
                                "_claim_main_chests", return_value=True) as chests,
              mock.patch.object(soul_of_spiritual_beast, "_open_quests",
                                return_value=True),
              mock.patch.object(soul_of_spiritual_beast,
                                "_select_quest_tab", return_value=True),
              mock.patch.object(soul_of_spiritual_beast, "_scan_quest_tab",
                                side_effect=[(False, False, True, True),
                                             (False, False, True, False)])):
            outcome = soul_of_spiritual_beast.claim_opened(bot)

        self.assertEqual(soul_of_spiritual_beast.DONE_1, outcome)
        chests.assert_called_once()

    def test_soul_does_not_open_main_chest_until_both_tabs_are_clear(self):
        bot = mock.Mock()
        with (mock.patch.object(soul_of_spiritual_beast, "_main_open",
                                return_value=True),
              mock.patch.object(soul_of_spiritual_beast,
                                "_claim_main_chests", return_value=True) as chests,
              mock.patch.object(soul_of_spiritual_beast, "_open_quests",
                                return_value=True),
              mock.patch.object(soul_of_spiritual_beast,
                                "_select_quest_tab", return_value=True),
              mock.patch.object(soul_of_spiritual_beast, "_scan_quest_tab",
                                side_effect=[(True, True, True, False),
                                             (True, False, True, False)])):
            outcome = soul_of_spiritual_beast.claim_opened(bot)

        self.assertEqual(soul_of_spiritual_beast.PENDING, outcome)
        # The first call checks the chest before opening Quests. There must be
        # no second, post-Claim pass while either tab still has a Claim.
        chests.assert_called_once()

    def test_soul_missing_congratulations_accepts_confirmed_chest_absence(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.screenshot.return_value = screen
        with (mock.patch.object(soul_of_spiritual_beast, "_main_open",
                                return_value=True),
              mock.patch.object(soul_of_spiritual_beast,
                                "_find_main_chest",
                                side_effect=[(40, 198), None, None]),
              mock.patch.object(soul_of_spiritual_beast, "find",
                                return_value=None)):
            complete = soul_of_spiritual_beast._claim_main_chests(bot)

        self.assertTrue(complete)
        bot.tap.assert_called_once_with(40, 198,
                                        delay=soul_of_spiritual_beast.STEP_DELAY)

    def test_soul_main_chest_uses_its_calibrated_template_and_threshold(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        with mock.patch.object(soul_of_spiritual_beast, "find",
                               return_value=(31, 225)) as find_chest:
            chest = soul_of_spiritual_beast._find_main_chest(bot, screen)

        self.assertEqual((31, 225), chest)
        find_chest.assert_called_once_with(
            bot, soul_of_spiritual_beast.MAIN_CHEST, screen,
            threshold=soul_of_spiritual_beast.MAIN_CHEST_THRESHOLD,
            region=soul_of_spiritual_beast.MAIN_CHEST_REGION,
        )

    def test_soul_done_1_is_not_written_as_db_done(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.screenshot.return_value = screen
        spec = next(spec for spec in super_value_return.SPECS
                    if spec.task.key == soul_of_spiritual_beast.KEY)

        def find_named(_bot, name, *_args, **_kwargs):
            if name == super_value_return.PAGE:
                return (198, 25)
            if name == spec.tab:
                return (100, 70)
            return None

        with (mock.patch.object(super_value_return, "SPECS", (spec,)),
              mock.patch.object(super_value_return, "find",
                                side_effect=find_named),
              mock.patch.object(super_value_return, "carousel_moved",
                                return_value=False),
              mock.patch.object(
                  super_value_return.soul_of_spiritual_beast,
                  "claim_opened", return_value=soul_of_spiritual_beast.DONE_1),
              mock.patch.object(super_value_return, "mark_task_done") as mark):
            results, clean = super_value_return.run_opened(
                bot, {soul_of_spiritual_beast.KEY})

        self.assertTrue(clean)
        self.assertEqual(soul_of_spiritual_beast.DONE_1,
                         results[soul_of_spiritual_beast.KEY])
        mark.assert_not_called()

    def test_super_value_search_pass_order_visible_then_long_swipe_then_short_scan(self):
        bot = mock.Mock()
        calls = []
        with (mock.patch.object(super_value_zone, "open_super_value_return",
                                side_effect=lambda b: calls.append("open") or True),
              mock.patch.object(super_value_zone, "capture_title",
                                side_effect=lambda b: calls.append("title")),
              mock.patch.object(super_value_zone, "do_visible",
                                side_effect=lambda *a: calls.append("visible")),
              mock.patch.object(super_value_zone, "swipe_to_left_edge",
                                side_effect=lambda *a: calls.append("long") or True),
              mock.patch.object(super_value_zone, "scan_to_right_edge",
                                side_effect=lambda *a: calls.append("short") or True)):
            self.assertTrue(super_value_zone.search_pass(bot, {"gift_lucky_raffle"}, set()))
        self.assertEqual(["open", "title", "visible", "long", "visible", "short"], calls)

    def test_super_value_zone_uses_user_fallback_when_no_image_matches(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(super_value_zone, "on_main", return_value=True),
              mock.patch.object(super_value_zone, "to_city", return_value=False),
              mock.patch.object(super_value_zone, "find_super_value_return",
                                return_value=None),
              mock.patch.object(super_value_zone, "identify",
                                return_value=GiftScreen.SUPER_VALUE_RETURN)):
            self.assertTrue(super_value_zone.open_super_value_return(bot))

        bot.tap.assert_called_once_with(35, 560)

    def test_super_value_first_swipe_is_500_percent(self):
        self.assertEqual((5, 12, 500, 12), super_value_zone.FIRST_SWIPE)

    def test_super_value_three_passes_then_marks_every_event_done(self):
        bot, done = self._daily_bot()
        with (mock.patch.object(super_value_zone, "search_pass", return_value=True) as search,
              mock.patch.object(super_value_zone, "return_home", return_value=True)):
            self.assertTrue(super_value_zone.run(bot))
        self.assertEqual(3, search.call_count)
        for number in (1, 2, 3):
            self.assertIn(f"gift_super_value_return_pass_{number}", done)
        for task in super_value_zone.TASKS:
            self.assertIn(task.key, done)
        self.assertIn(super_value_zone.KEY, done)

    def test_super_value_new_event_resets_pass_count(self):
        bot, done = self._daily_bot()
        with (mock.patch.object(super_value_zone, "search_pass",
                                side_effect=self._passes_seeing((), ("A",), (), ())) as search,
              mock.patch.object(super_value_zone, "return_home", return_value=True)):
            self.assertTrue(super_value_zone.run(bot))
        self.assertEqual(4, search.call_count)

    def test_super_value_open_fail_keeps_pass(self):
        bot, done = self._daily_bot()
        with (mock.patch.object(super_value_zone, "search_pass", return_value=False),
              mock.patch.object(super_value_zone, "return_home", return_value=True)):
            self.assertFalse(super_value_zone.run(bot))
        self.assertNotIn("gift_super_value_return_pass_1", done)
        self.assertNotIn(super_value_zone.KEY, done)

    def test_super_value_do_visible_runs_leftmost_tab_then_marks_done(self):
        bot, done = self._daily_bot()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        lucky = next(s for s in super_value_return.SPECS if s.task.key == "gift_lucky_raffle")
        empire = next(s for s in super_value_return.SPECS if s.task.key == "gift_empire_depot")
        positions = {lucky.tab: (250, 80), empire.tab: (120, 80)}
        order = []
        with (mock.patch.object(super_value_zone, "close_popup", return_value=False),
              mock.patch.object(super_value_zone, "find_tab",
                                side_effect=lambda _b, spec, _s: positions.get(spec.tab)),
              mock.patch.object(super_value_zone, "open_tab", return_value=True),
              mock.patch.object(super_value_zone, "run_event",
                                side_effect=lambda _b, spec: order.append(spec.task.key) or True)):
            pending = {lucky.task.key, empire.task.key}
            super_value_zone.do_visible(bot, pending, set())
        self.assertEqual(["gift_empire_depot", "gift_lucky_raffle"], order)   # tab bên trái trước
        self.assertEqual(set(), pending)
        self.assertIn("gift_empire_depot", done)
        self.assertIn("gift_lucky_raffle", done)

    def test_super_value_run_event_uses_own_claim_for_login_gifts_and_refining(self):
        bot = mock.Mock()
        specs = {s.task.key: s for s in super_value_return.SPECS}
        with (mock.patch.object(super_value_zone.login_gifts, "claim_opened", return_value=True) as login,
              mock.patch.object(super_value_zone.refining_weekly_card, "claim_opened", return_value=False) as refining,
              mock.patch.object(super_value_zone, "process_exact", return_value=True) as exact):
            self.assertTrue(super_value_zone.run_event(bot, specs["gift_login_gifts"]))
            self.assertFalse(super_value_zone.run_event(bot, specs["gift_refining_weekly_card"]))
            self.assertTrue(super_value_zone.run_event(bot, specs["gift_lucky_raffle"]))
        login.assert_called_once_with(bot)
        refining.assert_called_once_with(bot)
        exact.assert_called_once_with(bot, specs["gift_lucky_raffle"].flow)

    def test_super_value_confirms_both_edges_before_full_scan(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.screenshot.return_value = screen
        spec = super_value_return.SPECS[0]

        def find_named(_bot, name, *_args, **_kwargs):
            return (198, 25) if name == super_value_return.PAGE else None

        with (mock.patch.object(super_value_return, "SPECS", (spec,)),
              mock.patch.object(super_value_return, "find",
                                side_effect=find_named),
              mock.patch.object(super_value_return, "carousel_moved",
                                return_value=False)):
            results, clean = super_value_return.run_opened(
                bot, {spec.task.key})

        self.assertTrue(clean)
        self.assertEqual("not_present", results[spec.task.key])
        swipes = bot.swipe_percent.call_args_list
        self.assertEqual(4, len(swipes))
        self.assertTrue(all(call.args[:4] == (20, 14, 85, 14)
                            for call in swipes[:2]))
        self.assertTrue(all(call.args[:4] == (85, 14, 55, 14)
                            for call in swipes[2:]))

    def test_city_growth_done_requires_level_15_and_claimed_tick_crop(self):
        marker = cv2.imread(str(IMAGES / "GiftClaims" /
                                "SuperValueReturn" / "CityGrowthPlan" /
                                "level_15_claimed.png"))
        self.assertIsNotNone(marker)
        self.assertGreater(marker.shape[1], 100)
        city = next(spec for spec in super_value_return.SPECS
                    if spec.task.key == "gift_city_growth_plan")
        self.assertEqual(("SuperValueReturn/CityGrowthPlan/level_15_claimed",), city.flow.done)

    def test_refining_weekly_card_uses_custom_done_state(self):
        self.assertEqual((), refining_weekly_card.FLOW.done)
        self.assertEqual((refining_weekly_card.CLAIM,),
                         refining_weekly_card.FLOW.claims)

    def test_refining_weekly_card_colour_crop_uses_gift_claims_pack_path(self):
        bot = mock.Mock()
        bot._template.return_value = np.zeros((26, 62, 3), dtype=np.uint8)
        screen = np.zeros((704, 396, 3), dtype=np.uint8)

        crop = refining_weekly_card._button_crop(
            bot, screen, (200, 500), refining_weekly_card.CLAIM)

        bot._template.assert_called_once_with(
            "GiftClaims/SuperValueReturn/RefiningWeeklyCard/button_claim.png")
        self.assertEqual((26, 62, 3), crop.shape)

    def test_refining_weekly_card_swipes_only_inside_green_reward_frame(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.screenshot.return_value = screen

        with (mock.patch.object(refining_weekly_card, "_green_claims",
                                return_value=[]),
              mock.patch.object(refining_weekly_card, "_yellow_continues",
                                return_value=[]),
              mock.patch.object(refining_weekly_card,
                                "EDGE_CONFIRMATIONS", 1)):
            self.assertEqual(refining_weekly_card.DONE_1,
                             refining_weekly_card.claim_opened(bot))

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
                                side_effect=[
                                    (True, False, False),
                                    (False, False, True),
                                ]) as scan):
            self.assertEqual(refining_weekly_card.DONE,
                             refining_weekly_card.claim_opened(bot))

        self.assertEqual(2, scan.call_count)

    def test_refining_weekly_card_done_requires_only_yellow_continue(self):
        bot = mock.Mock()
        with mock.patch.object(
                refining_weekly_card, "_scan_full_list",
                return_value=(False, False, True)):
            self.assertEqual(refining_weekly_card.DONE,
                             refining_weekly_card.claim_opened(bot))

        with mock.patch.object(
                refining_weekly_card, "_scan_full_list",
                return_value=(False, False, False)):
            self.assertEqual(refining_weekly_card.DONE_1,
                             refining_weekly_card.claim_opened(bot))

    def test_refining_weekly_card_templates_have_green_and_yellow_bands(self):
        claim = cv2.imread(str(IMAGES / "GiftClaims" / "SuperValueReturn" /
                               "RefiningWeeklyCard" / "button_claim.png"))
        continue_button = cv2.imread(str(
            IMAGES / "GiftClaims" / "SuperValueReturn" /
            "RefiningWeeklyCard" / "button_continue.png"))
        self.assertIsNotNone(claim)
        self.assertIsNotNone(continue_button)
        claim_green, claim_yellow = refining_weekly_card._colour_ratios(claim)
        continue_green, continue_yellow = refining_weekly_card._colour_ratios(
            continue_button)
        self.assertGreater(claim_green, refining_weekly_card.GREEN_MIN_RATIO)
        self.assertLess(claim_yellow, refining_weekly_card.YELLOW_MIN_RATIO)
        self.assertLess(continue_green, refining_weekly_card.GREEN_MIN_RATIO)
        self.assertGreater(continue_yellow,
                           refining_weekly_card.YELLOW_MIN_RATIO)

    def test_refining_done_1_is_not_written_as_db_done(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.screenshot.return_value = screen
        spec = next(spec for spec in super_value_return.SPECS
                    if spec.task.key == refining_weekly_card.KEY)

        def find_named(_bot, name, *_args, **_kwargs):
            if name == super_value_return.PAGE:
                return (198, 25)
            if name == spec.tab:
                return (100, 70)
            return None

        with (mock.patch.object(super_value_return, "SPECS", (spec,)),
              mock.patch.object(super_value_return, "find",
                                side_effect=find_named),
              mock.patch.object(super_value_return, "carousel_moved",
                                return_value=False),
              mock.patch.object(
                  super_value_return.refining_weekly_card,
                  "claim_opened", return_value=refining_weekly_card.DONE_1),
              mock.patch.object(super_value_return, "mark_task_done") as mark):
            results, clean = super_value_return.run_opened(
                bot, {refining_weekly_card.KEY})

        self.assertTrue(clean)
        self.assertEqual(refining_weekly_card.DONE_1,
                         results[refining_weekly_card.KEY])
        mark.assert_not_called()

    def test_refining_done_1_is_deferred_until_next_120s_run(self):
        bot = mock.Mock()
        deferred = set()
        result = {refining_weekly_card.KEY: refining_weekly_card.DONE_1}

        with (mock.patch.object(super_value_zone, "identify",
                                return_value=GiftScreen.SUPER_VALUE_RETURN),
              mock.patch.object(super_value_zone, "run_opened",
                                return_value=(result, True)) as opened):
            inspected = super_value_zone._sweep(
                bot, [refining_weekly_card.KEY], deferred)
            second = super_value_zone._sweep(
                bot, [refining_weekly_card.KEY], deferred)

        self.assertEqual(set(), inspected)
        self.assertEqual(set(), second)
        self.assertEqual({refining_weekly_card.KEY}, deferred)
        opened.assert_called_once()

    def test_login_gifts_absent_chest_is_done_without_fallback_tap(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)

        def find_page(_bot, name, *_args, **_kwargs):
            return (40, 140) if name == login_gifts.PAGE else None

        with (mock.patch.object(login_gifts, "find", side_effect=find_page),
              mock.patch.object(login_gifts, "find_reward_chest",
                                return_value=None),
              mock.patch.object(login_gifts, "_tap_reward",
                                return_value=False) as tap):
            self.assertTrue(login_gifts.claim_opened(bot))

        tap.assert_not_called()
        bot.tap.assert_not_called()


    def test_login_gifts_real_screen_without_reward_button_is_done(self):
        # Màn Login Gifts kiểu danh sách ngày (không có hộp quà phát sáng): không bấm gì, DONE.
        bot = mock.Mock()
        bot.screenshot.return_value = cv2.imread(
            str(Path(__file__).parent / "screens" / "super_value_return_login_gifts_no_button.png"))
        bot.find.side_effect = self.bot.find
        bot._template.side_effect = self.bot._template
        self.assertTrue(login_gifts.claim_opened(bot))
        bot.tap.assert_not_called()

    def test_login_gifts_uses_captured_reward_button(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.screenshot.return_value = screen

        def find_page(_bot, name, *_args, **_kwargs):
            if name == login_gifts.PAGE:
                return (40, 140)
            return None

        with (mock.patch.object(login_gifts, "find", side_effect=find_page),
              mock.patch.object(login_gifts, "find_reward_chest",
                                return_value=(51, 192)) as find_chest,
              mock.patch.object(login_gifts, "_tap_reward",
                                return_value=True) as tap):
            self.assertTrue(login_gifts.claim_opened(bot))

        find_chest.assert_called_once_with(
            bot, screen, region=login_gifts.REWARD_REGION,
            threshold=login_gifts.REWARD_THRESHOLD)
        tap.assert_called_once_with(bot, (51, 192))

    def test_reward_chest_finder_supports_region_or_full_screen(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        region = (2, 22, 18, 34)
        with mock.patch.object(common, "find",
                               side_effect=[(51, 192), (52, 193)]) as finder:
            regional = common.find_reward_chest(bot, screen, region=region)
            full = common.find_reward_chest(bot, screen)

        self.assertEqual((51, 192), regional)
        self.assertEqual((52, 193), full)
        self.assertEqual(
            mock.call(bot, common.REWARD_CHEST_TEMPLATE, screen=screen,
                      threshold=common.REWARD_CHEST_THRESHOLD, region=region),
            finder.call_args_list[0])
        self.assertEqual(
            mock.call(bot, common.REWARD_CHEST_TEMPLATE, screen=screen,
                      threshold=common.REWARD_CHEST_THRESHOLD, region=None),
            finder.call_args_list[1])

    def test_shared_reward_chest_uses_measured_full_crop_and_threshold(self):
        chest = cv2.imread(str(IMAGES / "GiftClaims" / "Common" /
                              "button_reward_chest.png"))
        self.assertEqual((47, 47), chest.shape[:2])
        self.assertEqual("Common/button_reward_chest",
                         login_gifts.REWARD_BUTTON)
        self.assertEqual(0.78, login_gifts.REWARD_THRESHOLD)
        self.assertEqual((2, 22, 18, 34), login_gifts.REWARD_REGION)

        flows = {spec.task.key: spec.flow for spec in valuable_event.SPECS}
        self.assertEqual(("Common/button_reward_chest",),
                         flows["gift_super_value_weekly_card"].navigation)
        self.assertEqual(0.80,
                         flows["gift_super_value_weekly_card"].navigation_threshold)

    def test_active_monthly_card_uses_supplied_green_scroll_frame(self):
        flow = active_monthly_card.FLOW
        claim = cv2.imread(str(
            IMAGES / "GiftClaims" / "ValuableEvent" / "ActiveMonthlyCard" / "button_claim.png"))

        self.assertEqual((26, 62), claim.shape[:2])
        self.assertEqual(("ValuableEvent/ActiveMonthlyCard/button_claim",), flow.claims)
        self.assertEqual(
            ("ValuableEvent/ActiveMonthlyCard/button_reward_chest_median",),
            flow.navigation)
        self.assertEqual((2, 17, 27, 41), flow.navigation_region)
        self.assertEqual(0.72, flow.navigation_threshold)
        self.assertIsNone(flow.fallback_tap)
        self.assertEqual((4, 59, 96, 99), flow.claim_region)
        self.assertEqual((), flow.done)
        self.assertTrue(flow.scroll_claims)
        self.assertTrue(flow.absence_done)
        self.assertEqual((50, 92), flow.scroll_start)
        self.assertEqual((50, 65), flow.scroll_end)
        self.assertEqual((4, 59, 96, 99), flow.scroll_region)
        self.assertTrue(flow.confirm_scroll_edges)
        self.assertEqual(24, flow.scroll_same_distance)
        self.assertEqual(2, flow.scroll_edge_confirmations)

    def test_active_monthly_card_without_chest_scans_to_bottom_and_claims(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        flow = active_monthly_card.FLOW
        downward_swipes = [0]

        def swipe(_bot, _flow, *, toward_start):
            if not toward_start:
                downward_swipes[0] += 1
                return 40 if downward_swipes[0] == 1 else 0
            return 0

        def find_state(_bot, templates, screen=None, *, region, threshold):
            if templates == flow.opened:
                return (flow.opened[0], (100, 100))
            if templates == flow.navigation:
                self.assertEqual(flow.navigation_region, region)
                return None
            if templates == flow.claims:
                self.assertEqual(flow.claim_region, region)
                if downward_swipes[0] and not bot.tap.called:
                    return (flow.claims[0], (320, 500))
            return None

        with (mock.patch.object(valuable_named_flow, "find_any", side_effect=find_state),
              mock.patch.object(valuable_named_flow, "_swipe_vertical", side_effect=swipe),
              mock.patch.object(valuable_named_flow, "close_congratulations", return_value=True)):
            self.assertTrue(valuable_named_flow.process_exact(bot, flow))

        bot.tap.assert_called_once_with(320, 500, delay=valuable_named_flow.STEP_DELAY)
        self.assertGreaterEqual(downward_swipes[0], 3)

    def test_active_monthly_card_without_chest_or_claim_is_done_after_edges(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        flow = active_monthly_card.FLOW

        def find_state(_bot, templates, screen=None, *, region, threshold):
            if templates == flow.opened:
                return (flow.opened[0], (100, 100))
            return None

        with (mock.patch.object(valuable_named_flow, "find_any", side_effect=find_state),
              mock.patch.object(valuable_named_flow, "_swipe_vertical", return_value=0) as swipe):
            self.assertTrue(valuable_named_flow.process_exact(bot, flow))

        bot.tap.assert_not_called()
        self.assertEqual(2, sum(call.kwargs["toward_start"] for call in swipe.call_args_list))
        self.assertEqual(2, sum(not call.kwargs["toward_start"] for call in swipe.call_args_list))

    def test_super_value_weekly_card_uses_same_vertical_green_frame_edges(self):
        flow = super_value_weekly_card.FLOW
        self.assertEqual(common.TEXT_CLAIM_CONTROLS, flow.claims)
        self.assertEqual((), flow.done)
        self.assertTrue(flow.absence_done)
        self.assertEqual((4, 59, 96, 99), flow.claim_region)
        self.assertTrue(flow.scroll_claims)
        self.assertEqual((50, 92), flow.scroll_start)
        self.assertEqual((50, 65), flow.scroll_end)
        self.assertEqual((4, 59, 96, 99), flow.scroll_region)
        self.assertTrue(flow.confirm_scroll_edges)
        self.assertEqual(24, flow.scroll_same_distance)
        self.assertEqual(2, flow.scroll_edge_confirmations)

    def test_vertical_green_frame_requires_two_unchanged_swipes_per_edge(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.screenshot.return_value = screen
        flow = valuable_named_flow.ExactFlow(
            scroll_claims=True, confirm_scroll_edges=True,
            scroll_region=(4, 59, 96, 99))

        # A moved frame resets the first edge counter.  Both the real top and
        # bottom then require two consecutive distances <= 24.
        distances = (5, 30, 10, 8, 50, 20, 24)
        with mock.patch.object(valuable_named_flow, "_swipe_vertical",
                               side_effect=distances) as swipe:
            completed, saw_claim, bottom = (
                valuable_named_flow._process_edge_scrolled(bot, flow))

        self.assertFalse(completed)
        self.assertFalse(saw_claim)
        self.assertTrue(bottom)
        self.assertEqual(len(distances), swipe.call_count)

    def test_reusable_region_hamming_distance_ignores_outside_changes(self):
        before = np.zeros((100, 100, 3), dtype=np.uint8)
        after = before.copy()
        after[:, :40] = 255

        distance = valuable_named_flow.region_hamming_distance(
            before, after, (50, 0, 100, 100))

        self.assertEqual(0, distance)

    def test_reusable_region_hamming_distance_counts_changed_hash_bits(self):
        rising = np.tile(np.arange(100, dtype=np.uint8), (100, 1))
        falling = np.fliplr(rising)
        before = np.repeat(rising[:, :, None], 3, axis=2)
        after = np.repeat(falling[:, :, None], 3, axis=2)

        distance = valuable_named_flow.region_hamming_distance(
            before, after, (0, 0, 100, 100))

        self.assertEqual(48 * 12, distance)

    def test_exact_flow_uses_configured_claim_scroll_geometry(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.screenshot.return_value = screen
        flow = valuable_named_flow.ExactFlow(
            claims=("Task/button_claim",), absence_done=True,
            claim_region=(4, 59, 96, 99),
            scroll_claims=True, scroll_start=(50, 92), scroll_end=(50, 65),
            scroll_region=(4, 59, 96, 99), max_scroll_pages=12)

        with mock.patch.object(valuable_named_flow, "find", return_value=None):
            self.assertTrue(valuable_named_flow.process_exact(bot, flow))

        bot.swipe_percent.assert_called_once_with(
            50, 92, 50, 65, duration=valuable_named_flow.SLOW_SWIPE_DURATION,
            delay=valuable_named_flow.STEP_DELAY)

    def test_scroll_absence_stays_pending_until_bottom_is_confirmed(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        flow = valuable_named_flow.ExactFlow(
            claims=("Task/button_claim",), absence_done=True,
            scroll_claims=True, max_scroll_pages=2)
        moving = np.ones((570, 396, 3), dtype=np.uint8)

        with (mock.patch.object(valuable_named_flow, "find", return_value=None),
              mock.patch.object(valuable_named_flow.cv2, "absdiff",
                                return_value=moving)):
            self.assertFalse(valuable_named_flow.process_exact(bot, flow))

        self.assertEqual(1, bot.swipe_percent.call_count)
        self.assertTrue(any(
            "chưa xác nhận đáy" in call.args[0]
            for call in bot.record.call_args_list))

    def test_login_gift_confirms_and_closes_congratulations(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        shown = [False]

        def find_popup(_bot, name, *_args, **_kwargs):
            if name == login_gifts.CONGRATULATIONS and not shown[0]:
                shown[0] = True
                return (198, 319)
            if name == login_gifts.PAGE:
                return (40, 140)
            return None

        with (mock.patch.object(login_gifts, "find", side_effect=find_popup),
              mock.patch.object(login_gifts, "find_reward_chest",
                                return_value=None)):
            self.assertTrue(login_gifts._tap_reward(bot, (123, 470)))

        bot.tap.assert_called_once_with(123, 470, delay=1)
        bot.back.assert_called_once_with(delay=1)
        self.assertEqual(login_gifts.POST_TAP_WAIT,
                         bot.sleep.call_args_list[0].args[0])

    def test_login_gift_is_done_when_fresh_screenshot_has_no_chest(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)

        def find_state(_bot, name, *_args, **_kwargs):
            if name == login_gifts.PAGE:
                return (40, 140)
            return None

        with (mock.patch.object(login_gifts, "find", side_effect=find_state),
              mock.patch.object(login_gifts, "find_reward_chest",
                                return_value=None)):
            self.assertTrue(login_gifts._tap_reward(bot, (45, 190)))

        bot.tap.assert_called_once_with(45, 190, delay=1)
        bot.back.assert_not_called()

    def test_login_gift_congratulations_alone_is_not_done_if_chest_remains(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        shown = [False]

        def find_state(_bot, name, *_args, **_kwargs):
            if name == login_gifts.CONGRATULATIONS and not shown[0]:
                shown[0] = True
                return (198, 319)
            if name == login_gifts.PAGE:
                return (40, 140)
            return None

        with (mock.patch.object(login_gifts, "find", side_effect=find_state),
              mock.patch.object(login_gifts, "find_reward_chest",
                                return_value=(40, 198))):
            self.assertFalse(login_gifts._tap_reward(bot, (40, 198)))

        bot.back.assert_called_once_with(delay=1)

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

    def test_moment_of_glory_assets_and_limited_registration(self):
        for name in ("list_row.png", "title.png", "status_claimed.png"):
            self.assertTrue((IMAGES / "GiftClaims" / "EventCenter" /
                             "MomentOfGlory" / name).is_file())
        moment = next(policy for policy in event_center.EVENT_POLICIES
                      if policy.key == "gift_moment_of_glory")
        self.assertEqual(GiftScreen.MOMENT_OF_GLORY, moment.screen)
        self.assertNotIn(moment.key, event_center.POLICY_CATEGORIES)
        self.assertTrue(any(
            row[0] == "EventCenter/MomentOfGlory/list_row"
            and row[2] == GiftScreen.MOMENT_OF_GLORY
            for row in event_center.FORCED_LIMITED_ROWS))

    def test_moment_of_glory_title_identifies_opened_page(self):
        title = cv2.imread(str(IMAGES / "GiftClaims" / "EventCenter" /
                               "MomentOfGlory" / "title.png"))
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        height, width = title.shape[:2]
        screen[5:5 + height, 100:100 + width] = title
        self.assertEqual(GiftScreen.MOMENT_OF_GLORY,
                         identify(CvBot(), screen))

    def test_moment_of_glory_no_claim_full_pass_is_done(self):
        bot = mock.Mock()
        with (mock.patch.object(event_center, "_moment_swipe_to_top"),
              mock.patch.object(event_center, "_scan_moment_once",
                                return_value=(common.ClaimReport(),
                                              True, False)) as scan):
            report, done = event_center._handle_moment_of_glory(bot)

        self.assertTrue(done)
        self.assertEqual(common.ClaimReport(), report)
        scan.assert_called_once_with(bot)

    def test_moment_of_glory_claim_requires_clean_followup_pass(self):
        bot = mock.Mock()
        with (mock.patch.object(event_center,
                                "_moment_swipe_to_top") as to_top,
              mock.patch.object(event_center, "_scan_moment_once",
                                side_effect=[
                                    (common.ClaimReport(2, 2), True, False),
                                    (common.ClaimReport(), True, False),
                                ]) as scan):
            report, done = event_center._handle_moment_of_glory(bot)

        self.assertTrue(done)
        self.assertEqual(common.ClaimReport(2, 2), report)
        self.assertEqual(2, to_top.call_count)
        self.assertEqual(2, scan.call_count)

    def test_moment_of_glory_stuck_claim_stays_pending(self):
        bot = mock.Mock()
        with (mock.patch.object(event_center, "_moment_swipe_to_top"),
              mock.patch.object(event_center, "_scan_moment_once",
                                return_value=(common.ClaimReport(1, 0),
                                              False, True))):
            _, done = event_center._handle_moment_of_glory(bot)

        self.assertFalse(done)

    def test_moment_of_glory_rejects_gray_claimed_prefix(self):
        claimed = cv2.imread(str(
            IMAGES / "GiftClaims" / "EventCenter" / "MomentOfGlory" /
            "status_claimed.png"))
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        top, left = 610, 300
        screen[top:top + claimed.shape[0],
               left:left + claimed.shape[1]] = claimed
        center = (left + claimed.shape[1] // 2,
                  top + claimed.shape[0] // 2)

        with mock.patch.object(event_center, "find_all",
                               return_value=[center]):
            self.assertEqual([], event_center._moment_claims(bot=mock.Mock(),
                                                              screen=screen))

    def test_moment_of_glory_accepts_green_claim_band(self):
        claim = cv2.imread(str(IMAGES / "GiftClaims" / "Common" /
                               "button_claim_text.png"))
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        top, left = 610, 315
        screen[top:top + claim.shape[0], left:left + claim.shape[1]] = claim
        center = (left + claim.shape[1] // 2,
                  top + claim.shape[0] // 2)

        with mock.patch.object(event_center, "find_all",
                               return_value=[center]):
            self.assertEqual([center], event_center._moment_claims(
                bot=mock.Mock(), screen=screen))

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

    def test_wishful_panel_with_only_claimed_still_scans_to_the_bottom(self):
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
        self.assertEqual(2, bot.swipe_percent.call_count)

    def test_wishful_done_one_no_records_finishes_without_claim_or_scroll(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(event_center, "_wishful_panel_open",
                                return_value=True),
              mock.patch.object(event_center, "_wishful_done_one_no_records",
                                return_value=True),
              mock.patch.object(event_center, "_wishful_claims") as claims):
            report, done = event_center._claim_wishful_panel(bot, "DONE 1")

        self.assertTrue(done)
        self.assertEqual(common.ClaimReport(0, 1), report)
        claims.assert_not_called()
        bot.swipe_percent.assert_not_called()

    def test_wishful_done_two_scan_uses_the_measured_left_frame_gesture(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(event_center, "_wishful_panel_open",
                                return_value=True),
              mock.patch.object(event_center, "_wishful_claims",
                                return_value=[]),
              mock.patch.object(event_center, "_wishful_claimed",
                                return_value=[])):
            _report, done = event_center._claim_wishful_panel(
                bot, "Challenge Quest")

        self.assertTrue(done)
        expected = mock.call(
            *event_center.WISHFUL_SCAN_SWIPE,
            duration=event_center.WISHFUL_SCROLL_DURATION_SECONDS,
            delay=event_center.LIST_SCROLL_SETTLE_SECONDS)
        self.assertEqual([expected, expected], bot.swipe_percent.call_args_list)

    def test_wishful_claim_and_claimed_require_opposite_colour_bands(self):
        root = IMAGES / "GiftClaims" / "EventCenter" / "WishfulWindmillFestival"
        claim = cv2.imread(str(root / "button_claim.png"))
        claimed = cv2.imread(str(root / "status_claimed.png"))
        claim_center = (claim.shape[1] // 2, claim.shape[0] // 2)
        claimed_center = (claimed.shape[1] // 2, claimed.shape[0] // 2)

        self.assertTrue(event_center._wishful_is_green_claim(
            claim, claim_center))
        self.assertFalse(event_center._wishful_is_gray_claimed(
            claim, claim_center))
        self.assertFalse(event_center._wishful_is_green_claim(
            claimed, claimed_center))
        self.assertTrue(event_center._wishful_is_gray_claimed(
            claimed, claimed_center))

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
              mock.patch.object(event_center, "_claim_wishful_done_two_chest",
                                return_value=(common.ClaimReport(1, 1), True)) as chest,
              mock.patch.object(event_center, "_wait_for",
                                side_effect=((190, 80), (198, 620)))):
            report, done = event_center._handle_wishful(bot)

        self.assertTrue(done)
        self.assertEqual(common.ClaimReport(6, 6), report)
        open_first.assert_called_once_with(bot)
        self.assertEqual([mock.call(bot, "DONE 1"),
                          mock.call(bot, "Challenge Quest")],
                         claim.call_args_list)
        chest.assert_called_once_with(bot)
        self.assertEqual(
            [mock.call(delay=event_center.WISHFUL_SETTLE_SECONDS)] * 2,
            bot.back.call_args_list)

    def test_wishful_done_two_without_new_claim_still_requires_final_chest(self):
        bot = mock.Mock()
        first = common.ClaimReport(1, 1)
        second = common.ClaimReport(0, 1)
        with (mock.patch.object(event_center, "_wishful_open_blessings",
                                return_value=True),
              mock.patch.object(event_center, "_claim_wishful_panel",
                                side_effect=((first, True), (second, True))),
              mock.patch.object(event_center, "_claim_wishful_done_two_chest",
                                return_value=(common.ClaimReport(1, 1), True)) as chest,
              mock.patch.object(event_center, "_wait_for",
                                side_effect=((190, 80), (198, 620)))):
            report, done = event_center._handle_wishful(bot)

        self.assertTrue(done)
        self.assertEqual(common.ClaimReport(2, 3), report)
        chest.assert_called_once_with(bot)
        self.assertEqual(
            [mock.call(delay=event_center.WISHFUL_SETTLE_SECONDS)] * 2,
            bot.back.call_args_list)

    def test_wishful_done_two_with_unresolved_claim_stays_pending(self):
        bot = mock.Mock()
        first = common.ClaimReport(1, 1)
        second = common.ClaimReport(3, 0)
        with (mock.patch.object(event_center, "_wishful_open_blessings",
                                return_value=True),
              mock.patch.object(event_center, "_claim_wishful_panel",
                                side_effect=((first, True), (second, False))),
              mock.patch.object(event_center, "_claim_wishful_done_two_chest") as chest,
              mock.patch.object(event_center, "_wait_for",
                                side_effect=((190, 80), (198, 620)))):
            report, done = event_center._handle_wishful(bot)

        self.assertFalse(done)
        self.assertEqual(common.ClaimReport(4, 1), report)
        chest.assert_not_called()

    def test_wishful_done_two_final_chest_requires_congratulations(self):
        bot = mock.Mock()
        with (mock.patch.object(event_center, "_wait_for",
                                return_value=(39, 157)),
              mock.patch.object(event_center, "close_congratulations",
                                side_effect=(True, False))):
            claimed, done = event_center._claim_wishful_done_two_chest(bot)
            pending, pending_done = event_center._claim_wishful_done_two_chest(bot)

        self.assertTrue(done)
        self.assertEqual(common.ClaimReport(1, 1), claimed)
        self.assertFalse(pending_done)
        self.assertEqual(common.ClaimReport(1, 0), pending)
        self.assertEqual(
            [mock.call(39, 157, delay=event_center.WISHFUL_SETTLE_SECONDS)] * 2,
            bot.tap.call_args_list)

    def test_wishful_done_two_final_chest_disappearance_is_done(self):
        bot = mock.Mock()
        with (mock.patch.object(event_center, "_wait_for",
                                side_effect=((39, 157), None)) as wait,
              mock.patch.object(event_center, "close_congratulations",
                                return_value=False)):
            report, done = event_center._claim_wishful_done_two_chest(bot)

        self.assertTrue(done)
        self.assertEqual(common.ClaimReport(1, 1), report)
        self.assertEqual(2, wait.call_count)
        bot.tap.assert_called_once_with(
            39, 157, delay=event_center.WISHFUL_SETTLE_SECONDS)

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

    def test_lucky_apple_multiplier_rejects_a_low_score_match_at_wish_once(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        # x100 only weakly matches the yellow Wish Once button.  The exact
        # Once crop is strong at that same position, so this must be absent,
        # not an endless sequence of x100 taps.
        bot.best_match.side_effect = (
            (0.475, (200, 620)),  # x100 active
            (0.321, (200, 620)),  # x100 done
            (0.960, (200, 620)),  # Wish Once active
            (0.330, (200, 620)),  # Wish Once gray
            (0.960, (200, 620)),  # Wish Once active (DONE candidate)
            (0.330, (200, 620)),  # Wish Once gray (DONE candidate)
        )
        with (mock.patch.object(event_center, "_scaled_template",
                                side_effect=lambda _bot, name, _screen: name),
              mock.patch.object(event_center, "_apple_button_color_band",
                                return_value=(184.6, 0.80))):
            state, position = event_center._apple_button_state(
                bot, screen,
                "EventCenter/DwarfsLuckyApple/button_green_wish_x100",
                "EventCenter/DwarfsLuckyApple/status_green_wish_x100_done",
                exclude_once=True)

        self.assertIsNone(state)
        self.assertIsNone(position)

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

    def test_lucky_apple_red_post_tap_only_once_is_done(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        # Captured terminal layout: the x10 ACTIVE crop weakly matches the
        # sole remaining Wish Once at 0.449; the old DONE crop only gets 0.340.
        bot.best_match.side_effect = ((0.449, (250, 620)),
                                      (0.340, (250, 620)))
        with (mock.patch.object(event_center, "_scaled_template",
                                return_value=np.zeros((38, 151, 3),
                                                      dtype=np.uint8)),
              mock.patch.object(event_center, "_apple_button_color_band",
                                return_value=(28.8, 0.09)),
              mock.patch.object(event_center, "_apple_special_state",
                                return_value=("red-once", (250, 620)))):
            done = event_center._apple_red_x10_post_tap_done(bot, screen)

        self.assertTrue(done)

    def test_lucky_apple_red_post_tap_keeps_distinct_yellow_x10_active(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.best_match.return_value = (0.480, (250, 520))
        with (mock.patch.object(event_center, "_scaled_template",
                                return_value=np.zeros((38, 151, 3),
                                                      dtype=np.uint8)),
              mock.patch.object(event_center, "_apple_button_color_band",
                                return_value=(189.3, 0.83)),
              mock.patch.object(event_center, "_apple_special_state",
                                return_value=("red-once", (250, 620)))):
            done = event_center._apple_red_x10_post_tap_done(bot, screen)

        self.assertFalse(done)

    def test_lucky_apple_red_both_gray_multipliers_are_done(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.best_match.side_effect = ((0.96, (250, 510)),
                                      (0.94, (250, 610)))
        with (mock.patch.object(event_center, "_scaled_template",
                                return_value=np.zeros((35, 153, 3),
                                                      dtype=np.uint8)),
              mock.patch.object(event_center, "_apple_button_color_band",
                                return_value=(22.0, 0.05))):
            done = event_center._apple_red_multipliers_gray(bot)

        self.assertTrue(done)

    def test_lucky_apple_red_gray_templates_must_be_distinct(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        bot.best_match.side_effect = ((0.96, (250, 610)),
                                      (0.94, (250, 610)))
        with (mock.patch.object(event_center, "_scaled_template",
                                return_value=np.zeros((35, 153, 3),
                                                      dtype=np.uint8)),
              mock.patch.object(event_center, "_apple_button_color_band",
                                return_value=(22.0, 0.05))):
            done = event_center._apple_red_multipliers_gray(bot)

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
              mock.patch.object(event_center, "identify",
                                return_value=GiftScreen.DWARFS_LUCKY_APPLE),
              mock.patch.object(event_center, "_apple_button_state",
                                side_effect=states) as state):
            _report, done = event_center._apple_phase(
                bot, "active.png", "done.png", max_taps=1)

        self.assertTrue(done)
        self.assertEqual(4, state.call_count)
        bot.back.assert_not_called()

    def test_lucky_apple_lagged_colour_bands_override_low_template_score(self):
        bot = mock.Mock()
        screen = np.zeros((704, 396, 3), dtype=np.uint8)
        yellow = (185.4, 0.81)
        gray = (23.7, 0.07)
        with (mock.patch.object(event_center, "_scaled_template",
                                side_effect=("active", "done")),
              mock.patch.object(bot, "best_match",
                                side_effect=((0.485, (250, 500)),
                                             (0.312, (250, 500)))),
              mock.patch.object(event_center, "_apple_button_color_band",
                                side_effect=(yellow, gray))):
            state, _ = event_center._apple_button_state(
                bot, screen, "active.png", "done.png")
        self.assertEqual("active", state)

        with (mock.patch.object(event_center, "_scaled_template",
                                side_effect=("active", "done")),
              mock.patch.object(bot, "best_match",
                                side_effect=((0.545, (250, 500)),
                                             (0.491, (250, 500)))),
              mock.patch.object(event_center, "_apple_button_color_band",
                                side_effect=(gray, gray))):
            state, _ = event_center._apple_button_state(
                bot, screen, "active.png", "done.png")
        self.assertEqual("done", state)

    def test_lucky_apple_missing_popup_still_rechecks_and_taps_active(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(event_center, "_apple_congratulations_hit",
                                return_value=None),
              mock.patch.object(event_center, "identify",
                                return_value=GiftScreen.DWARFS_LUCKY_APPLE),
              mock.patch.object(event_center, "_apple_button_state",
                                side_effect=(("active", (250, 500)),
                                             ("done", (250, 500)))),
              mock.patch.object(event_center, "_close_apple_congratulations",
                                return_value=False) as close):
            report, done = event_center._apple_phase(
                bot, "active.png", "done.png", max_taps=2)

        self.assertTrue(done)
        self.assertEqual(common.ClaimReport(1, 1), report)
        bot.tap.assert_called_once_with(
            250, 500, delay=event_center.UI_SETTLE_SECONDS)
        close.assert_called_once_with(bot, attempts=3)

    def test_lucky_apple_stops_after_three_frames_on_wrong_page(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(event_center, "_apple_congratulations_hit",
                                return_value=None),
              mock.patch.object(event_center, "identify",
                                return_value=GiftScreen.EVENT_CENTER),
              mock.patch.object(event_center, "_apple_button_state",
                                return_value=(None, None))):
            _report, done = event_center._apple_phase(
                bot, "active.png", "done.png", max_taps=2)

        self.assertFalse(done)
        self.assertEqual(3, bot.screenshot.call_count)

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

    def test_lucky_apple_red_both_gray_shortcuts_red_claim_phase(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(event_center, "_wait_for_any",
                                side_effect=((300, 300), (100, 300))),
              mock.patch.object(event_center, "_wait_apple_special_state",
                                return_value=("green-once", (250, 540))),
              mock.patch.object(event_center, "_apple_red_multipliers_gray",
                                return_value=True),
              mock.patch.object(event_center, "_run_optional_apple_phase",
                                side_effect=(
                                    (common.ClaimReport(2, 2), True, True),
                                    (common.ClaimReport(3, 3), True, True),
                                    (common.ClaimReport(), True, False),
                                )) as phase):
            report, done = event_center._handle_dwarfs_lucky_apple(bot)

        self.assertTrue(done)
        self.assertEqual(common.ClaimReport(5, 5), report)
        self.assertEqual(3, phase.call_count)

    def test_lucky_apple_green_both_gray_switches_to_red_without_once(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(event_center, "_wait_for_any",
                                side_effect=((300, 300), (100, 300))),
              mock.patch.object(event_center, "_apple_green_multipliers_gray",
                                return_value=True),
              mock.patch.object(event_center, "_wait_apple_special_state") as once,
              mock.patch.object(event_center, "_run_optional_apple_phase",
                                return_value=(common.ClaimReport(2, 2),
                                              True, True)) as phase):
            report, done = event_center._handle_dwarfs_lucky_apple(bot)

        self.assertTrue(done)
        self.assertEqual(common.ClaimReport(2, 2), report)
        once.assert_not_called()
        self.assertEqual(1, phase.call_count)
        self.assertIn("button_red_wish_x10", phase.call_args.args[1])

    def test_lucky_apple_red_x10_gray_is_done_before_once_shortcut(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with (mock.patch.object(event_center, "_wait_for_any",
                                side_effect=((300, 300), (100, 300))),
              mock.patch.object(event_center, "_wait_apple_special_state",
                                return_value=("green-once", (250, 540))),
              mock.patch.object(event_center, "_apple_red_multipliers_gray")
              as both_gray,
              mock.patch.object(event_center, "_run_optional_apple_phase",
                                side_effect=(
                                    (common.ClaimReport(), True, False),
                                    (common.ClaimReport(), True, False),
                                    (common.ClaimReport(1, 1), True, True),
                                )) as phase):
            report, done = event_center._handle_dwarfs_lucky_apple(bot)

        self.assertTrue(done)
        self.assertEqual(common.ClaimReport(1, 1), report)
        self.assertEqual(3, phase.call_count)
        both_gray.assert_not_called()

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
        self.assertEqual((40, 112), cv2.imread(str(
            folder / "status_red_wish_x100_done.png")).shape[:2])

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

    def test_event_center_uses_two_confirmations_without_local_swipe_ceiling(self):
        self.assertEqual(2, event_center.LIST_EDGE_CONFIRMATIONS)
        self.assertEqual(8, event_center.LIST_SAME_DISTANCE)
        self.assertFalse(hasattr(event_center, "MAX_SCROLLS"))
        self.assertFalse(hasattr(event_center, "APPLE_LIST_MAX_SWIPES"))

    def test_event_center_list_hamming_ignores_right_side_animation(self):
        first = np.zeros((704, 396, 3), dtype=np.uint8)
        for y in range(110, 700, 100):
            first[y:y + 4, :270] = 220
            first[y + 15:y + 28, 70:220] = 160
        animated = first.copy()
        animated[110:690, 275:] = 255

        old = event_center._list_signature(first)
        new = event_center._list_signature(animated)
        self.assertEqual(0, event_center._list_hamming_distance(old, new))
        self.assertTrue(event_center._same_list_position(old, new))

    def test_event_center_list_hamming_detects_vertical_displacement(self):
        first = np.zeros((704, 396, 3), dtype=np.uint8)
        for index, y in enumerate(range(110, 700, 87)):
            first[y:y + 3, :270] = 220
            first[y + 10:y + 18 + index, 60:230] = 80 + index * 20
        shifted = np.roll(first, 60, axis=0)

        distance = event_center._list_hamming_distance(
            event_center._list_signature(first),
            event_center._list_signature(shifted))
        self.assertGreater(distance, event_center.LIST_SAME_DISTANCE)

    def test_event_center_top_edge_requires_two_unchanged_swipes(self):
        bot = mock.Mock()
        bot.screenshot.return_value = np.zeros((704, 396, 3), dtype=np.uint8)
        with mock.patch.object(event_center, "_same_list_position",
                               side_effect=(True, False, True, True)):
            self.assertTrue(event_center._return_list_to_top(bot, "limited"))

        self.assertEqual(4, bot.swipe_percent.call_count)

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
              mock.patch.object(event_center, "identify",
                                return_value=GiftScreen.GRACE_OF_STAR_TRAIL),
              mock.patch.object(event_center, "_process_opened_event") as process,
              mock.patch.object(event_center, "_back_to_list", return_value=True),
              mock.patch.object(event_center, "_list_signature", return_value=b"same")):
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
              mock.patch.object(event_center, "identify",
                                return_value=GiftScreen.DWARFS_TREASURE),
              mock.patch.object(event_center, "_process_opened_event") as process,
              mock.patch.object(event_center, "_back_to_list", return_value=True),
              mock.patch.object(event_center, "_list_signature", return_value=b"same")):
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

        self.assertNotIn(dragon, inspected)
        self.assertNotIn(apple, inspected)
        bot.mark_daily_done.assert_called_once_with(
            f"{dragon}_miss_done_1")

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

    def test_event_center_has_no_outer_red_dot_scanner(self):
        self.assertFalse(hasattr(event_center, "DOT"))
        self.assertFalse(hasattr(event_center, "_row_dots"))
        self.assertFalse(hasattr(event_center, "_verify_clean"))

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
                           event_center.FIXED_CLAIMS,
                           back_to_territory.FIXED_CLAIMS):
            self.assertIn("Common/button_claim_text", collection)


if __name__ == "__main__":
    unittest.main()
