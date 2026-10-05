"""Kiểm thử Join Boss bằng ảnh ADB chụp khi chạy code hiện tại.

Mục đích
-------
Đây là bộ hồi quy của lần test code Join Boss mới. Ảnh nằm trong
``screens/new_join_boss_flow`` và là ảnh nguyên màn hình 396x704 lấy trực tiếp
từ giả lập; không phải ảnh sao chép từ bộ ``screens`` cũ và không phải ảnh dựng.

Cấu hình chung
--------------
* Chỉ cho phép ``Junior Cerberus`` (Cerberus cấp 1).
* Dùng đội quân 1, không tự dùng vật phẩm thể lực.
* ``exit_when_idle=True`` để flow kết thúc bằng ``IDLE`` khi quét hết danh sách.

Các trường hợp được chứng minh bằng ảnh ADB
------------------------------------------
1. Luồng thành công hoàn chỉnh:
   Home -> mở Alliance War -> Join đúng boss -> chọn Troop 1 -> March -> danh
   sách hiện ``Joined`` -> kết thúc rảnh.
2. Rally hết thời gian:
   chữ thời gian đỏ phải bị bỏ qua; bot không tap và không report boss. Bot quét
   đủ chu kỳ 3 lần xuống + 3 lần lên rồi mới trả ``IDLE``.
3. Ô ``War`` đang được tích:
   phải bỏ tích ``War`` trước, chỉ sau đó mới được quét/cuộn Monster War.
4. Danh sách ngắn chỉ còn rally ``Joined``:
   không tap lại, không report lại và trả ``IDLE``.
5. Chuyển trạng thái timer:
   cùng thuật toán phải nhận ảnh rally hết giờ là đỏ và ảnh boss còn hạn là có
   thể tham gia, tránh bỏ nhầm boss hợp lệ.

Các trường hợp danh sách hỗn hợp khó chờ xuất hiện đồng thời trên ADB
--------------------------------------------------------------------
6. Nhiều Cerberus bị cấm/không đúng cấp nằm trên Cerberus hợp lệ:
   blacklist từng thẻ cấm trên màn hiện tại và vẫn tap đúng thẻ hợp lệ cuối.
7. Boss cấm và boss đúng loại nhưng hết giờ xen kẽ:
   bỏ qua toàn bộ thẻ cấm/đỏ, không dừng sớm và chỉ tap boss hợp lệ còn hạn.

Hai trường hợp 6-7 dùng danh sách điểm xác định để kiểm tra thuật toán duyệt
thẻ, không tạo ảnh giả. Những nhánh không có trạng thái màn hình ổn định như
OCR tọa độ hỏng, March không xác nhận Joined, popup stamina lỗi, chọn tướng lỗi
và giới hạn bỏ tích War nằm trong ``test_edge_cases.py``.

Quy ước PASS quan trọng
-----------------------
* Không được tap boss cấm, boss hết giờ hoặc nút ``Joined``.
* Một boss chỉ được ghi nhận đã tham gia sau khi màn War xác nhận ``Joined``.
* Có thẻ không hợp lệ ở phía trên không được làm bot bỏ sót thẻ hợp lệ phía dưới.
"""

import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import cv2
import numpy as np

from bot.activities import join_monster_war
from bot.activities.join_monster_war.constants import (
    IDLE,
    JOIN,
    JOIN_THRESHOLD,
    LISTBOSS,
    MARCH,
    PRESET_X0,
    PRESET_Y,
    REGIONS,
)
from bot.activities.join_monster_war.run import _Boss
from bot.context import BotContext
from tests.flow import Step, end, run_flow, swipe, tap, tap_at, tap_pct


SCREENS = Path(__file__).parent / "screens" / "new_join_boss_flow"

SETTINGS = {
    "troop": ["Troop 1"],
    "use_stamina": "No",
    "exit_when_idle": True,
    "selected_bosses": [
        {
            "category_key": "special_and_recurring_event_bosses",
            "name": "Cerberus",
            "levels": [1],
        }
    ],
}

DOWN = swipe(50, 65, 50, 40)
UP = swipe(50, 40, 50, 65)

# Danh mục ảnh ADB của lần test này. Mỗi ảnh chỉ đại diện cho một trạng thái có
# ý nghĩa; không chụp lặp theo từng vòng polling.
#
# 01_home_listboss.png              Màn Home có nút mở danh sách boss.
# 02_expired_manticore_skipped.png  Manticore hết giờ đã được bot bỏ qua.
# 03_war_joined_list.png            Danh sách War có rally đã Joined, ô War tắt.
# 04_war_checkbox_on.png            Danh sách War khi ô War còn được tích.
# 05_expired_rallies_list.png       Các rally có timer đỏ/hết thời gian.
# 06_valid_boss_before_join.png     Junior Cerberus còn hạn trước khi tap Join.
# 07_march_before_action.png        Màn March trước khi chọn quân/hành quân.
# 08_war_after_march_joined.png     Quay lại War và thấy xác nhận Joined.

