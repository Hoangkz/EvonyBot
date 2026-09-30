"""
Flow test "Join Monster War": từ màn hình chính tới lúc bấm nút Join, và
BossMemory (boss đã tham gia / bỏ qua) trên danh sách War
(xem .claude/skills/flow-test/flows.md và bot/activities/join_monster_war/FLOW.md).

Ảnh trong screens/ là ảnh chụp nguyên màn hình giả lập, cùng độ phân giải
bot chạy (REGIONS của Join Boss đo trên 396x704).
"""
import unittest
from pathlib import Path

import cv2

from bot.activities import join_monster_war
from bot.activities.join_monster_war.boss_memory import JOINED, SKIPPED, BossMemory
from bot.activities.join_monster_war.constants import IDLE, JOIN, LISTBOSS, REGIONS, WAR_TICKED
from bot.context import TEMPLATE_DIR
from tests.flow import Step, end, run_flow, swipe, tap, tap_at

SCREENS = Path(__file__).parent / "screens"
# Như tab thật: boss được tích nằm trong selected_bosses (boss thường không có cấp).
TICKED = ["Peryton", "Manticore", "Yasha", "Minotaur"]
SETTINGS = {"troop": ["Troop 1"], "use_stamina": "No",
            "selected_bosses": [{"category_key": "standard_bosses", "name": n, "levels": []}
                                for n in TICKED]}
IDLE_SETTINGS = {**SETTINGS, "exit_when_idle": True}

PERYTON = (649, 865)     # 02_war_list_join.png
MANTICORE = (633, 941)   # war_list_join_red.png
YASHA = (655, 997)       # war_list_attacking_join.png
MINOTAUR = (623, 935)    # war_list_two_join.png, war_list_more_below.png
BAYARD = (768, 975)      # war_list_long_name.png: Junior Knight Bayard (cấp 1), ô War đã bỏ tích (ảnh thật)
BAYARD_JUNIOR = (621, 919)   # war_senior_junior_bayard.png (thẻ dưới), war_joined_and_join.png
BAYARD_SENIOR = (592, 915)   # war_senior_junior_bayard.png (thẻ trên): "Senior Bayar Knight", cấp 2
GOLEM = (655, 875)           # war_scrolled_*.png: không có tier, lực 12.4M -> cấp 1


def war_off(screen):
    """ẢNH TỔNG HỢP: xoá dấu tích xanh của ô "War" (mọi ảnh chụp hiện có đều đang
    tích ô này, bot sẽ bấm bỏ tích trước tiên). Dùng cho các kịch bản không liên
    quan tới ô War; thay bằng ảnh chụp thật khi có."""
    h, w = screen.shape[:2]
    x0, y0, x1, y1 = REGIONS[WAR_TICKED]
    box = screen[int(h * y0 / 100):int(h * y1 / 100), int(w * x0 / 100):int(w * x1 / 100)]
    b, g, r = (box[..., i].astype(int) for i in range(3))
    box[(g > 150) & (r < 130) & (b < 100)] = (40, 40, 40)
    return screen


def W(screen):
    """Ảnh danh sách War với ô "War" đã bỏ tích (tổng hợp, xem war_off)."""
    return f"{screen}?war_off"


def run_join(testcase, flow, settings, **kwargs):
    return run_flow(testcase, join_monster_war.run, SCREENS, flow, settings,
                    variants={"war_off": war_off}, **kwargs)


def remember(coords, status):
    """setup cho run_flow: BossMemory của giả lập đã nhớ sẵn `coords`."""
    def setup(ctx):
        ctx.boss_memory = BossMemory()
        ctx.boss_memory.mark(coords, status)
    return setup


# Các kịch bản không có end(): dừng ngay sau action cuối (harness bật Stop).
BEFORE_JOIN = [
    # Màn hình chính, có icon danh sách boss (listboss.png) ở cột phải.
    Step("01_home_listboss.png", tap(LISTBOSS)),
    # Tab PvP War: một rally Peryton, nút Join chữ trắng.
    Step(W("02_war_list_join.png"), tap(JOIN)),
]

# Rally Manticore có nút Join chữ đỏ (chưa join được) -> bỏ qua. Danh sách chỉ có 1 thẻ
# (đã hiện hết) nên không cuộn: không còn boss nào để tham gia -> rảnh, không bấm gì.
SKIP_RED_JOIN = [
    Step(W("war_list_join_red.png"), end(IDLE)),
]

