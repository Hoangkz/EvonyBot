"""Giới hạn số giả lập chạy cùng lúc theo giấy phép (payload "max_devices")."""
import json
import unittest
from unittest import mock

import licensing
from bot.worker import manager as manager_module
from bot.worker.manager import BotManager


def _license(payload: dict) -> dict:
    return {"payload": json.dumps(payload), "signature": "x"}


class MaxDevicesTest(unittest.TestCase):
    def _max(self, license_):
        with mock.patch.object(licensing, "_load", return_value=license_), \
                mock.patch.object(licensing, "_signature_ok", return_value=True):
            return licensing.max_devices()

    def test_reads_limit_from_payload(self):
        self.assertEqual(self._max(_license({"max_devices": 3})), 3)

    def test_missing_or_invalid_means_unlimited(self):
        self.assertIsNone(self._max(_license({})))
        self.assertIsNone(self._max(_license({"max_devices": None})))
        self.assertIsNone(self._max(_license({"max_devices": 0})))

    def test_unreadable_license_blocks_everything(self):
        self.assertEqual(self._max(_license({"max_devices": "abc"})), 0)
        self.assertEqual(self._max(None), 0)

    def test_bad_signature_blocks_everything(self):
        with mock.patch.object(licensing, "_load", return_value=_license({"max_devices": 99})), \
                mock.patch.object(licensing, "_signature_ok", return_value=False):
            self.assertEqual(licensing.max_devices(), 0)

    def test_verify_sends_running_devices(self):
        sent = {}

        def fake_call(endpoint, code, customer=None, running=None, peak=None):
            sent.update(endpoint=endpoint, running=running, peak=peak)
            return {"code": code, "payload": "{}", "signature": "x"}

        with mock.patch.object(licensing, "stored_code", return_value="C"), \
                mock.patch.object(licensing, "_call", fake_call), \
                mock.patch.object(licensing, "_save"):
            licensing.verify(["emu-1", "emu-2"], 5)
        self.assertEqual(sent, {"endpoint": "verify", "running": ["emu-1", "emu-2"], "peak": 5})

    def test_peak_survives_stopping_until_reset(self):
        mgr = BotManager()
        mgr._workers.update({"a": object(), "b": object(), "c": object()})
        mgr._peak = 3
        mgr._workers.pop("b")
        mgr._workers.pop("c")
        self.assertEqual(mgr.peak_devices(), 3)   # stopped before the report, still seen
        mgr.reset_peak()
        self.assertEqual(mgr.peak_devices(), 1)

    def test_start_raises_peak(self):
        mgr = BotManager()
        with mock.patch.object(manager_module, "BotWorker"):
            mgr.start("a", ["x"], {})
            mgr.start("b", ["x"], {})
        mgr._workers.clear()
        self.assertEqual(mgr.peak_devices(), 2)

    def test_running_serials(self):
        mgr = BotManager()
        mgr._workers["a"] = object()
        self.assertEqual(mgr.running_serials(), ["a"])

    def test_manager_refuses_over_limit(self):
        mgr = BotManager()
        mgr.max_running = 1
        mgr._workers["a"] = object()
        logs = []
        mgr.log_message.connect(lambda serial, msg: logs.append((serial, msg)))
        with mock.patch.object(manager_module, "BotWorker") as worker_cls:
            self.assertFalse(mgr.start("b", ["x"], {}))
            worker_cls.assert_not_called()
        self.assertTrue(mgr.at_limit())
        self.assertEqual(logs[0][0], "b")

    def test_manager_unlimited_by_default(self):
        self.assertFalse(BotManager().at_limit())


if __name__ == "__main__":
    unittest.main()