# Luồng ADB chính: phải dùng đúng ảnh trước hành động, rồi ảnh tiếp theo chứng
# minh trạng thái đã đổi. Kết quả cuối phải report đúng tọa độ boss (767, 811).
LIVE_MAIN_FLOW = [
    Step("01_home_listboss.png", tap(LISTBOSS)),
    Step("06_valid_boss_before_join.png", tap(JOIN)),
    Step("07_march_before_action.png", tap_pct(PRESET_X0, PRESET_Y, tol=8)),
    Step("07_march_before_action.png", tap(MARCH)),
    Step("08_war_after_march_joined.png", end(IDLE)),
]
LIVE_BOSS_COORDS = (767, 811)

# Một chu kỳ quét đầy đủ khi mọi rally đều đã hết giờ: 3 xuống + 3 lên. Ở bước
# cuối activity phải tự trả IDLE, không được tap bất kỳ nút Join nào.
LIVE_EXPIRED_SCAN_FLOW = [
    *[Step("05_expired_rallies_list.png", DOWN) for _ in range(3)],
    *[Step("05_expired_rallies_list.png", UP) for _ in range(3)],
    Step("05_expired_rallies_list.png", end(IDLE)),
]

# War đang tích phải được tắt trước. Ảnh sau thao tác xác nhận dấu tích đã mất;
# lúc đó bot mới được cuộn danh sách Monster War.
LIVE_UNTICK_WAR_FLOW = [
    Step("04_war_checkbox_on.png", tap_at(201, 118, tol=8)),
    Step("03_war_joined_list.png", DOWN),
]

# Danh sách ngắn chỉ có Joined đã hiện đầy đủ: không cần tap hoặc cuộn.
LIVE_JOINED_IDLE_FLOW = [Step("08_war_after_march_joined.png", end(IDLE))]