# Thẻ trên đang Attacking (không có Join), thẻ dưới Yasha có Join y = 562.
JOIN_BELOW_ATTACKING = [
    Step(W("war_list_attacking_join.png"), tap(JOIN)),
]

# Hai rally cùng một boss Minotaur, cả hai Join chữ trắng -> tap một Join.
TWO_JOIN_SAME_BOSS = [
    Step(W("war_list_two_join.png"), tap(JOIN)),
]

# Trên 3 rally: 2 thẻ Minotaur có Join, thẻ thứ 3 bị che ở đáy màn hình.
MORE_BELOW = [
    Step(W("war_list_more_below.png"), tap(JOIN)),
]

# Màn hình chính có nút Alliance nhưng không có icon listboss -> không có boss để
# join: không bấm gì, trả IDLE để worker làm activity khác (exit_when_idle).
NO_BOSS = [
    Step("home_no_boss.png", end(IDLE)),
]

# Có listboss nhưng tab PvP War trống (không có Join / Joined) -> rảnh, trả IDLE.
EMPTY_WAR_LIST = [
    Step("01_home_listboss.png", tap(LISTBOSS)),
    Step(W("war_list_empty.png"), end(IDLE)),
]

# Peryton không được tích ở tab -> OCR tên, không Join, nhớ là không tham gia -> rảnh.
NOT_TICKED_PERYTON = [
    Step(W("02_war_list_join.png"), end(IDLE)),
]

# Boss trên màn hình đã có trong BossMemory -> không Join. Danh sách đã hiện hết -> rảnh.
ALREADY_KNOWN_PERYTON = [
    Step(W("02_war_list_join.png"), end(IDLE)),
]
ALREADY_KNOWN_MINOTAUR = [
    Step(W("war_list_two_join.png"), end(IDLE)),
]
# Còn thẻ bị che ở đáy màn hình -> vẫn phải cuộn xuống tìm rally khác.
ALREADY_KNOWN_MORE_BELOW = [
    Step(W("war_list_more_below.png"), swipe(50, 65, 50, 40)),
]

# Mỗi chu kỳ cuộn 3 lần xuống rồi 3 lần lên; hết 6 lần mà không thấy boss mới -> rảnh.
DOWN, UP = swipe(50, 65, 50, 40), swipe(50, 40, 50, 65)
SCROLL_LIMIT = [
    *[Step(W("war_list_more_below.png"), DOWN) for _ in range(3)],
    *[Step(W("war_list_more_below.png"), UP) for _ in range(3)],
    Step(W("war_list_more_below.png"), end(IDLE)),
]

# Sau 2 lần cuộn thấy Yasha (boss mới, không được tích) -> đếm lại từ đầu, nên cần
# thêm 6 lần cuộn nữa (tổng 8) mới rảnh; chu kỳ xuống/lên vẫn chạy tiếp.
NEW_BOSS_RESETS_SCROLLS = [
    Step(W("war_list_more_below.png"), DOWN),
    Step(W("war_list_more_below.png"), DOWN),
    Step(W("war_list_attacking_join.png"), DOWN),   # Yasha mới -> đếm lại: lần 1 (xuống thứ 3)
    Step(W("war_list_attacking_join.png"), UP),     # lần 2
    Step(W("war_list_attacking_join.png"), UP),     # lần 3
    Step(W("war_list_attacking_join.png"), UP),     # lần 4 (về đầu danh sách)
    Step(W("war_list_attacking_join.png"), DOWN),   # lần 5 (danh sách chưa hiện hết -> cuộn tiếp)
    Step(W("war_list_attacking_join.png"), DOWN),   # lần 6
    Step(W("war_list_attacking_join.png"), end(IDLE)),
]


