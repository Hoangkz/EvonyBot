"""
Flow test "Join Monster War": từ màn hình chính tới lúc bấm nút Join, và
BossMemory (boss đã tham gia / bỏ qua) trên danh sách War
(xem .claude/skills/flow-test/flows.md và bot/activities/join_monster_war/FLOW.md).

Ảnh trong screens/ là ảnh chụp nguyên màn hình giả lập, cùng độ phân giải
bot chạy (REGIONS của Join Boss đo trên 396x704).
"""
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import cv2
import numpy as np

from bot.activities import join_monster_war
from bot.activities.join_monster_war.boss_memory import JOINED, SKIPPED, BossMemory
from bot.activities.join_monster_war.constants import (CHOOSE_DEVELOPMENT, FAVORITE_OFF, IDLE, JOIN, JOINED_BUTTON, LISTBOSS, MARCH,
                                                     NOT_ENOUGH_STAMINA, PRESET_DX, PRESET_X0, PRESET_Y,
                                                     REGIONS, SELECT_GENERAL, STAMINA_SLIDER_END,
                                                     STAMINA_USE, WAR_TICKED)
from bot.activities.join_monster_war.run import _Boss, _is_green_button
from bot.context import TEMPLATE_DIR, BotContext
from tests.flow import Step, back, end, run_flow, swipe, tap, tap_at, tap_pct

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
BAYARD_LEGENDARY = (417, 585)   # war_legendary_cerberus_bayar.png (thẻ dưới): "Legendary Bayar Knight", cấp 4
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


def no_items(screen):
    """ẢNH TỔNG HỢP: xoá cột nút "Use ( N )" của màn Use Item (không còn vật phẩm thể lực).
    Thay bằng ảnh chụp thật khi có."""
    screen[300:, 255:370] = (20, 20, 20)
    return screen


def unknown(screen):
    """ẢNH TỔNG HỢP: màn hình không ảnh mẫu nào khớp (nhiễu), như hiệu ứng tạm sau khi bấm
    Join. (Làm tối ảnh thật không đủ: so khớp ảnh mẫu không phụ thuộc độ sáng.)"""
    screen[:] = np.random.default_rng(0).integers(0, 255, screen.shape, dtype=np.uint8)
    return screen


def run_join(testcase, flow, settings, **kwargs):
    return run_flow(testcase, join_monster_war.run, SCREENS, flow, settings,
                    variants={"war_off": war_off, "no_items": no_items, "unknown": unknown}, **kwargs)


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

