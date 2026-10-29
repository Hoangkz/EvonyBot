"""IScout hub: phân tích khung socket, gộp theo id, chọn tab theo server (không cần Chrome)."""
import json
import unittest

from bot.iscout import hub
from bot.iscout.hub import (BROWSER_START_SECONDS, LOGIN_SECONDS, NO_DATA_SECONDS, IScoutHub, IScoutLoginFailed, IScoutNoBrowser,
                            IScoutNoServer, IScoutNotOpen, IScoutWrongServer, Tab, parse_frame, pick_tab)

NOW = 1000.0


def row(uid, x, y, kind="evony.filters.event_monster", name="Rùa Nham thạch", level="Lv1", server=1835):
    return {"id": uid, "x": x, "y": y, "serverId": server, "item": {"raw_text": name},
            "details": {"translate": kind, "raw_text": level, "power_text": "12M"}, "monster_key": "33"}


def frame(upsert, delete=(), server_id=1835):
    body = {"type": "combined_query", "server_id": server_id, "data": {"delete": list(delete), "upsert": upsert}}
    return "42" + json.dumps(["filter_subscribe", body], ensure_ascii=False)


def tab_of(server, url="https://www.iscout.club/vi/dashboard", age=0):
    tab = Tab(url)
    tab.started = NOW - age
    if server is not None:
        tab.apply(server, [], [])
    return tab


class ParseTests(unittest.TestCase):
    def test_parse_frame_reads_boss_fields(self):
        server, bosses, deleted = parse_frame(
            frame([row("a1", 651, 225, "evony.filters.boss_monster", "Hươu có cánh (Trùm)", "Lv8")], ["z9"]))
        self.assertEqual((server, deleted), (1835, ["z9"]))
        self.assertEqual(bosses, [{"id": "a1", "name": "Hươu có cánh (Trùm)", "kind": "evony.filters.boss_monster", "level": 8,
                                   "power": "12M", "server": 1835, "x": 651, "y": 225}])

    def test_parse_frame_drops_other_kinds_and_other_frames(self):
        _, bosses, _ = parse_frame(frame([row("a", 1, 2), row("b", 3, 4, kind="evony.filters.resource")]))
        self.assertEqual([b["id"] for b in bosses], ["a"])
        self.assertIsNone(parse_frame("40"))
        self.assertIsNone(parse_frame('42["other",{"x":1}]'))
        self.assertIsNone(parse_frame("42not json"))

    def test_tab_keeps_id_when_boss_moves_and_removes_deleted(self):
        tab = Tab()
        tab.apply(*parse_frame(frame([row("a", 556, 66), row("b", 573, 48)])))
        tab.apply(*parse_frame(frame([row("a", 554, 66)], ["b"])))
        self.assertEqual([(b["id"], b["x"], b["y"]) for b in tab.bosses.values()], [("a", 554, 66)])


class PickTabTests(unittest.TestCase):
    def test_matches_server_of_device(self):
        tabs = [tab_of(1000), tab_of(1835)]
        self.assertIs(pick_tab(tabs, "1835", now=NOW), tabs[1])

    def test_prefers_previous_tab(self):
        tabs = [tab_of(1835), tab_of(1835)]
        self.assertIs(pick_tab(tabs, "1835", prefer=tabs[1], now=NOW), tabs[1])
        self.assertIs(pick_tab(tabs, "1835", prefer=None, now=NOW), tabs[0])

    def test_without_tabs_is_not_open(self):
        with self.assertRaises(IScoutNotOpen):
            pick_tab([], "1835", now=NOW)

    def test_wrong_server_raises_with_message(self):
        with self.assertRaises(IScoutWrongServer) as wrong:
            pick_tab([tab_of(1000), tab_of(1001)], "1835", now=NOW)
        self.assertEqual(wrong.exception.servers, [1000, 1001])
        self.assertIn("1835", wrong.exception.message)
        self.assertIn("1000", wrong.exception.message)

    def test_waits_for_young_tab_without_data(self):
        self.assertIsNone(pick_tab([tab_of(1000), tab_of(None, age=5)], "1835", now=NOW))

    def test_login_page_waits_then_fails(self):
        young = tab_of(None, url="https://www.iscout.club/vi/login", age=LOGIN_SECONDS - 1)
        self.assertIsNone(pick_tab([young], "1835", now=NOW))      # bot đang đăng nhập: chờ
        old = tab_of(None, url="https://www.iscout.club/vi/login", age=LOGIN_SECONDS + 1)
        with self.assertRaises(IScoutLoginFailed):
            pick_tab([old], "1835", now=NOW)

    def test_no_server(self):
        with self.assertRaises(IScoutNoServer):
            pick_tab([tab_of(None, age=NO_DATA_SECONDS + 1)], "1835", now=NOW)

    def test_every_error_has_a_popup_message(self):
        for error in (IScoutNotOpen(), IScoutNoBrowser(), IScoutLoginFailed(), IScoutNoServer(), IScoutWrongServer([1], "2")):
            self.assertTrue(error.message)
            self.assertIsInstance(error, hub.IScoutError)

    def test_configured_server_from_page_picks_tab_before_any_frame(self):
        tab = tab_of(None, age=5)
        tab.configured = 1835
        self.assertIs(pick_tab([tab], "1835", now=NOW), tab)
        other = tab_of(None, age=5)
        other.configured = 1000
        self.assertIsNone(pick_tab([other], "1835", now=NOW))      # tab mới mở: chờ dữ liệu
        with self.assertRaises(IScoutWrongServer):
            pick_tab([other], "1835", now=NOW + NO_DATA_SECONDS)

    def test_frame_server_beats_configured_server(self):
        tab = tab_of(1000)
        tab.configured = 1835
        with self.assertRaises(IScoutWrongServer):
            pick_tab([tab], "1835", now=NOW)


class FakeHub(IScoutHub):
    """Hub không có trình duyệt thật: không tab nào, đồng hồ do test điều khiển."""

    def __init__(self, launcher):
        self.now = 0.0
        super().__init__(launcher=launcher, clock=lambda: self.now)

    def _targets(self):
        return {}


class LaunchTests(unittest.TestCase):
    def test_opens_browser_once_then_waits_then_reports_not_open(self):
        launched = []
        hub = FakeHub(launched.append)
        self.assertEqual(hub.bosses("1835", "a@b.c", "pw"), [])
        self.assertEqual(hub.bosses("1835", "a@b.c", "pw"), [])
        self.assertEqual(len(launched), 1)                  # đang chờ tab hiện ra: không mở thêm
        hub.now = BROWSER_START_SECONDS + 1
        with self.assertRaises(IScoutNotOpen):
            hub.bosses("1835", "a@b.c", "pw")
        self.assertEqual(hub.bosses("1835", "a@b.c", "pw"), [])      # Start lại: mở trình duyệt lại
        self.assertEqual(len(launched), 2)

    def test_no_browser_installed_is_reported(self):
        def no_browser(port):
            raise IScoutNoBrowser()
        with self.assertRaises(IScoutNoBrowser):
            FakeHub(no_browser).bosses("1835", "a@b.c", "pw")


if __name__ == "__main__":
    unittest.main()