# Ô "War" đang tích (ảnh thật) -> bấm bỏ tích trước khi xét boss.
# Tâm ô "War" trên 396x704. Dùng tap_at (không dùng tap(WAR_TICKED)) vì ô "Monster War"
# cũng khớp ảnh mẫu 0.92: test phải bắt được nếu bot bấm nhầm ô đó.
WAR_CHECKBOX_CENTER = (201, 118)
UNTICK_WAR = [
    Step("02_war_list_join.png", tap_at(*WAR_CHECKBOX_CENTER, tol=8)),
    Step(W("02_war_list_join.png"), tap(JOIN)),
]
# Danh sách trống nhưng ô War đang tích -> bỏ tích trước, rồi mới rảnh.
UNTICK_WAR_EMPTY = [
    Step("war_list_empty.png", tap_at(*WAR_CHECKBOX_CENTER, tol=8)),
    Step(W("war_list_empty.png"), end(IDLE)),
]
# Màn hình chính cũng có màu xanh ở vùng đó? Không bấm: chỉ xét ô War trên danh sách War.
HOME_NOT_WAR_LIST = [
    Step("01_home_listboss.png", tap(LISTBOSS)),
    Step(W("02_war_list_join.png"), tap(JOIN)),
]


# Ảnh thật, ô War đã bỏ tích: không bấm ô War; tier "Junior" -> Knight Bayard cấp 1.
JOIN_TIER_BOSS = [
    Step("war_list_long_name.png", tap(JOIN)),
]
SKIP_TIER_NOT_TICKED = [
    Step("war_list_long_name.png", end(IDLE)),
]


def with_bayard(levels):
    return {**SETTINGS, "selected_bosses": SETTINGS["selected_bosses"] + [
        {"category_key": "special_and_recurring_event_bosses", "name": "Knight Bayard", "levels": levels}]}


def with_golem(levels):
    return {**SETTINGS, "selected_bosses": SETTINGS["selected_bosses"] + [
        {"category_key": "special_and_recurring_event_bosses", "name": "Golem", "levels": levels}]}


# Hai thẻ Knight Bayard: Senior (cấp 2, thẻ trên) và Junior (cấp 1, thẻ dưới). Ảnh thật
# đang tích ô War -> bấm bỏ tích trước. Chỉ tích cấp 2 -> Junior bị bỏ qua, Join Senior.
SENIOR_ONLY = [
    Step("war_senior_junior_bayard.png", tap_at(201, 118, tol=8)),
    Step(W("war_senior_junior_bayard.png"), tap(JOIN)),
]
# Thẻ trên đã "Joined", thẻ dưới Junior có Join -> Join Junior, không bấm nút Joined.
JOINED_AND_JOIN = [
    Step(W("war_joined_and_join.png"), tap_at(335, 569, tol=8)),
]
# Cả hai thẻ đều "Joined", ô War bị thanh thông báo che (không thấy -> không bấm):
# không có gì để Join, danh sách còn dài -> cuộn xuống.
ALL_JOINED = [
    Step("war_all_joined.png", swipe(50, 65, 50, 40)),
]
# Danh sách đã cuộn: thẻ trên cùng bị cắt (nút "Joined" ở y 370 khớp ảnh mẫu Join 0,80 ->
# phải bị loại), Golem ở y 597 -> Join Golem.
SCROLLED_JOIN_GOLEM = [
    Step(W("war_scrolled_join_cut_top.png"), tap_at(335, 604, tol=8)),
]
# Ảnh thật, ô War đã bỏ tích; hai thẻ đều "Joined" và danh sách đã hiện hết -> rảnh,
# không bấm gì (không bấm ô War, không cuộn).
ALL_JOINED_SHORT_LIST = [
    Step("war_epic_cerberus_skeleton.png", end(IDLE)),
]
# Cuối một danh sách dài: thẻ cuối sát nút Battle Logs (không có khoảng trống), mọi boss
# đã biết -> không được rảnh ngay, vẫn cuộn theo vòng 3 xuống / 3 lên.
BOTTOM_OF_LONG_LIST = [
    Step(W("war_list_bottom.png"), swipe(50, 65, 50, 40)),
]
# Nút Join của Golem bị cắt ở mép dưới (ngoài dải 262-615) -> chỉ còn Joined -> cuộn.
JOIN_CUT_AT_BOTTOM = [
    Step(W("war_scrolled_join_cut_bottom.png"), swipe(50, 65, 50, 40)),
]


