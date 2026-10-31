"""Cờ "hết kim cương" (bot/common/no_gems.py flag / take): nhiệm vụ báo, worker đọc rồi loại nhiệm vụ khỏi danh sách."""
import unittest
from unittest import mock

from bot.common import no_gems


class OutOfGemsFlag(unittest.TestCase):
    def test_take_reads_then_clears(self):
        ctx = mock.Mock()
        self.assertFalse(no_gems.take(ctx))
        no_gems.flag(ctx)
        self.assertTrue(no_gems.take(ctx))
        self.assertFalse(no_gems.take(ctx), "đọc xong thì xoá cờ")

    def test_dismiss_sets_the_flag(self):
        ctx = mock.Mock()
        no_gems.dismiss(ctx, "Task")
        ctx.back.assert_called_once()
        self.assertTrue(no_gems.take(ctx))


if __name__ == "__main__":
    unittest.main()