# Bấm Join Peryton -> thông báo "You cannot send more troops." (hết đội quân), vẫn ở danh sách.
# Không bỏ qua: lượt sau xét lại chính nút đó, thời gian không đỏ -> bấm Join lại.
CANNOT_SEND_MORE = "war_cannot_send_more_troops.png"
PERYTON_2 = (731, 917)   # Peryton trên ảnh này
JOIN_AGAIN_AFTER_CANNOT_SEND = [
    Step(CANNOT_SEND_MORE, tap(JOIN)),
    Step(CANNOT_SEND_MORE, tap(JOIN)),
    Step(CANNOT_SEND_MORE, tap(JOIN)),
]
# Aglaope (thẻ trên, được tích) bấm Join mà không vào được màn March: không tính là đã xử lý,
# không cuộn tìm boss khác, bấm lại chính nút Join đó.
AGLAOPE = (673, 850)
JOIN_AGAIN_AGLAOPE = [
    Step("war_aglaope_join.png", tap(JOIN)),
    Step("war_aglaope_join.png", tap(JOIN)),
    Step("war_aglaope_join.png", tap(JOIN)),
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

# Boss không được tích không kéo dài vòng quét vô hạn: vẫn hoàn thành chu kỳ 3 xuống / 3 lên.
UNWANTED_BOSS_DOES_NOT_RESET_SCROLLS = [
    Step(W("war_list_more_below.png"), DOWN),
    Step(W("war_list_more_below.png"), DOWN),
    Step(W("war_list_attacking_join.png"), DOWN),
    Step(W("war_list_attacking_join.png"), UP),
    Step(W("war_list_attacking_join.png"), UP),
    Step(W("war_list_attacking_join.png"), UP),
    Step(W("war_list_attacking_join.png"), end(IDLE)),
]

LEGACY_SKIPPED_RECHECK = [
    Step(W("02_war_list_join.png"), tap(JOIN)),
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
# Ảnh thật, ô War đã bỏ tích: thẻ trên Legendary Cerberus đang Attacking (không có Join),
# thẻ dưới Legendary Bayar Knight (tên xuống 2 dòng) -> Knight Bayard cấp 4.
JOIN_LEGENDARY_BOSS = [
    Step("war_legendary_cerberus_bayar.png", tap(JOIN)),
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
# ---- Màn March (march_preset_2_unlocked.png: ô 1-2 mở, 3-8 khoá; đội đang chọn có tướng chính)
def preset(troop):
    """Bấm ô preset `troop` ở hàng trên cùng màn March."""
    return tap_pct(PRESET_X0 + (troop - 1) * PRESET_DX, PRESET_Y, tol=8)


MARCH_SCREEN = "march_preset_2_unlocked.png"
ALL_TROOPS = {**IDLE_SETTINGS, "troop": [f"Troop {i}" for i in range(1, 9)]}

# Join Peryton -> màn March: chọn đội 1 (có tướng chính) -> March -> màn March đóng
# (quay về danh sách) -> nhớ Peryton là đã tham gia -> không còn boss mới -> rảnh.
JOIN_AND_MARCH = [
    Step(W("02_war_list_join.png"), tap(JOIN)),
    Step(MARCH_SCREEN, preset(1)),
    Step(MARCH_SCREEN, tap(MARCH)),
    Step(W("war_after_march_joined.png"), end(IDLE)),
]
# Người dùng chỉ chọn đội 3, 4 nhưng các ô đó đang khoá -> không đội nào dùng được -> Back.
MARCH_ONLY_LOCKED = [
    Step(MARCH_SCREEN, back()),
]


# Chọn tướng phụ (tab tích "Select General" + "With Assistant General"): đội 1 đã có tướng
# chính, ô tướng phụ trống ("+") -> bấm "+" -> màn Select a General: trái tim lọc chưa tích
# -> bấm tích -> bấm Select tướng đầu tiên -> về màn March, ô tướng phụ đã có tướng -> March.
WITH_GENERALS = {**ALL_TROOPS, "select_general": True, "select_assistant_general": True}
CHOOSE_ASSISTANT = [
    Step("march_main_general_chosen.png", preset(1)),
    Step("march_main_general_chosen.png", tap(SELECT_GENERAL)),
    Step("select_general_fav_off.png", tap(FAVORITE_OFF)),
    Step("select_general_fav_on.png", tap_at(329, 373, tol=8)),
    Step("march_preset_2_unlocked.png", tap(MARCH)),
    Step("war_epic_cerberus_skeleton.png", end(IDLE)),
]
# Trái tim lọc đã tích sẵn -> không bấm lại, bấm luôn Select.
CHOOSE_ASSISTANT_FAV_ALREADY_ON = [
    Step("march_main_general_chosen.png", preset(1)),
    Step("march_main_general_chosen.png", tap(SELECT_GENERAL)),
    Step("select_general_fav_on.png", tap_at(329, 373, tol=8)),
    Step("march_preset_2_unlocked.png", tap(MARCH)),
]
# Tích "Development General": màn Select a General -> bấm tab Development (cái búa) trước
# rồi mới tích trái tim lọc và Select. (Ảnh sau khi bấm búa dùng lại ảnh tab All.)
CHOOSE_ASSISTANT_DEVELOPMENT = [
    Step("march_main_general_chosen.png", preset(1)),
    Step("march_main_general_chosen.png", tap(SELECT_GENERAL)),
    Step("select_general_fav_off.png", tap(CHOOSE_DEVELOPMENT)),
    Step("select_general_fav_off.png", tap(FAVORITE_OFF)),
    Step("select_general_fav_on.png", tap_at(329, 373, tol=8)),
    Step("march_preset_2_unlocked.png", tap(MARCH)),
]
# Màn chọn tướng phụ: King Arthur (tướng chính) có nút Select XÁM, không chọn được ->
# bỏ qua, bấm Select của Hudson (tướng đầu tiên có nút xanh).
CHOOSE_ASSISTANT_SKIP_MAIN = [
    Step("march_main_general_chosen.png", preset(1)),
    Step("march_main_general_chosen.png", tap(SELECT_GENERAL)),
    Step("select_assistant_main_disabled.png", tap(FAVORITE_OFF)),
    Step("select_assistant_main_disabled.png", tap_at(329, 627, tol=8)),
    Step("march_preset_2_unlocked.png", tap(MARCH)),
]
# Màn chọn tướng phụ nhưng không còn tướng yêu thích nào ("No favorite General", tim đã
# tích) -> Back về màn March -> vẫn March với tướng chính, không có tướng phụ.
ASSISTANT_NO_FAVORITE = [
    Step("march_main_general_chosen.png", preset(1)),
    Step("march_main_general_chosen.png", tap(SELECT_GENERAL)),
    Step("select_general_no_favorite.png", back()),
    Step("march_main_general_chosen.png", tap(MARCH)),
]
# march_no_main_general.png: ô Main General trống (dấu "+"), rally đang "Attacking".
NO_MAIN = "march_no_main_general.png"
# Đội 1 không có tướng chính -> thử đội 2 (có tướng chính) -> dùng đội 2.
SKIP_TROOP_WITHOUT_GENERAL = [
    Step(NO_MAIN, preset(1)),
    Step(NO_MAIN, preset(2)),
    Step(MARCH_SCREEN, tap(MARCH)),
]
# Đội 1, 2 đều không có tướng chính, tích "Select General" -> bấm "+" ô Main General ->
# Select tướng đầu tiên -> về màn March, ô đã có tướng -> March.
CHOOSE_MAIN_GENERAL = [
    Step(NO_MAIN, preset(1)),
    Step(NO_MAIN, preset(2)),
    Step(NO_MAIN, tap(SELECT_GENERAL)),
    Step("select_general_fav_on.png", tap_at(329, 373, tol=8)),
    Step("march_main_general_chosen.png", tap(MARCH)),
]
# Chọn tướng chính không được (không có tướng yêu thích) -> Back -> vẫn tham gia boss (March).
NO_MAIN_GENERAL_STILL_MARCH = [
    Step(NO_MAIN, preset(1)),
    Step(NO_MAIN, preset(2)),
    Step(NO_MAIN, tap(SELECT_GENERAL)),
    Step("select_general_no_favorite.png", back()),
    Step(NO_MAIN, tap(MARCH)),
]
# Không tích "Select General" -> không chọn tướng, vẫn March với đội thử cuối (đội 2).
NO_MAIN_GENERAL_MARCH = [
    Step(NO_MAIN, preset(1)),
    Step(NO_MAIN, preset(2)),
    Step(NO_MAIN, tap(MARCH)),
]
# Ảnh thật trước / sau khi bấm March (đủ thể lực): màn March (đội có tướng chính và tướng phụ)
# -> March -> quay về danh sách War, thẻ Manticore đã "Joined", ô War đang tích -> bỏ tích ->
# chỉ còn thẻ Joined, danh sách đã hiện hết -> rảnh.
MARCH_THEN_BACK_TO_LIST = [
    Step("march_ready.png", preset(1)),
    Step("march_ready.png", tap(MARCH)),
    Step("war_after_march_joined.png", tap_at(201, 118, tol=8)),
    Step(W("war_after_march_joined.png"), end(IDLE)),
]
# Bấm March mà không đủ thể lực -> popup "Get more now?" (Cancel / Confirm).
# use_stamina = No -> dừng hẳn Join Boss (trả None); ALL / 100 -> bấm Confirm để lấy thể lực.
STAMINA_POPUP = "march_not_enough_stamina.png"
NO_STAMINA_STOP = [
    Step(W("02_war_list_join.png"), tap(JOIN)),
    Step(MARCH_SCREEN, preset(1)),
    Step(MARCH_SCREEN, tap(MARCH)),
    Step(STAMINA_POPUP, end(None)),
]
NO_STAMINA_CONFIRM = [
    Step(MARCH_SCREEN, preset(1)),
    Step(MARCH_SCREEN, tap(MARCH)),
    Step(STAMINA_POPUP, tap(NOT_ENOUGH_STAMINA)),
]
# Dùng vật phẩm thể lực: Confirm -> màn Use Item: bấm Use đầu tiên -> popup số lượng
# (100: Use luôn; ALL: bấm cuối thanh trượt rồi Use) -> chờ 5 s, Back -> màn March -> March lại.
def refill(slider_step):
    return [
        Step(W("02_war_list_join.png"), tap(JOIN)),
        Step(MARCH_SCREEN, preset(1)),
        Step(MARCH_SCREEN, tap(MARCH)),
        Step(STAMINA_POPUP, tap(NOT_ENOUGH_STAMINA)),
        Step("stamina_use_item_list.png", tap_at(292, 360, tol=8)),   # Use ( 90 ) của vật phẩm đầu
        *slider_step,
        Step("stamina_after_use.png", back()),       # bấm Use xong: về danh sách Use Item -> sau 5 s Back
        Step("march_after_refill.png", tap(MARCH)),   # về màn March, thể lực 101/20 -> March lại
        Step("war_epic_cerberus_skeleton.png", end(IDLE)),            # đã hành quân, không còn boss mới
    ]


# Hết vật phẩm thể lực: màn Use Item không còn nút Use -> Back 2 lần -> không dừng (thể lực
# tự hồi): nhớ boss là đã tham gia và coi như rảnh (trả IDLE khi còn activity khác).
OUT_OF_STAMINA_ITEMS = [
    Step(W("02_war_list_join.png"), tap(JOIN)),
    Step(MARCH_SCREEN, preset(1)),
    Step(MARCH_SCREEN, tap(MARCH)),
    Step(STAMINA_POPUP, tap(NOT_ENOUGH_STAMINA)),
    Step("stamina_after_use.png?no_items", back(2)),
    Step(W("war_after_march_joined.png"), end(IDLE)),
]
REFILL_100 = refill([Step("stamina_use_popup_100.png", tap(STAMINA_USE))])   # mặc định 10/87 (= 100)
REFILL_ALL = refill([Step("stamina_use_popup.png", tap_pct(*STAMINA_SLIDER_END, tol=8)),
                     Step("stamina_use_popup_all.png", tap(STAMINA_USE))])
# Tướng phụ đã có sẵn -> không chọn gì thêm, March luôn.
ASSISTANT_ALREADY_THERE = [
    Step(MARCH_SCREEN, preset(1)),
    Step(MARCH_SCREEN, tap(MARCH)),
]


# Ảnh thật, ô War đã bỏ tích; hai thẻ đều "Joined" và danh sách đã hiện hết -> rảnh,
# không bấm gì (không bấm ô War, không cuộn).
ALL_JOINED_SHORT_LIST = [
    Step("war_epic_cerberus_skeleton.png", end(IDLE)),
]
# Danh sách đã cuộn: thẻ trên cùng (Medium Cerberus) có Join nhưng ngoài dải hợp lệ (y ~235),
# các thẻ còn lại đang "Attacking" -> không thấy Join / Joined nào nhưng danh sách chưa hết ->
# cuộn tiếp, không được rảnh.
SCROLLED_ONLY_ATTACKING = [
    Step("war_scrolled_only_attacking.png", swipe(50, 65, 50, 40)),
]
# 2 thẻ đều "Attacking" (không Join / Joined), có khoảng hở nhỏ ngay trên 2 nút xanh cuối
# (Battle Logs / Auto-Join) = danh sách đã hiện hết -> rảnh ngay, không cuộn.
TWO_ATTACKING_LIST_END = [
    Step("war_two_attacking_list_end.png", end(IDLE)),
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
    def test_four_rallies_two_unwanted_still_joins_wanted(self):
        """Hai boss không chọn ở đầu danh sách không được chặn boss hợp lệ phía dưới."""
        points = [(319, 300), (319, 380), (319, 460), (319, 540)]

        class FakeBot:
            def __init__(self):
                self.boss_memory = BossMemory()
                self.reported = []
                self.taps = []

            def template_size(self, _):
                return 20, 14

            def find_all(self, template, **_):
                return list(points) if template == JOIN else []

            def crop(self, image, *_):
                return image

            def find(self, *_args, **_kwargs):
                return None

            def report_boss(self, coords):
                self.reported.append(coords)

            def tap(self, x, y):
                self.taps.append((x, y))

            def log(self, _):
                pass

        bot = FakeBot()
        boss = _Boss(bot, SETTINGS)
        boss._boss_is_wanted = mock.Mock(side_effect=[False, False, True])
        boss._join_text_is_red = mock.Mock(return_value=False)

        self.assertTrue(boss._join(np.zeros((704, 396, 3), dtype=np.uint8)))
        self.assertEqual(boss.screen_blacklist, points[:2])
        self.assertEqual(bot.taps, [(329, 467)])
        self.assertEqual(bot.reported, [None])

    def test_join_boss_by_tier_level(self):
        device = run_join(self, JOIN_TIER_BOSS, with_bayard([1]))
        self.assertEqual(device.reported, [BAYARD])
        self.assertNotIn("Bỏ tích ô War (chỉ giữ rally đánh boss)", device.logs)
        self.assertIn("Boss (768, 975): 'junior knight bayard' -> Knight Bayard lv 1: join", device.logs)

    def test_join_legendary_two_line_name(self):
        device = run_join(self, JOIN_LEGENDARY_BOSS, with_bayard([4]))
        self.assertEqual(device.reported, [BAYARD_LEGENDARY])
        self.assertIn("Boss (417, 585): 'legendary bayar knight' -> Knight Bayard lv 4: join", device.logs)

    def test_senior_ticked_junior_not(self):
        device = run_join(self, SENIOR_ONLY, with_bayard([2]))
        self.assertEqual(device.reported, [BAYARD_SENIOR])
        with device.fake_time():
            self.assertIsNone(device.ctx.boss_memory.status(BAYARD_JUNIOR))

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

    def test_join_then_march_marks_joined(self):
        device = run_join(self, JOIN_AND_MARCH, ALL_TROOPS)
        self.assertEqual(device.reported, [PERYTON])
        self.assertIn("Chọn đội quân 1", device.logs)
        with device.fake_time():
            self.assertEqual(device.ctx.boss_memory.status(PERYTON), JOINED)

    def test_march_only_locked_troops_backs_out(self):
        device = run_join(self, MARCH_ONLY_LOCKED, {**IDLE_SETTINGS, "troop": ["Troop 3", "Troop 4"]})
        self.assertIn("Join Monster War: đội quân đã chọn [3, 4] đều đang khoá (6 ô khoá)", device.logs)

    def test_choose_assistant_general(self):
        device = run_join(self, CHOOSE_ASSISTANT, WITH_GENERALS)
        self.assertIn("Chọn đội quân 1", device.logs)
        self.assertIn("Đã chọn tướng phụ", device.logs)

    def test_choose_assistant_when_favorite_filter_already_on(self):
        device = run_join(self, CHOOSE_ASSISTANT_FAV_ALREADY_ON, WITH_GENERALS)
        self.assertIn("Đã chọn tướng phụ", device.logs)

    def test_assistant_development_tab(self):
        device = run_join(self, CHOOSE_ASSISTANT_DEVELOPMENT, {**WITH_GENERALS, "development_general": True})
        self.assertIn("Đã chọn tướng phụ", device.logs)

    def test_assistant_skips_disabled_main_general(self):
        device = run_join(self, CHOOSE_ASSISTANT_SKIP_MAIN, WITH_GENERALS)
        self.assertIn("Đã chọn tướng phụ", device.logs)

    def test_assistant_no_favorite_backs_and_marches(self):
        device = run_join(self, ASSISTANT_NO_FAVORITE, WITH_GENERALS)
        self.assertIn("Chọn tướng phụ: không có tướng nào để chọn", device.logs)
        self.assertNotIn("Đã chọn tướng phụ", device.logs)

    def test_skip_troop_without_main_general(self):
        device = run_join(self, SKIP_TROOP_WITHOUT_GENERAL, ALL_TROOPS)
        self.assertIn("Chọn đội quân 2", device.logs)

    def test_choose_main_general(self):
        device = run_join(self, CHOOSE_MAIN_GENERAL, {**WITH_GENERALS, "select_assistant_general": False})
        self.assertIn("Đã chọn tướng chính", device.logs)

    def test_no_main_general_still_joins_when_select_general_ticked(self):
        device = run_join(self, NO_MAIN_GENERAL_STILL_MARCH, {**WITH_GENERALS, "select_assistant_general": False})
        self.assertIn("Đội quân 2: không chọn được tướng chính, vẫn tham gia boss", device.logs)

    def test_no_main_general_still_joins_when_select_general_not_ticked(self):
        device = run_join(self, NO_MAIN_GENERAL_MARCH, ALL_TROOPS)
        self.assertIn("Đội quân 2: không có tướng chính, vẫn tham gia boss", device.logs)
        self.assertNotIn("Đã chọn tướng chính", device.logs)

    def test_march_returns_to_war_list(self):
        device = run_join(self, MARCH_THEN_BACK_TO_LIST, ALL_TROOPS)
        self.assertIn("Chọn đội quân 1", device.logs)
        self.assertIn("Bỏ tích ô War (chỉ giữ rally đánh boss)", device.logs)

    def test_not_enough_stamina_stops_join_boss(self):
        device = run_join(self, NO_STAMINA_STOP, {**ALL_TROOPS, "use_stamina": "No"})
        with device.fake_time():
            self.assertIsNone(device.ctx.boss_memory.status(PERYTON))   # chưa tham gia được

    def test_not_enough_stamina_confirms_when_allowed(self):
        run_join(self, NO_STAMINA_CONFIRM, {**ALL_TROOPS, "use_stamina": "ALL"})

    def test_refill_stamina_100_then_march_again(self):
        device = run_join(self, REFILL_100, {**ALL_TROOPS, "use_stamina": "100"})
        self.assertIn("Join Monster War: dùng vật phẩm thể lực (100)", device.logs)
        with device.fake_time():
            self.assertEqual(device.ctx.boss_memory.status(PERYTON), JOINED)

    def test_refill_stamina_all_then_march_again(self):
        device = run_join(self, REFILL_ALL, {**ALL_TROOPS, "use_stamina": "ALL"})
        self.assertIn("Join Monster War: dùng vật phẩm thể lực (ALL)", device.logs)
        with device.fake_time():
            self.assertEqual(device.ctx.boss_memory.status(PERYTON), JOINED)

    def test_out_of_stamina_items_does_not_mark_joined(self):
        device = run_join(self, OUT_OF_STAMINA_ITEMS, {**ALL_TROOPS, "use_stamina": "ALL"})
        self.assertIn("Join Monster War: hết vật phẩm thể lực", device.logs)
        with device.fake_time():
            self.assertIsNone(device.ctx.boss_memory.status(PERYTON))

    def test_green_select_buttons_only(self):
        image = cv2.imread(str(SCREENS / "select_assistant_main_disabled.png"))
        if image is None:
            self.skipTest("thiếu ảnh")
        self.assertFalse(_is_green_button(image, (329, 373)))   # King Arthur: nút xám
        self.assertTrue(_is_green_button(image, (329, 627)))    # Hudson: nút xanh

    def test_assistant_already_there_marches_directly(self):
        device = run_join(self, ASSISTANT_ALREADY_THERE, WITH_GENERALS)
        self.assertNotIn("Đã chọn tướng phụ", device.logs)

    def test_all_joined_short_list_idles(self):
        device = run_join(self, ALL_JOINED_SHORT_LIST, IDLE_SETTINGS)
        self.assertEqual(device.events, [])
        self.assertEqual(device.reported, [])

    def test_scrolled_list_without_join_keeps_scrolling(self):
        device = run_join(self, SCROLLED_ONLY_ATTACKING, IDLE_SETTINGS)
        self.assertNotIn("Rảnh: không còn boss để tham gia", device.logs)

    def test_short_list_without_join_idles(self):
        device = run_join(self, TWO_ATTACKING_LIST_END, IDLE_SETTINGS)
        self.assertEqual(device.events, [])     # không cuộn, không bấm

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
            self.assertIsNone(device.ctx.boss_memory.status(BAYARD))

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
        self.assertIn("Boss (633, 941): thời gian đỏ, bỏ qua lần này", device.logs)
        with device.fake_time():
            # Chỉ bỏ qua lần này, không nhớ: lần quét sau kiểm tra lại, hết đỏ thì Join
            self.assertIsNone(device.ctx.boss_memory.status(MANTICORE))
        # Không còn chờ wait_gone 10 giây mỗi lượt (trước đây ~82 giây).
        self.assertLess(device.clock.now - 1000, 2)

    def test_red_timer_detection_on_real_buttons(self):
        # Chỉ Manticore có thời gian đỏ. Nút Join ở y 365 của war_list_bottom (thời gian trắng)
        # trước đây bị nhận nhầm là đỏ vì vùng kiểm tra chạm viền đỏ của thẻ bên dưới.
        checker = SimpleNamespace(bot=BotContext(SimpleNamespace(serial="t"), threading.Event(), None,
                                                 lambda _: None))
        jh = checker.bot.template_size(JOIN)[1]
        cases = [("war_list_join_red.png", (319, 331), True),
                 ("war_list_bottom.png", (319, 365), False),
                 ("war_list_bottom.png", (319, 596), False),
                 ("02_war_list_join.png", (319, 331), False),
                 ("war_joined_and_join.png", (319, 562), False),
                 ("war_cannot_send_more_troops.png", (319, 562), False)]
        for screen, (x, y), red in cases:
            image = cv2.imread(str(SCREENS / screen))
            if image is None:
                self.skipTest(f"thiếu ảnh {screen}")
            with self.subTest(screen=screen, y=y):
                self.assertEqual(_Boss._join_text_is_red(checker, image, x, y, jh), red)

    def test_unknown_screen_retries_before_go_home(self):
        # Màn hình không nhận ra: chụp lại 3 lần (mỗi lần 1 s) rồi mới go_home (Back).
        device = run_join(self, [Step("02_war_list_join.png?unknown", back())], IDLE_SETTINGS)
        self.assertEqual(device.shots, 1 + 3)
        self.assertIn("Màn hình vẫn không nhận ra: go_home", device.logs)

    def test_join_again_after_cannot_send_more_troops(self):
        device = run_join(self, JOIN_AGAIN_AFTER_CANNOT_SEND, IDLE_SETTINGS)
        self.assertEqual(device.reported, [PERYTON_2] * 3)            # bấm lại cùng một boss
        with device.fake_time():
            self.assertIsNone(device.ctx.boss_memory.status(PERYTON_2))   # không bị bỏ qua
        # Mỗi lần bấm cách nhau ~5 giây (JOIN_TAP_WAIT), không phải 10 giây của wait_gone:
        # 3 lần bấm = 2 khoảng chờ trước lần bấm cuối.
        self.assertLess(device.clock.now - 1000, 12)

    def test_join_again_same_boss_not_scroll_away(self):
        settings = {**IDLE_SETTINGS, "selected_bosses": [
            {"category_key": "mythical_and_elite_bosses", "name": "Aglaope", "levels": [1]}]}
        device = run_join(self, JOIN_AGAIN_AGLAOPE, settings)
        self.assertEqual(device.reported, [AGLAOPE] * 3)
        self.assertFalse(any(event[0] == "swipe" for _, event in device.events))

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
            self.assertIsNone(device.ctx.boss_memory.status(PERYTON))

    def test_ticked_boss_name_is_read(self):
        device = run_join(self, JOIN_BELOW_ATTACKING, SETTINGS)
        self.assertIn("Boss (655, 997): '(boss) yasha' -> Yasha: join", device.logs)

    # ---- BossMemory ------------------------------------------------------
    def test_joined_boss_is_not_joined_again(self):
        device = run_join(self, ALREADY_KNOWN_PERYTON, IDLE_SETTINGS,
                          setup=remember(PERYTON, JOINED))
        self.assertEqual(device.reported, [])

    def test_legacy_skipped_memory_does_not_block_selected_boss(self):
        device = run_join(self, LEGACY_SKIPPED_RECHECK, IDLE_SETTINGS,
                          setup=remember(PERYTON, SKIPPED))
        self.assertEqual(device.reported, [PERYTON])

    def test_joined_boss_skips_every_rally_on_it(self):
        # Hai rally cùng toạ độ Minotaur: đã tham gia một thì bỏ qua cả hai.
        device = run_join(self, ALREADY_KNOWN_MINOTAUR, IDLE_SETTINGS,
                          setup=remember(MINOTAUR, JOINED))
        self.assertEqual(device.reported, [])

    def test_scrolls_three_down_three_up_then_idle(self):
        device = run_join(self, SCROLL_LIMIT, IDLE_SETTINGS,
                          setup=remember(MINOTAUR, JOINED))
        self.assertEqual(device.reported, [])

    def test_unwanted_boss_does_not_reset_scroll_count(self):
        settings = {**IDLE_SETTINGS, "selected_bosses": [
            b for b in SETTINGS["selected_bosses"] if b["name"] != "Yasha"]}
        device = run_join(self, UNWANTED_BOSS_DOES_NOT_RESET_SCROLLS, settings,
                          setup=remember(MINOTAUR, JOINED))
        self.assertEqual(device.reported, [])
        with device.fake_time():
            self.assertIsNone(device.ctx.boss_memory.status(YASHA))

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
