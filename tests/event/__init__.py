"""
Flow test activity Event. Test nhiệm vụ chỉ kiểm phần nhiệm vụ: import setUpModule /
tearDownModule từ đây để tắt lượt nhận thưởng theo chấm đỏ (worker/event/policy.py maybe_claim) chạy sau mỗi
event. Test nhận thưởng bật lại bằng `mock.patch.object(event_policy, "maybe_claim", MAYBE_CLAIM)`.
Cũng tắt bước kiểm rương Login Rewards ở danh sách event (common.claim_login_reward): ảnh
04_event_list.png có rương chưa mở; test rương bật lại bằng
`mock.patch.object(common, "claim_login_reward", CLAIM_LOGIN_REWARD)`. Tắt cả bước mở Voyage to
Civilizations (common.open_voyage; 04_event_list.png của Gather Troops có Voyage); test Voyage bật
lại bằng `mock.patch.object(common, "open_voyage", OPEN_VOYAGE)`.
"""
from unittest import mock

from bot.activities.event import common
from bot.worker.event import policy as event_policy
from bot.worker.registry import REGISTRY

MAYBE_CLAIM = event_policy.maybe_claim   # hàm thật
CLAIM_LOGIN_REWARD = common.claim_login_reward   # hàm thật
OPEN_VOYAGE = common.open_voyage                 # hàm thật
_patcher = mock.patch.object(event_policy, "maybe_claim", lambda *args, **kwargs: None)
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


def run_event_tasks(bot, settings):
    """Chạy các nhiệm vụ Event đã được tích như worker: gọi thẳng `run` riêng của từng nhiệm vụ trong
    bot/worker/registry.py (theo thứ tự registry: nhiệm vụ của một event, rồi bước nhận thưởng của event đó).
    Không có hàm run của activity Event."""
    for definition in REGISTRY:
        if definition.group == "Event" and definition.key != "three_day_event" and definition.enabled(settings):
            definition.run(bot, settings)
