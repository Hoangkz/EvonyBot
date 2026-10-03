"""
Flow test activity Event. Test nhiệm vụ chỉ kiểm phần nhiệm vụ: import setUpModule /
tearDownModule từ đây để tắt lượt nhận thưởng theo chấm đỏ (event/claim.py) chạy sau mỗi
event. Test nhận thưởng bật lại bằng `mock.patch.object(claim, "maybe_claim", MAYBE_CLAIM)`.
Cũng tắt bước kiểm rương Login Rewards ở danh sách event (common.claim_login_reward): ảnh
04_event_list.png có rương chưa mở; test rương bật lại bằng
`mock.patch.object(common, "claim_login_reward", CLAIM_LOGIN_REWARD)`. Tắt cả bước mở Voyage to
Civilizations (common.open_voyage; 04_event_list.png của Gather Troops có Voyage); test Voyage bật
lại bằng `mock.patch.object(common, "open_voyage", OPEN_VOYAGE)`.
"""
from unittest import mock

from bot.activities.event import claim, common

MAYBE_CLAIM = claim.maybe_claim   # hàm thật
CLAIM_LOGIN_REWARD = common.claim_login_reward   # hàm thật
OPEN_VOYAGE = common.open_voyage                 # hàm thật
_patcher = mock.patch.object(claim, "maybe_claim", lambda *args, **kwargs: None)
LOGIN_REWARD_PATCHER = mock.patch.object(common, "claim_login_reward", lambda *args, **kwargs: False)
VOYAGE_PATCHER = mock.patch.object(common, "open_voyage", lambda *args, **kwargs: False)


def setUpModule():
    _patcher.start()
    LOGIN_REWARD_PATCHER.start()
    VOYAGE_PATCHER.start()


def tearDownModule():
    VOYAGE_PATCHER.stop()
    LOGIN_REWARD_PATCHER.stop()
    _patcher.stop()
