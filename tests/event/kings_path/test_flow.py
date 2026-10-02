"""
Flow test Event / King's Path (bot/activities/event/kings_path/): phần trên màn King's Path
— kiểm Day khoá -> tab Day -> tab phụ -> dòng Go của nhiệm vụ -> đọc tiến độ -> bấm Go.

Ảnh trong screens/ là ảnh chụp nguyên màn hình giả lập 396x704 (Day 5 đang khoá).

test_open_from_main đi đủ từ màn chính (03_main chép từ test Ground Troop); các test khác bắt
đầu ngay ở màn King's Path.
"""
import sys
from types import SimpleNamespace
from dataclasses import replace
import unittest
from pathlib import Path
from unittest import mock

import cv2


from bot.activities import event
from bot.activities.event.constants import CLAIM_ALL, KINGS_PATH_ICON
from bot.activities.event.kings_path import black_market, city_tax, donate, heal, patrol, path_task, train_troop, wheel
from bot.activities.event.kings_path.city_tax.constants import POPUP_TAX, TAX_MENU
from bot.activities.event.kings_path.city_tax.run import split_counts
from bot.activities.event.kings_path.donate.constants import DONATE_BUTTON, GEMS_BUTTON, OKAY
from bot.activities.event.kings_path.donate.alliance import alliance_key as donate_alliance_key
from bot.activities.event.kings_path.black_market.constants import (
    CONFIRM as BM_CONFIRM, INSTANT_REFRESH as BM_REFRESH, MENU_BLACK_MARKET as BM_MENU, SLOTS as BM_SLOTS)
from bot.activities.event.kings_path.heal.constants import MENU_HEAL as HEAL_MENU_HEAL, MENU_SPEED_UP as HEAL_MENU_SPEED_UP, RESET as HEAL_RESET, HEAL_BUTTON
from bot.activities.event.kings_path.heal.constants import INPUT_OK as HEAL_INPUT_OK, SPEED_UP as HEAL_SPEED_UP
from bot.activities.event.gather_troops.train_troop.constants import (
    CHECKBOX_OFF as TRAIN_CHECKBOX_OFF, CONFIRM as TRAIN_CONFIRM, FINISH_ALL as TRAIN_FINISH_ALL,
    SPEEDUP_SETTINGS as TRAIN_SPEEDUP_SETTINGS)
from bot.activities.event.kings_path.patrol.constants import (
    MENU_PATROL, PATROL_BUTTON, REFRESH_BUTTON as PATROL_REFRESH, SELECT_ALL_OFF as PATROL_SELECT_ALL_OFF)
from bot.activities.event.kings_path.patrol.run import round_key as patrol_round_key
from bot.activities.event.kings_path.wheel.constants import SPINS_10, SPINS_100
from bot.context import TEMPLATE_DIR, BotContext
from bot.context.errors import YieldToBoss
from bot.activities.event.gather_troops.troop_tier import choose_first_tier
from bot.activities.event.kings_path.train_troop.constants import TIERS as TRAIN_TIERS
from tests.flow import Step, back, end, run_flow, swipe, tap, tap_at, tap_pct
from tests.event import setUpModule, tearDownModule  # noqa: F401 (tắt lượt nhận thưởng)

SCREENS = Path(__file__).parent / "screens"
KP = "Event/KingsPath"
EVENT_BUTTON = (369, 281)   # chữ "Event Center" (359, 241) + (10, 40), xem test Gather Troops


def _blank(y0, y1, x0, x1):
    """Biến thể ảnh: tô đen một vùng."""
    def fn(bgr):
        bgr[y0:y1, x0:x1] = 0
        return bgr
    return fn


def _sold_out(bgr):
    """Black Market: mọi nút giá xám (đã mua hết) — tô đen 6 nút giá."""
    for x, y in BM_SLOTS:
        bgr[y - 10:y + 10, x - 44:x + 44] = 40
    return bgr


