"""
Flow test activity Event. Test nhiệm vụ chỉ kiểm phần nhiệm vụ: import setUpModule /
tearDownModule từ đây. `run_event_tasks` mặc định bỏ qua bước nhận thưởng theo chấm đỏ (event/job.py claim_job) chạy sau mỗi
event; test nhận thưởng gọi `run_event_tasks(bot, settings, claims=True)`.
Cũng tắt bước kiểm rương Login Rewards ở danh sách event (common.claim_login_reward): ảnh
04_event_list.png có rương chưa mở; test rương bật lại bằng
`mock.patch.object(common, "claim_login_reward", CLAIM_LOGIN_REWARD)`. Tắt cả bước mở Voyage to
Civilizations (common.open_voyage; 04_event_list.png của Gather Troops có Voyage); test Voyage bật
lại bằng `mock.patch.object(common, "open_voyage", OPEN_VOYAGE)`.
"""
from unittest import mock

from bot.activities.event import common
from bot.worker.tasks import REGISTRY

CLAIM_LOGIN_REWARD = common.claim_login_reward   # hàm thật
OPEN_VOYAGE = common.open_voyage                 # hàm thật
LOGIN_REWARD_PATCHER = mock.patch.object(common, "claim_login_reward", lambda *args, **kwargs: False)
VOYAGE_PATCHER = mock.patch.object(common, "open_voyage", lambda *args, **kwargs: False)


def setUpModule():
    LOGIN_REWARD_PATCHER.start()
    VOYAGE_PATCHER.start()


def tearDownModule():
    VOYAGE_PATCHER.stop()
    LOGIN_REWARD_PATCHER.stop()


def run_event_tasks(bot, settings, claims=False):
    """Chạy các nhiệm vụ Event đã được tích như worker: gọi thẳng `run` riêng của từng nhiệm vụ trong
    bot/worker/tasks.py REGISTRY (theo thứ tự trong bảng). `claims`: có chạy cả bước nhận thưởng của từng event không."""
    for definition in REGISTRY:
        if definition.group != "Event" or definition.key == "three_day_event":
            continue
        if definition.key.endswith("_claim") and not claims:
            continue
        if definition.enabled(settings):
            definition.run(bot, settings)