class CurrentCodeJoinBossFlow(unittest.TestCase):
    def test_multiple_forbidden_cerberus_cards_do_not_block_allowed_boss(self):
        """Ba thẻ cấm phía trên không được chặn thẻ Cerberus hợp lệ thứ tư.

        PASS: ba điểm đầu vào blacklist; chỉ tâm nút thứ tư được tap/report.
        FAIL: dừng sau thẻ cấm đầu tiên, cuộn đi, hoặc tap bất kỳ thẻ cấm nào.
        """
        points = [(319, 290), (319, 370), (319, 450), (319, 530)]

        class FakeBot:
            def __init__(self):
                from bot.activities.join_monster_war.boss_memory import BossMemory

                self.boss_memory = BossMemory()
                self.reported = []
                self.taps = []

            def template_size(self, _template):
                return 20, 14

            def find_all(self, template, **_kwargs):
                return list(points) if template == JOIN else []

            def crop(self, image, *_args):
                return image

            def find(self, *_args, **_kwargs):
                return None

            def report_boss(self, coords):
                self.reported.append(coords)

            def tap(self, x, y):
                self.taps.append((x, y))

            def log(self, _message):
                pass

        bot = FakeBot()
        boss = _Boss(bot, SETTINGS)
        # Ba thẻ Cerberus bị cấm/không đúng cấp, thẻ thứ tư là boss được phép.
        boss._boss_is_wanted = mock.Mock(side_effect=[False, False, False, True])
        boss._join_text_is_red = mock.Mock(return_value=False)

        self.assertTrue(boss._join(np.zeros((704, 396, 3), dtype=np.uint8)))
        self.assertEqual(boss.screen_blacklist, points[:3])
        self.assertEqual(bot.taps, [(329, 537)])
        self.assertEqual(bot.reported, [None])

    def test_forbidden_and_expired_cerberus_cards_do_not_block_valid_boss(self):
        """Thẻ cấm và thẻ timer đỏ xen kẽ không được chặn boss hợp lệ cuối.

        Thứ tự: cấm -> đúng loại/hết giờ -> cấm -> đúng loại/hết giờ -> hợp lệ.
        PASS: bốn thẻ đầu vào blacklist và chỉ thẻ thứ năm được tap/report.
        """
        points = [(319, 280), (319, 350), (319, 420), (319, 490), (319, 560)]

        class FakeBot:
            def __init__(self):
                from bot.activities.join_monster_war.boss_memory import BossMemory

                self.boss_memory = BossMemory()
                self.reported = []
                self.taps = []

            def template_size(self, _template):
                return 20, 14

            def find_all(self, template, **_kwargs):
                return list(points) if template == JOIN else []

            def crop(self, image, *_args):
                return image

            def find(self, *_args, **_kwargs):
                return None

            def report_boss(self, coords):
                self.reported.append(coords)

            def tap(self, x, y):
                self.taps.append((x, y))

            def log(self, _message):
                pass

        bot = FakeBot()
        boss = _Boss(bot, SETTINGS)
        # 1 cấm, 2 đúng loại nhưng hết giờ, 3 cấm, 4 hết giờ, 5 hợp lệ.
        boss._boss_is_wanted = mock.Mock(side_effect=[False, True, False, True, True])
        boss._join_text_is_red = mock.Mock(side_effect=[True, True, False])

        self.assertTrue(boss._join(np.zeros((704, 396, 3), dtype=np.uint8)))
        self.assertEqual(boss.screen_blacklist, points[:4])
        self.assertEqual(bot.taps, [(329, 567)])
        self.assertEqual(bot.reported, [None])

    def test_live_main_flow_home_join_march_joined(self):
        """Ảnh ADB: chạy trọn Home -> Join -> Troop 1 -> March -> Joined.

        PASS: report đúng boss (767, 811), có log chọn đội 1 và chỉ kết thúc sau
        khi ảnh cuối đã hiển thị Joined.
        """
        device = run_flow(self, join_monster_war.run, SCREENS, LIVE_MAIN_FLOW, SETTINGS)
        self.assertEqual(device.reported, [LIVE_BOSS_COORDS])
        self.assertIn("Chọn đội quân 1", device.logs)

    def test_live_expired_rallies_are_never_tapped(self):
        """Ảnh ADB: mọi rally timer đỏ phải bị bỏ qua suốt một chu kỳ quét.

        Cố ý cho phép cả Cerberus cấp 1 và Manticore để chứng minh lý do bỏ qua
        là hết thời gian, không phải vì tên boss chưa được chọn.
        """
        settings = {
            **SETTINGS,
            "selected_bosses": [
                {
                    "category_key": "special_and_recurring_event_bosses",
                    "name": "Cerberus",
                    "levels": [1],
                },
                {"category_key": "standard_bosses", "name": "Manticore", "levels": []},
            ],
        }
        device = run_flow(self, join_monster_war.run, SCREENS, LIVE_EXPIRED_SCAN_FLOW, settings)
        self.assertEqual(device.reported, [])
        self.assertFalse(any(event[0] == "tap" for _, event in device.events))
        self.assertIn("thời gian đỏ, bỏ qua lần này", "\n".join(device.logs))

    def test_live_war_checkbox_is_unticked_before_scrolling(self):
        """Ảnh ADB: tắt bộ lọc War trước khi cuộn danh sách Monster War."""
        device = run_flow(self, join_monster_war.run, SCREENS, LIVE_UNTICK_WAR_FLOW, SETTINGS)
        self.assertIn("Bỏ tích ô War (chỉ giữ rally đánh boss)", device.logs)

    def test_live_joined_short_list_returns_idle(self):
        """Ảnh ADB: danh sách chỉ còn Joined thì không thao tác và trả IDLE."""
        device = run_flow(
            self,
            join_monster_war.run,
            SCREENS,
            LIVE_JOINED_IDLE_FLOW,
            SETTINGS,
        )
        self.assertEqual(device.reported, [])
        self.assertEqual(device.events, [])

    def test_live_timer_color_changes_from_red_to_available(self):
        """Ảnh ADB: phân biệt timer đỏ đã hết giờ với nút Join còn hiệu lực.

        PASS: tất cả nút ở ảnh expired là đỏ và có ít nhất một nút ở ảnh valid
        không đỏ. Đây là chốt chống bỏ nhầm boss vừa chuyển sang trạng thái Join.
        """
        checker = SimpleNamespace(
            bot=BotContext(SimpleNamespace(serial="current-code-flow"), threading.Event(), None, lambda _: None)
        )
        join_height = checker.bot.template_size(JOIN)[1]

        expired = cv2.imread(str(SCREENS / "05_expired_rallies_list.png"))
        available = cv2.imread(str(SCREENS / "06_valid_boss_before_join.png"))
        self.assertIsNotNone(expired)
        self.assertIsNotNone(available)

        expired_buttons = checker.bot.find_all(
            JOIN, JOIN_THRESHOLD, expired, center=False, region=REGIONS[JOIN]
        )
        available_buttons = checker.bot.find_all(
            JOIN, JOIN_THRESHOLD, available, center=False, region=REGIONS[JOIN]
        )
        self.assertTrue(expired_buttons)
        self.assertTrue(available_buttons)
        self.assertTrue(
            all(_Boss._join_text_is_red(checker, expired, x, y, join_height)
                for x, y in expired_buttons)
        )
        self.assertTrue(
            any(not _Boss._join_text_is_red(checker, available, x, y, join_height)
                for x, y in available_buttons)
        )


if __name__ == "__main__":
    unittest.main()