VARIANTS = {
    # Black Market đã mua hết 6 món (nút giá không còn xanh).
    "sold_out": _sold_out,
    # Màn chính đã nhận quà: không còn icon Login Gifts (cột phải + góc dưới trái).
    "main_claimed": lambda bgr: _blank(525, 575, 0, 60)(_blank(130, 170, 330, 396)(bgr)),
    # Đã bấm Claim All: xoá nút Claim All ở đáy màn.
    "claimed": _blank(655, 695, 140, 256),
    # Màn event cùng khung nhưng không phải King's Path (VD Gather Troops): xoá tiêu đề.
    "not_kp": _blank(5, 40, 120, 280),
}


def _run(testcase, flow, settings, **kw):
    return run_flow(testcase, event.run, SCREENS, flow, settings, variants=VARIANTS, **kw)


class KingsPathFlow(unittest.TestCase):
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

    def test_patrol(self):
        """Day 2 (tab Unstoppable) -> tab Teamwork -> dòng "Patrol for" trên cùng (140 / 150) -> Go."""
        flow = [
            Step("day2_unstoppable.png", tap(CLAIM_ALL)),
            Step("day2_unstoppable.png?claimed", tap(f"{KP}/Tab/teamwork.png")),
            Step("day2_teamwork.png", tap_at(335, 344)),   # sau Go: harness dừng bot
        ]
        device = _run(self, flow, {patrol.KEY: {"value": 200, "day": 2}})
        self.assertIn("Patrol: done 140, target 200", device.logs)

    def test_patrol_rounds(self):
        """Patrol (đã làm 140, mục tiêu 160): Go -> bấm giữa thành -> icon Patrol -> Select All ->
        Patrol (+10) -> đã patrol -> Refresh -> Select All -> Patrol (+10 = 160) -> đủ, Back, xong."""
        rounds = [
            Step("patrol_screen.png", tap(PATROL_SELECT_ALL_OFF)),
            Step("patrol_selected.png", tap(PATROL_BUTTON)),
        ]
        flow = [
            Step("day2_teamwork.png", tap_at(335, 344)),
            Step("patrol_city.png", tap_pct(50, 50)),
            Step("patrol_menu.png", tap(MENU_PATROL)),
            *rounds,
            Step("patrol_done.png", tap(PATROL_REFRESH)),
            *rounds,
            Step("patrol_done.png", back(), end()),
        ]
        device = _run(self, flow, {patrol.KEY: {"value": 160, "day": 2}})
        self.assertIn("Patrol: progress 160 / 160, done", device.logs)
        self.assertIn(patrol.KEY, device.daily_done)
        self.assertIn(patrol_round_key(2), device.daily_done)

    def test_patrol_daily_limit(self):
        """Hôm nay đã patrol 9 lượt (lưu daily_done): patrol thêm 1 lượt -> đủ 10 -> Back, xong hôm
        nay (mục tiêu 200 chưa đủ, mai làm tiếp)."""
        flow = [
            Step("day2_teamwork.png", tap_at(335, 344)),
            Step("patrol_city.png", tap_pct(50, 50)),
            Step("patrol_menu.png", tap(MENU_PATROL)),
            Step("patrol_screen.png", tap(PATROL_SELECT_ALL_OFF)),
            Step("patrol_selected.png", tap(PATROL_BUTTON)),
            Step("patrol_done.png", back(), end()),
        ]
        done = {patrol_round_key(n): "2026-10-02T08:00:00" for n in range(1, 10)}
        device = _run(self, flow, {patrol.KEY: {"value": 200, "day": 2}}, daily_done=done)
        self.assertIn("Patrol: 10 rounds today, done for today", device.logs)
        self.assertIn(patrol.KEY, device.daily_done)

    def test_patrol_out_of_refreshes(self):
        """Refresh mà phần thưởng vẫn là bộ đã patrol (hết lượt Refresh): Back, xong hôm nay."""
        flow = [
            Step("day2_teamwork.png", tap_at(335, 344)),
            Step("patrol_city.png", tap_pct(50, 50)),
            Step("patrol_menu.png", tap(MENU_PATROL)),
            Step("patrol_done.png", tap(PATROL_REFRESH)),
            Step("patrol_done.png", back(), end()),
        ]
        device = _run(self, flow, {patrol.KEY: {"value": 200, "day": 2}})
        self.assertIn(patrol.KEY, device.daily_done)

    def test_patrol_not_confirmed(self):
        """Bấm Patrol mà màn không chuyển sang "đã patrol" (game chậm / popup): không tính lượt,
        không cộng tiến độ, dừng (không đánh dấu xong)."""
        flow = [
            Step("day2_teamwork.png", tap_at(335, 344)),
            Step("patrol_city.png", tap_pct(50, 50)),
            Step("patrol_menu.png", tap(MENU_PATROL)),
            Step("patrol_selected.png", tap(PATROL_BUTTON)),
            Step("patrol_selected.png", end()),
        ]
        device = _run(self, flow, {patrol.KEY: {"value": 200, "day": 2}})
        self.assertNotIn(patrol_round_key(1), device.daily_done)
        self.assertNotIn(patrol.KEY, device.daily_done)

    def test_patrol_claimed_detection(self):
        """Đếm dấu tích lớn: chưa tích / chỉ tích ô nhỏ -> chưa patrol; sau patrol / hết lượt -> đã."""
        claimed = sys.modules["bot.activities.event.kings_path.patrol.run"]._claimed
        for name, expected in (("patrol_screen.png", False), ("patrol_selected.png", False),
                               ("patrol_done.png", True), ("patrol_no_refresh.png", True)):
            self.assertEqual(claimed(cv2.imread(str(SCREENS / name))), expected, name)

    def test_patrol_refresh_disabled(self):
        """Đã patrol lượt hiện tại, nút Refresh xám (Refreshes Today 10/10, ảnh thật): Back, xong
        hôm nay — không bấm Refresh."""
        flow = [
            Step("day2_teamwork.png", tap_at(335, 344)),
            Step("patrol_city.png", tap_pct(50, 50)),
            Step("patrol_menu.png", tap(MENU_PATROL)),
            Step("patrol_no_refresh.png", back(), end()),
        ]
        device = _run(self, flow, {patrol.KEY: {"value": 200, "day": 2}})
        self.assertIn("Patrol: Refresh disabled (out of refreshes), done for today", device.logs)
        self.assertIn(patrol.KEY, device.daily_done)

    def test_donate(self):
        """Tab Teamwork: dòng "Donate to the Alliance" (0 / 10) -> Go -> Alliance Science:
        Donate 2 lần -> hết lượt (nút kim cương) -> Okay -> Donate lần 3 -> xong (mục tiêu 3)."""
        flow = [
            Step("day2_teamwork.png", tap_at(335, 567)),
            Step("donate_science.png", tap(DONATE_BUTTON)),
            Step("donate_science.png", tap(DONATE_BUTTON)),
            Step("donate_gems.png", tap(GEMS_BUTTON)),
            Step("donate_confirm_gems.png", tap(OKAY)),
            Step("donate_science.png", tap(DONATE_BUTTON), end()),
        ]
        device = _run(self, flow, {donate.KEY: {"value": 3, "day": 2}})
        self.assertIn("Donate: done 0, target 3", device.logs)
        self.assertIn(donate.KEY, device.daily_done)

    def test_donate_via_alliance_when_patrol_off(self):
        """Ô Patrol = 0: Donate không vào King's Path mà qua Liên minh -> Alliance Science (ở sẵn
        màn đó), donate 2 lần (lưu từng lần vào daily_done) -> đủ, Back, xong."""
        settings = {patrol.KEY: {"value": 0, "day": 2}, donate.KEY: {"value": 2, "day": 2}}
        flow = [
            Step("donate_science.png", tap(DONATE_BUTTON)),
            Step("donate_science.png", tap(DONATE_BUTTON)),
            Step("donate_science.png", back(), end()),
        ]
        device = _run(self, flow, settings, ctx_settings={"Event": settings})
        self.assertIn(donate_alliance_key(1), device.daily_done)
        self.assertIn(donate_alliance_key(2), device.daily_done)
        self.assertIn(donate.KEY, device.daily_done)
        self.assertNotIn("King's Path", " ".join(device.logs))

    def test_donate_via_alliance_full_path(self):
        """Ô Patrol = 0, đi đủ đường (ảnh thật): màn chính -> nút Liên minh -> màn Liên minh (Alliance
        Science bị che) -> cuộn 2 lần -> Alliance Science -> donate thẻ đầu (Alliance Capacity) -> xong."""
        settings = {patrol.KEY: {"value": 0, "day": 2}, donate.KEY: {"value": 1, "day": 2}}
        flow = [
            Step("alliance_main.png", tap("JoinBoss/lienminh.png")),
            Step("alliance_screen.png", swipe(50, 87, 50, 54), swipe(50, 87, 50, 54)),
            Step("alliance_scrolled.png", tap("Science/scienceclick.png")),
            Step("alliance_science.png", tap(DONATE_BUTTON)),
            Step("alliance_science.png", back(), end()),
        ]
        device = _run(self, flow, settings, ctx_settings={"Event": settings})
        self.assertIn(donate.KEY, device.daily_done)

    def test_donate_via_alliance_resumes(self):
        """Đường Liên minh, hôm nay đã donate 2 / 3 (bị ngắt): chỉ donate thêm 1 lần."""
        settings = {patrol.KEY: {"value": 0, "day": 2}, donate.KEY: {"value": 3, "day": 2}}
        flow = [
            Step("donate_science.png", tap(DONATE_BUTTON)),
            Step("donate_science.png", back(), end()),
        ]
        done = {donate_alliance_key(n): "2026-10-02T08:00:00" for n in (1, 2)}
        device = _run(self, flow, settings, ctx_settings={"Event": settings}, daily_done=done)
        self.assertIn(donate_alliance_key(3), device.daily_done)
        self.assertIn(donate.KEY, device.daily_done)

    def test_donate_gem_limit(self):
        """Đã mua lại lượt đủ MAX_GEM_BUYS lần mà vẫn hết lượt: dừng, không đánh dấu xong."""
        flow = [
            Step("day2_teamwork.png", tap_at(335, 567)),
            Step("donate_gems.png", end()),
        ]
        with mock.patch.object(sys.modules["bot.activities.event.kings_path.donate.donating"],
                               "MAX_GEM_BUYS", 0):
            device = _run(self, flow, {donate.KEY: {"value": 60, "day": 2}})
        self.assertNotIn(donate.KEY, device.daily_done)

    def test_city_tax(self):
        """Day 1 City Tax (ảnh thật): dòng Go trên cùng 93 / 110, các dòng Claimed dồn xuống dưới
        -> Go -> bấm giữa thành -> icon Tax -> màn Tax: còn 17 / 4 = 4,25 -> mỗi dòng 5 -> mỗi
        dòng Tax -> popup gõ số -> Tax -> xong."""
        rows = [284, 383, 482, 581]
        flow = [
            Step("day1_city_tax_go.png", tap_at(335, 344)),
            Step("tax_city.png", tap_pct(50, 50)),
            Step("tax_menu.png", tap(TAX_MENU)),
        ]
        for y in rows:
            flow += [
                Step("tax_screen.png", tap_at(308, y)),
                Step("tax_popup.png", tap_at(198, 300)),
                Step("tax_input.png", tap_at(62, 300)),   # thanh nhập -> bấm chỗ trống cho mất
                Step("tax_popup.png", tap(POPUP_TAX)),
            ]
        flow.append(Step("tax_screen.png", end()))
        device = _run(self, flow, {city_tax.KEY: {"value": 110, "day": 1}})
        texts = [c for c in device.shells if c.startswith("input text")]
        self.assertIn("City Tax: done 93, target 110, tax [5, 5, 5, 5]", device.logs)
        self.assertEqual(texts, ["input text 5"] * 4)
        self.assertIn(city_tax.KEY, device.daily_done)

    def test_train_troop(self):
        """Day 3 -> tab Strong Troops (ảnh thật, tiến độ xuống 2 dòng "23,530 / 50,000") -> Go ->
        doanh trại -> menu Train -> màn Train: bấm vòng cấp I (sát mép trái) -> Train."""
        flow = [
            Step("day3_healing_heart.png", tap(f"{KP}/Tab/strongTroops.png")),
            Step("day3_strong_troops_go.png", tap_at(335, 344)),
            Step("train_after_go.png", tap_at(198, 352)),
            Step("train_menu.png", tap("Event/GatherTroops/Train/train.png")),
            Step("train_t01.png", tap("Event/GatherTroops/GroundTroop/Tier/1.png")),
            Step("train_t01.png", tap("Event/GatherTroops/Train/trainButton.png")),
        ]
        device = _run(self, flow, {train_troop.KEY: {"value": 50000, "day": 3}})
        # Tiến độ xuống 2 dòng "23,530 /" + "50,000" -> đã làm 23530, còn 26470 / 1580 = 17 mẻ.
        self.assertIn("Train Troop: done 23530, remaining 26470", device.logs)
        self.assertIn("Train Troop: 1580 per batch -> 17 batch(es)", device.logs)

    def test_city_tax_open_tab(self):
        """Day 1 đang mở tab Hoarding: bấm tab City Tax (ảnh "chưa chọn") -> dòng Go 93 / 110 -> Go."""
        flow = [
            Step("day1_hoarding.png", tap(f"{KP}/Tab/cityTax.png")),
            Step("day1_city_tax_go.png", tap_at(335, 344)),   # sau Go: harness dừng bot
        ]
        device = _run(self, flow, {city_tax.KEY: {"value": 110, "day": 1}})
        self.assertIn("City Tax: done 93, target 110", device.logs)

    def test_train_first_tier_walks_down(self):
        """Doanh trại mở ở cấp cao (ảnh lính bộ cấp XIII .. V của test Ground Troop): bấm vòng trái nhất
        (nhảy ra giữa) để lùi dần XIII -> XI -> IX -> VII -> V -> III; thấy vòng cấp I (train_t01, I sát
        mép trái) thì bấm I, có nút "+" -> chọn cấp 1."""
        g = "../../gather_troops/ground_troop/screens/"
        flow = [
            Step(g + "train_t13.png", tap_at(27, 463)),   # XI
            Step(g + "train_t11.png", tap_at(24, 463)),   # IX
            Step(g + "train_t09.png", tap_at(23, 463)),   # VII
            Step(g + "train_t07.png", tap_at(22, 463)),   # V
            Step(g + "train_t05.png", tap_at(20, 463)),   # III
            Step("train_t01.png", tap_at(44, 463)),       # I
            Step("train_t01.png", end(1)),
        ]
        run_flow(self, lambda bot, _: choose_first_tier(bot, TRAIN_TIERS), SCREENS, flow, {})

    def test_split_counts(self):
        self.assertEqual(split_counts(110), [28] * 4)
        self.assertEqual(split_counts(90), [23] * 4)   # đã làm 20 / 110
        self.assertEqual(split_counts(3), [1] * 4)
        self.assertEqual(split_counts(0), [0, 0, 0, 0])

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

    def test_wheel(self):
        """Day 4 tab Accumulation -> tab Fortune Wheel -> Go trên cùng -> màn Wheel of
        Fortune -> bấm "100 Spins" một lần -> xong."""
        flow = [
            Step("day4_accumulation.png", tap(f"{KP}/Tab/fortuneWheel.png")),
            Step("day4_fortune_wheel.png", tap_at(335, 344)),
            Step("wheel_of_fortune.png", tap(SPINS_100), back(), end()),
        ]
        device = _run(self, flow, {wheel.KEY: {"value": 100, "day": 4}})
        self.assertIn(wheel.KEY, device.daily_done)

    def test_wheel_out_of_chips(self):
        """Chỉ có 10 Spins: bấm liên tục (kể cả khi bảng kết quả đang hiện) tới khi không đủ chip,
        game mở Purchase Chips -> Back, đánh dấu xong hôm nay (không dùng chip trong túi)."""
        flow = [
            Step("day4_fortune_wheel.png", tap_at(335, 344)),
            Step("wheel_10_only.png", tap(SPINS_10)),
            Step("wheel_result_10.png", tap(SPINS_10)),
            Step("wheel_chips_empty.png", back(), end()),
        ]
        device = _run(self, flow, {wheel.KEY: {"value": 100, "day": 4}})
        self.assertIn("Wheel: out of chips after 2 x 10 Spins, done for today", device.logs)
        self.assertIn(wheel.KEY, device.daily_done)

    def test_wheel_no_button(self):
        """Sau Go không thấy nút "100 Spins" (màn khác): không đánh dấu xong."""
        flow = [
            Step("day4_fortune_wheel.png", tap_at(335, 344)),
            Step("day4_accumulation.png", end()),
        ]
        device = _run(self, flow, {wheel.KEY: {"value": 100, "day": 4}})
        self.assertNotIn(wheel.KEY, device.daily_done)

    def test_yield_to_boss_after_task_done(self):
        """Đang chạy theo lịch ưu tiên boss: nhiệm vụ vừa xong (đủ mục tiêu ở dòng Go) -> nhường ngay
        để kiểm tra boss (YieldToBoss), không làm nhiệm vụ sau."""
        flow = [Step("day2_teamwork.png", end())]

        def setup(ctx):
            ctx._boss_interrupt_enabled = True

        with self.assertRaises(YieldToBoss):
            _run(self, flow, {patrol.KEY: {"value": 100, "day": 2},
                              donate.KEY: {"value": 60, "day": 2}}, setup=setup)

    def test_no_yield_outside_boss_window(self):
        """Không chạy theo lịch ưu tiên boss: nhiệm vụ xong thì làm tiếp bình thường."""
        flow = [Step("day2_teamwork.png", end())]
        device = _run(self, flow, {patrol.KEY: {"value": 100, "day": 2}})
        self.assertIn("Event: task kings_path_patrol done", device.logs)
        self.assertIn(patrol.KEY, device.daily_done)

    def test_heal_idle_hospital(self):
        """Heal: Go -> bấm giữa (Bệnh viện) -> menu có "Heal" -> màn Hospital (chọn hết) -> Reset ->
        cuộn xuống cuối 5 lần -> ô số dòng cuối (285, 465) -> thanh nhập: gõ 50000 - 0 -> OK -> Heal
        -> Speed Up -> Healing Speedup: Speedup Settings -> tích ô -> Confirm -> Finish All -> làm lại
        từ đầu (harness dừng bot)."""
        flow = [
            Step("day3_healing_heart.png", tap_at(335, 344)),
            Step("heal_city.png", tap_pct(50, 50)),
            Step("heal_menu.png", tap(HEAL_MENU_HEAL)),
            Step("heal_screen.png", tap(HEAL_RESET)),
            Step("heal_screen_reset.png", *[swipe(50, 70, 50, 30) for _ in range(5)], tap_at(285, 465)),
            Step("heal_input.png", tap(HEAL_INPUT_OK)),
            Step("heal_screen_reset.png", tap(HEAL_BUTTON)),
            Step("heal_healing.png", tap(HEAL_SPEED_UP)),
            Step("heal_speedup.png", tap(TRAIN_SPEEDUP_SETTINGS)),
            Step("heal_finish_all.png", tap(TRAIN_CHECKBOX_OFF)),
            Step("heal_finish_all_ticked.png", tap(TRAIN_CONFIRM)),
            Step("heal_speedup.png", tap(TRAIN_FINISH_ALL)),   # -> AGAIN; harness dừng bot
        ]
        device = _run(self, flow, {heal.KEY: {"value": 50000, "day": 3}})
        self.assertIn("Heal: hospital idle, Heal (done 0, target 50000)", device.logs)
        self.assertIn("input text 50000", device.shells)

    def test_heal_no_wounded(self):
        """Hospital không còn lính bị thương ("Wounded Troops 0/0", không có dòng lính): Back, xong
        hôm nay."""
        flow = [
            Step("day3_healing_heart.png", tap_at(335, 344)),
            Step("heal_city.png", tap_pct(50, 50)),
            Step("heal_menu.png", tap(HEAL_MENU_HEAL)),
            Step("heal_empty.png", back(), end()),
        ]
        device = _run(self, flow, {heal.KEY: {"value": 50000, "day": 3}})
        self.assertIn("Heal: no wounded troops, done for today", device.logs)
        self.assertIn(heal.KEY, device.daily_done)

    def test_heal_menu_without_heal(self):
        """Menu Bệnh viện chỉ có Citizen / Detail / Upgrade (không có lính bị thương): Back, xong hôm
        nay."""
        flow = [
            Step("day3_healing_heart.png", tap_at(335, 344)),
            Step("heal_city.png", tap_pct(50, 50)),
            Step("heal_menu_empty.png", back(), end()),
        ]
        device = _run(self, flow, {heal.KEY: {"value": 50000, "day": 3}})
        self.assertIn("Heal: no wounded troops, done for today", device.logs)
        self.assertIn(heal.KEY, device.daily_done)

    def test_heal_busy_hospital_speed_up(self):
        """Heal: bệnh viện đang chữa dở -> menu có "Speed Up" -> Healing Speedup -> Finish All (như
        train lính) -> làm lại từ đầu (harness dừng bot)."""
        flow = [
            Step("day3_healing_heart.png", tap_at(335, 344)),
            Step("heal_city.png", tap_pct(50, 50)),
            Step("heal_menu_healing.png", tap(HEAL_MENU_SPEED_UP)),
            Step("heal_speedup.png", tap(TRAIN_SPEEDUP_SETTINGS)),
            Step("heal_finish_all.png", tap(TRAIN_CHECKBOX_OFF)),
            Step("heal_finish_all_ticked.png", tap(TRAIN_CONFIRM)),
            Step("heal_speedup.png", tap(TRAIN_FINISH_ALL)),   # -> AGAIN; harness dừng bot
        ]
        device = _run(self, flow, {heal.KEY: {"value": 50000, "day": 3}})
        self.assertIn("Heal: hospital busy, Speed Up", device.logs)

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

    def test_black_market_open_day5(self):
        """Black Market: đang ở Day 1 -> bấm Day 5 (đã mở) -> tab Market Trade đang chọn -> dòng Go
        trên cùng (0 / 1) -> Go (phần sau Go: TODO)."""
        flow = [
            Step("day1_day5_open.png", tap(f"{KP}/Day/day5.png")),
            Step("day5_market_trade.png", tap_at(335, 344)),   # sau Go: harness dừng bot
        ]
        device = _run(self, flow, {black_market.KEY: {"value": 100, "day": 5}})
        self.assertIn("Black Market: done 0, target 100", device.logs)

    def test_black_market_open_tab(self):
        """Day 5 đang mở tab War Horn: bấm tab Market Trade (ảnh "chưa chọn") -> Go."""
        flow = [
            Step("day5_war_horn.png", tap(f"{KP}/Tab/marketTrade.png")),
            Step("day5_market_trade.png", tap_at(335, 344)),   # sau Go: harness dừng bot
        ]
        _run(self, flow, {black_market.KEY: {"value": 100, "day": 5}})

    def test_black_market_buy(self):
        """Black Market (đã mua 0, mục tiêu 2): Go -> bấm giữa (Chợ) -> icon Black Market -> mua món 1
        -> Confirm -> món 2 -> Confirm -> đủ, Back, xong. Món trả kim cương (ô 3) không bấm."""
        flow = [
            Step("day5_market_trade.png", tap_at(335, 344)),
            Step("bm_city.png", tap_pct(50, 50)),
            Step("bm_menu.png", tap(BM_MENU)),
            Step("bm_screen.png", tap_at(*BM_SLOTS[0])),
            Step("bm_confirm.png", tap(BM_CONFIRM)),
            Step("bm_screen.png", tap_at(*BM_SLOTS[1])),
            Step("bm_confirm.png", tap(BM_CONFIRM)),
            Step("bm_bought.png", back(), end()),
        ]
        device = _run(self, flow, {black_market.KEY: {"value": 2, "day": 5}})
        self.assertIn("Black Market: bought 2 / 2, done", device.logs)
        self.assertIn(black_market.KEY, device.daily_done)

    def test_black_market_refresh_and_continue(self):
        """Mua hết bộ hàng (nút giá đều xám) -> Instant Refresh -> chờ 3 s -> bộ mới -> mua tiếp tới đủ."""
        flow = [
            Step("day5_market_trade.png", tap_at(335, 344)),
            Step("bm_city.png", tap_pct(50, 50)),
            Step("bm_menu.png", tap(BM_MENU)),
            Step("bm_screen.png?sold_out", tap(BM_REFRESH)),
            Step("bm_screen.png", tap_at(*BM_SLOTS[0])),
            Step("bm_confirm.png", tap(BM_CONFIRM)),
            Step("bm_bought.png", back(), end()),
        ]
        device = _run(self, flow, {black_market.KEY: {"value": 1, "day": 5}})
        self.assertIn("Black Market: all bought, Instant Refresh (0 / 1)", device.logs)
        self.assertIn(black_market.KEY, device.daily_done)

    def test_black_market_refresh_retry(self):
        """Bấm Refresh mà ô vật phẩm 1 vẫn y như trước (chờ 2 s + 10 lần x 1 s): bấm Refresh lại; lần
        này ô 1 đổi -> mua tiếp."""
        flow = [
            Step("day5_market_trade.png", tap_at(335, 344)),
            Step("bm_city.png", tap_pct(50, 50)),
            Step("bm_menu.png", tap(BM_MENU)),
            Step("bm_screen.png?sold_out", tap(BM_REFRESH)),
            Step("bm_screen.png?sold_out", tap(BM_REFRESH)),
            Step("bm_screen_2.png", tap_at(*BM_SLOTS[0])),
            Step("bm_confirm.png", tap(BM_CONFIRM)),
            Step("bm_bought.png", back(), end()),
        ]
        device = _run(self, flow, {black_market.KEY: {"value": 1, "day": 5}})
        self.assertIn("Black Market: items unchanged after 10 checks, Refresh again", device.logs)

    def test_black_market_gem_items_skipped(self):
        """Bộ hàng nhiều món trả kim cương (ảnh thật): chỉ bấm món trả tài nguyên (ô 2 — 100k Iron)."""
        flow = [
            Step("day5_market_trade.png", tap_at(335, 344)),
            Step("bm_city.png", tap_pct(50, 50)),
            Step("bm_menu.png", tap(BM_MENU)),
            Step("bm_screen_3.png", tap_at(*BM_SLOTS[1])),
            Step("bm_confirm.png", tap(BM_CONFIRM)),
            Step("bm_bought.png", back(), end()),
        ]
        _run(self, flow, {black_market.KEY: {"value": 1, "day": 5}})

    def test_black_market_buyable_slots(self):
        """Món mua được = nút giá xanh, không trả kim cương (7 mẫu thật, vị trí icon kim cương xê dịch
        theo độ dài số; ô đã mua xám)."""
        buyable = sys.modules["bot.activities.event.kings_path.black_market.run"]._buyable
        bot = SimpleNamespace(crop=BotContext.crop, find=lambda tpl, threshold, screen: (
            None if cv2.matchTemplate(screen, cv2.imread(str(TEMPLATE_DIR / tpl)), cv2.TM_CCOEFF_NORMED).max()
            < threshold else (0, 0)))
        expected = {
            "bm_screen.png": "110111", "bm_bought.png": "110110", "bm_screen_2.png": "110111",
            "bm_screen_3.png": "010000", "bm_refresh_gems.png": "001001", "bm_screen_4.png": "000001",
            "bm_screen_5.png": "000000", "bm_screen_6.png": "101000", "bm_screen_7.png": "001000",
        }
        for name, want in expected.items():
            screen = cv2.imread(str(SCREENS / name))
            got = "".join("1" if buyable(bot, screen, x, y) else "0" for x, y in BM_SLOTS)
            self.assertEqual(got, want, name)

    def test_black_market_paid_refresh(self):
        """Hết món, Instant Refresh bằng kim cương (nút "Instant Refresh 50"): vẫn bấm như bình thường;
        có hộp xác nhận thì Confirm (không tính là 1 lần mua)."""
        flow = [
            Step("day5_market_trade.png", tap_at(335, 344)),
            Step("bm_city.png", tap_pct(50, 50)),
            Step("bm_menu.png", tap(BM_MENU)),
            Step("bm_refresh_gems.png?sold_out", tap(BM_REFRESH)),
            Step("bm_confirm.png", tap(BM_CONFIRM)),
            Step("bm_screen.png", tap_at(*BM_SLOTS[0])),
            Step("bm_confirm.png", tap(BM_CONFIRM)),
            Step("bm_bought.png", back(), end()),
        ]
        device = _run(self, flow, {black_market.KEY: {"value": 1, "day": 5}})
        self.assertIn("Black Market: confirm paid refresh", device.logs)
        self.assertIn("Black Market: buy confirmed (1 / 1)", device.logs)

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
            run_flow(self, event.run, SCREENS, flow, {wheel.KEY: {"value": 100, "day": 4}})


if __name__ == "__main__":
    unittest.main()
