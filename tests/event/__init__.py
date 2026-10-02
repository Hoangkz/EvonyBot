"""
Flow test activity Event. Test nhiệm vụ chỉ kiểm phần nhiệm vụ: import setUpModule /
tearDownModule từ đây để tắt lượt nhận thưởng theo chấm đỏ (event/claim.py) chạy sau mỗi
event. Test nhận thưởng bật lại bằng `mock.patch.object(claim, "maybe_claim", MAYBE_CLAIM)`.
"""
from unittest import mock

from bot.activities.event import claim

MAYBE_CLAIM = claim.maybe_claim   # hàm thật
_patcher = mock.patch.object(claim, "maybe_claim", lambda *args, **kwargs: None)


def setUpModule():
    _patcher.start()


def tearDownModule():
    _patcher.stop()