class JoinMonsterWarFlow(unittest.TestCase):
    def test_join_boss_by_tier_level(self):
        device = run_join(self, JOIN_TIER_BOSS, with_bayard([1]))
        self.assertEqual(device.reported, [BAYARD])
        self.assertNotIn("Bỏ tích ô War (chỉ giữ rally đánh boss)", device.logs)
        self.assertIn("Boss (768, 975): 'junior knight bayard' -> Knight Bayard lv 1: join", device.logs)

    def test_senior_ticked_junior_not(self):
        device = run_join(self, SENIOR_ONLY, with_bayard([2]))
        self.assertEqual(device.reported, [BAYARD_SENIOR])
        with device.fake_time():
            self.assertEqual(device.ctx.boss_memory.status(BAYARD_JUNIOR), SKIPPED)

    def test_joined_button_is_not_tapped(self):
        device = run_join(self, JOINED_AND_JOIN, with_bayard([1]))
        self.assertEqual(device.reported, [BAYARD_JUNIOR])

    def test_all_joined_scrolls(self):
        device = run_join(self, ALL_JOINED, SETTINGS)
        self.assertEqual(device.reported, [])
        self.assertNotIn("Bỏ tích ô War (chỉ giữ rally đánh boss)", device.logs)

    def test_scrolled_list_joins_golem_not_joined_button(self):
        device = run_join(self, SCROLLED_JOIN_GOLEM, with_golem([1]))
        self.assertEqual(device.reported, [GOLEM])

    def test_all_joined_short_list_idles(self):
        device = run_join(self, ALL_JOINED_SHORT_LIST, IDLE_SETTINGS)
        self.assertEqual(device.events, [])
        self.assertEqual(device.reported, [])

    def test_bottom_of_long_list_keeps_scrolling(self):
        device = run_join(self, BOTTOM_OF_LONG_LIST, with_bayard([2]),
                          setup=remember(BAYARD_SENIOR, JOINED))
        self.assertEqual(device.reported, [])

    def test_join_cut_at_bottom_is_ignored(self):
        device = run_join(self, JOIN_CUT_AT_BOTTOM, with_golem([1]))
        self.assertEqual(device.reported, [])

    def test_skip_boss_when_tier_level_not_ticked(self):
        device = run_join(self, SKIP_TIER_NOT_TICKED, {**with_bayard([2, 3]), "exit_when_idle": True})
        self.assertEqual(device.reported, [])
        with device.fake_time():
            self.assertEqual(device.ctx.boss_memory.status(BAYARD), SKIPPED)

    def test_war_ticked_template_on_real_crops(self):
        # Ảnh chụp thật ô "War": còn tích -> khớp; đã bỏ tích -> không khớp (ngưỡng 0.9).
        tpl = cv2.imread(str(TEMPLATE_DIR / WAR_TICKED))
        scores = {}
        for name in ("war_checkbox_on.png", "war_checkbox_off.png"):
            crop = cv2.imread(str(SCREENS / name))
            if crop is None:
                self.skipTest(f"thiếu ảnh {name}")
            crop = cv2.copyMakeBorder(crop, 6, 6, 6, 6, cv2.BORDER_REPLICATE)
            scores[name] = cv2.matchTemplate(crop, tpl, cv2.TM_CCOEFF_NORMED).max()
        self.assertGreater(scores["war_checkbox_on.png"], 0.95)
        self.assertLess(scores["war_checkbox_off.png"], 0.8)

    def test_untick_war_before_joining(self):
        device = run_join(self, UNTICK_WAR, SETTINGS)
        self.assertEqual(device.reported, [PERYTON])
        self.assertIn("Bỏ tích ô War (chỉ giữ rally đánh boss)", device.logs)

    def test_untick_war_on_empty_list(self):
        run_join(self, UNTICK_WAR_EMPTY, IDLE_SETTINGS)

    def test_home_screen_is_not_war_list(self):
        run_join(self, HOME_NOT_WAR_LIST, SETTINGS)

    def test_home_to_join(self):
        device = run_join(self, BEFORE_JOIN, SETTINGS)
        # Báo boss cho các giả lập cùng server đúng 1 lần, ngay trước khi tap Join,
        # với toạ độ boss đọc bằng OCR.
        self.assertEqual(device.reported, [PERYTON])
        # Mới tap Join, chưa hành quân -> chưa được nhớ là đã tham gia.
        with device.fake_time():
            self.assertIsNone(device.ctx.boss_memory.status(PERYTON))

    def test_skip_red_join(self):
        device = run_join(self, SKIP_RED_JOIN, IDLE_SETTINGS)
        self.assertEqual(device.reported, [])
        self.assertEqual(device.events, [])     # không bấm, không cuộn
        with device.fake_time():
            self.assertEqual(device.ctx.boss_memory.status(MANTICORE), SKIPPED)
        # Không còn chờ wait_gone 10 giây mỗi lượt (trước đây ~82 giây).
        self.assertLess(device.clock.now - 1000, 2)

    def test_join_below_attacking(self):
        device = run_join(self, JOIN_BELOW_ATTACKING, SETTINGS)
        self.assertEqual(device.reported, [YASHA])

    def test_two_join_same_boss(self):
        device = run_join(self, TWO_JOIN_SAME_BOSS, SETTINGS)
        self.assertEqual(device.reported, [MINOTAUR])

    def test_join_with_more_below(self):
        device = run_join(self, MORE_BELOW, SETTINGS)
        self.assertEqual(device.reported, [MINOTAUR])

    def test_no_boss_returns_idle(self):
        device = run_join(self, NO_BOSS, IDLE_SETTINGS)
        self.assertEqual(device.events, [])
        self.assertEqual(device.reported, [])

    def test_empty_war_list_returns_idle(self):
        device = run_join(self, EMPTY_WAR_LIST, IDLE_SETTINGS)
        self.assertEqual(device.reported, [])

    def test_boss_not_ticked_is_skipped(self):
        settings = {**SETTINGS, "selected_bosses": [
            b for b in SETTINGS["selected_bosses"] if b["name"] != "Peryton"]}
        device = run_join(self, NOT_TICKED_PERYTON,
                          {**settings, "exit_when_idle": True})
        self.assertEqual(device.reported, [])
        with device.fake_time():
            self.assertEqual(device.ctx.boss_memory.status(PERYTON), SKIPPED)

    def test_ticked_boss_name_is_read(self):
        device = run_join(self, JOIN_BELOW_ATTACKING, SETTINGS)
        self.assertIn("Boss (655, 997): '(boss) yasha' -> Yasha: join", device.logs)

    # ---- BossMemory ------------------------------------------------------
    def test_joined_boss_is_not_joined_again(self):
        device = run_join(self, ALREADY_KNOWN_PERYTON, IDLE_SETTINGS,
                          setup=remember(PERYTON, JOINED))
        self.assertEqual(device.reported, [])

    def test_skipped_boss_is_not_checked_again(self):
        device = run_join(self, ALREADY_KNOWN_PERYTON, IDLE_SETTINGS,
                          setup=remember(PERYTON, SKIPPED))
        self.assertEqual(device.reported, [])

    def test_joined_boss_skips_every_rally_on_it(self):
        # Hai rally cùng toạ độ Minotaur: đã tham gia một thì bỏ qua cả hai.
        device = run_join(self, ALREADY_KNOWN_MINOTAUR, IDLE_SETTINGS,
                          setup=remember(MINOTAUR, JOINED))
        self.assertEqual(device.reported, [])

    def test_scrolls_three_down_three_up_then_idle(self):
        device = run_join(self, SCROLL_LIMIT, IDLE_SETTINGS,
                          setup=remember(MINOTAUR, JOINED))
        self.assertEqual(device.reported, [])

    def test_new_boss_resets_scroll_count(self):
        settings = {**IDLE_SETTINGS, "selected_bosses": [
            b for b in SETTINGS["selected_bosses"] if b["name"] != "Yasha"]}
        device = run_join(self, NEW_BOSS_RESETS_SCROLLS, settings,
                          setup=remember(MINOTAUR, JOINED))
        self.assertEqual(device.reported, [])
        with device.fake_time():
            self.assertEqual(device.ctx.boss_memory.status(YASHA), SKIPPED)

    def test_all_known_but_list_continues_scrolls(self):
        device = run_join(self, ALREADY_KNOWN_MORE_BELOW, SETTINGS,
                          setup=remember(MINOTAUR, JOINED))
        self.assertEqual(device.reported, [])

    def test_other_boss_in_memory_does_not_block(self):
        device = run_join(self, TWO_JOIN_SAME_BOSS, SETTINGS,
                          setup=remember(PERYTON, JOINED))
        self.assertEqual(device.reported, [MINOTAUR])


if __name__ == "__main__":
    unittest.main()
