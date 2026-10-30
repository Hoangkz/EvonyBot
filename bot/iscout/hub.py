"""iScout bosses from the socket frames of browser tabs (any Chromium browser) that have the iScout dashboard open.

iScout's socket sits behind Cloudflare, so a real browser keeps the page and socket; we only read the frames through DevTools. The bot starts
that browser itself (launch_browser: own profile + DevTools port, so the login is kept between runs) and logs in with the email / password from
the tab; a browser already started by open_browser.bat is reused. Each frame is `42["filter_subscribe", {data: {upsert: [...], delete: [ids]}}]`:
a boss keeps its `id` while its x / y change, so `upsert` overwrites the entry of that id.
"""
import json
import os
import re
import subprocess
import threading
import time
import urllib.request

import websocket

PORT = 9222
KINDS = ("evony.filters.boss_monster", "evony.filters.event_monster")     # chỉ hai loại này; loại khác thì bỏ
RESCAN_SECONDS = 2
EVAL_EVERY = 2             # giây giữa hai lần đọc server đã cấu hình trên trang (tới khi đọc được)
EVAL_ID = 100
# Thẻ "ID máy chủ đã cấu hình <số> (Sửa Hồ Sơ)": tìm theo liên kết /user/profile, lấy số trong thẻ cha (không phụ thuộc ngôn ngữ trang)
CONFIGURED_JS = ("(() => { for (const a of document.querySelectorAll(\"a[href$='/user/profile']\")) "
                 "{ const m = (a.parentElement ? a.parentElement.innerText : '').match(/[0-9]+/); if (m) return m[0]; } return null; })()")
NO_DATA_SECONDS = 30       # tab (không phải trang đăng nhập) quá chừng này giây mà chưa nhận khung nào = không lấy được server
LOGIN_SECONDS = 40         # trang đăng nhập quá chừng này giây vẫn chưa vào được = đăng nhập thất bại
BROWSER_START_SECONDS = 40     # mở trình duyệt xong chờ chừng này giây cho tab iScout hiện ra
LOGIN_ID = 200
RELOAD_ID = 300
START_URL = "https://www.iscout.club/vi/dashboard"
PROFILE = os.path.join(os.path.expanduser("~"), "iscout_browser")      # hồ sơ riêng (cùng thư mục với open_browser.bat): giữ phiên đăng nhập
# Điền email / mật khẩu rồi bấm đăng nhập; "wait" khi form chưa hiện. Giá trị gán bằng setter gốc + sự kiện input để React / Vue nhận ra.
LOGIN_JS = """(() => {
  const email = document.querySelector("input[type=email], input[name=email]");
  const pass = document.querySelector("input[type=password]");
  const form = pass && pass.closest("form");      // trang có nhiều nút submit: lấy nút của chính form đăng nhập
  const button = form && [...form.querySelectorAll("button")].find(b => b.type === "submit");      // nút Đăng nhập không có thuộc tính type, mặc định là submit
  if (!email || !pass || !button) return "wait";
  const fill = (el, value) => {
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set.call(el, value);
    el.dispatchEvent(new Event("input", {bubbles: true}));
    el.dispatchEvent(new Event("change", {bubbles: true}));
  };
  fill(email, __EMAIL__);
  fill(pass, __PASSWORD__);
  button.click();
  return "submitted";
})()"""
# Trình duyệt nền Chromium (cùng giao thức gỡ lỗi), thư mục gốc là biến môi trường; thứ tự ưu tiên.
BROWSERS = (
    ("ProgramFiles", "Google/Chrome/Application/chrome.exe"),
    ("ProgramFiles(x86)", "Google/Chrome/Application/chrome.exe"),
    ("LocalAppData", "Google/Chrome/Application/chrome.exe"),
    ("ProgramFiles(x86)", "Microsoft/Edge/Application/msedge.exe"),
    ("ProgramFiles", "Microsoft/Edge/Application/msedge.exe"),
    ("ProgramFiles", "BraveSoftware/Brave-Browser/Application/brave.exe"),
    ("LocalAppData", "BraveSoftware/Brave-Browser/Application/brave.exe"),
    ("ProgramFiles", "CocCoc/Browser/Application/browser.exe"),
    ("LocalAppData", "CocCoc/Browser/Application/browser.exe"),
)


class IScoutError(Exception):
    """Lý do không dùng được iScout; `message` là nội dung popup."""
    message = ""


class IScoutNoBrowser(IScoutError):
    message = "Không tìm thấy trình duyệt nào để mở iScout.\nHãy cài Chrome, Edge, Brave hoặc Cốc Cốc rồi bấm Start lại."


class IScoutNoCredentials(IScoutError):
    message = "Chưa nhập email và mật khẩu iScout.\nHãy nhập ở tab Attack Boss (nguồn IsCout) rồi bấm Start lại."


class IScoutNotOpen(IScoutError):
    message = ("Chưa bật iScout.\nĐã mở trình duyệt nhưng không thấy trang iScout. Hãy mở https://www.iscout.club/vi/dashboard "
               "trong cửa sổ đó (hoặc đóng nó đi) rồi bấm Start lại.")


class IScoutLoginFailed(IScoutError):
    message = ("Đăng nhập iScout không thành công.\nHãy kiểm tra email, mật khẩu ở tab Attack Boss, hoặc đăng nhập tay một lần "
               "trong cửa sổ trình duyệt vừa mở (có thể trang đòi xác minh), rồi bấm Start lại.")


class IScoutNoServer(IScoutError):
    message = ("Không lấy được server từ trang iScout.\nHãy vào trang Dashboard, đặt bộ lọc boss "
               "rồi bấm Start lại.")


class IScoutWrongServer(IScoutError):
    def __init__(self, servers, device_server):
        super().__init__(servers)
        self.servers = servers
        self.message = (f"Tài khoản iScout đã đăng nhập không cùng server với thiết bị này (thiết bị: server {device_server}, "
                        f"iScout: server {', '.join(str(n) for n in servers)})." + "\n" +
                        "Hãy đổi server trong Hồ sơ iScout, hoặc nhập tài khoản iScout khác ở tab Attack Boss, rồi bấm Start lại.")


def parse_boss(row):
    """Một phần tử `upsert` -> {id, name, kind, level, power, server, x, y}; None nếu thiếu trường / không phải hai loại KINDS."""
    try:
        details = row["details"]
        if details["translate"] not in KINDS:
            return None
        return {
            "id": str(row["id"]), "name": row["item"]["raw_text"], "kind": details["translate"],
            "level": int(re.sub(r"\D", "", details["raw_text"])), "power": details.get("power_text", ""),
            "server": int(row["serverId"]), "x": int(row["x"]), "y": int(row["y"]),
        }
    except (KeyError, TypeError, ValueError):
        return None


def parse_frame(payload):
    """Khung socket.io -> (server_id hoặc None, [boss], [id đã mất]); None nếu không phải khung dữ liệu boss."""
    if not payload.startswith("42"):
        return None
    try:
        event = json.loads(payload[2:])
        info = event[1]
        data = info["data"]
        upsert, delete = data.get("upsert") or [], data.get("delete") or []
    except (ValueError, KeyError, IndexError, TypeError, AttributeError):
        return None
    bosses = [boss for boss in map(parse_boss, upsert) if boss]
    return info.get("server_id"), bosses, [str(i) for i in delete]


class Tab:
    """Boss của một tab iScout: id -> boss; `server` (từ khung dữ liệu) None tới khi tab nhận khung đầu tiên; `configured` là "ID máy chủ đã
    cấu hình" đọc từ chữ trên trang (server trong hồ sơ iScout, có thể khác server của boss với tài khoản miễn phí)."""

    def __init__(self, url="", socket_url=""):
        self.url = url
        self.socket_url = socket_url      # địa chỉ DevTools của tab (để gửi lệnh tải lại trang)
        self.started = time.monotonic()
        self.server = None
        self.login_sent = False
        self.configured = None
        self.bosses = {}
        self.alive = True

    def reset(self):
        """Quên dữ liệu đã nhận (trang vừa được tải lại): tab chờ khung đầu tiên như tab mới mở."""
        self.started = time.monotonic()
        self.server = None
        self.login_sent = False
        self.configured = None
        self.bosses = {}

    @property
    def known_server(self):
        """Server của tab: khung dữ liệu thắng, chưa có khung thì dùng server đã cấu hình trên trang."""
        return self.server if self.server is not None else self.configured

    @property
    def login_page(self):
        return "/login" in self.url

    def apply(self, server_id, bosses, deleted):
        if server_id is not None:
            self.server = int(server_id)
        elif bosses:
            self.server = bosses[0]["server"]
        for boss in bosses:
            self.bosses[boss["id"]] = boss
        for uid in deleted:
            self.bosses.pop(uid, None)


def _waiting(tab, now):
    """Tab chưa có dữ liệu mà còn trong thời gian chờ (trang đăng nhập: chờ đăng nhập xong; trang khác: chờ khung đầu tiên)."""
    return tab.server is None and now - tab.started < (LOGIN_SECONDS if tab.login_page else NO_DATA_SECONDS)


def pick_tab(tabs, server, prefer=None, now=None):
    """Tab có boss cùng server với thiết bị (`prefer`, tab đã dùng lần trước, được xét trước); None = chờ tab nhận dữ liệu.

    Chưa biết server thiết bị: tab đầu tiên có dữ liệu. Raises IScoutNotOpen / IScoutLoginFailed / IScoutNoServer / IScoutWrongServer.
    """
    now = time.monotonic() if now is None else now
    if not tabs:
        raise IScoutNotOpen()
    loaded = [tab for tab in tabs if tab.known_server is not None]
    if prefer in loaded:
        loaded.remove(prefer)
        loaded.insert(0, prefer)
    try:
        want = int(str(server).strip())
    except ValueError:
        want = None
    for tab in loaded:
        if want is None or tab.known_server == want:
            return tab
    if any(_waiting(tab, now) for tab in tabs):      # chưa có khung: chờ, khung mới là server thật của boss
        return None
    if loaded:
        raise IScoutWrongServer(sorted({tab.known_server for tab in loaded}), server)
    if any(tab.login_page for tab in tabs):
        raise IScoutLoginFailed()
    raise IScoutNoServer()


def launch_browser(port=PORT):
    """Mở trình duyệt nền Chromium đầu tiên tìm thấy tới trang iScout, với cổng gỡ lỗi và hồ sơ riêng. Raises IScoutNoBrowser."""
    for root, relative in BROWSERS:
        base = os.environ.get(root)
        path = os.path.join(base, *relative.split("/")) if base else ""
        if path and os.path.exists(path):
            subprocess.Popen([path, f"--remote-debugging-port={port}", "--remote-allow-origins=*", f"--user-data-dir={PROFILE}",
                              "--no-first-run", "--no-default-browser-check", START_URL])
            return path
    raise IScoutNoBrowser()


class IScoutHub:
    """Giữ một luồng nghe cho mỗi tab iScout của trình duyệt; dùng chung mọi thiết bị. Chưa có tab nào thì tự mở trình duyệt."""

    def __init__(self, port=PORT, launcher=launch_browser, clock=time.monotonic):
        self._port = port
        self._launcher = launcher
        self._clock = clock
        self._lock = threading.Lock()
        self._tabs = {}          # id của tab trình duyệt -> Tab
        self._last = {}          # server thiết bị -> tab đã dùng lần trước (xét trước)
        self._scanned = 0.0
        self._launched = None    # lúc đã mở trình duyệt mà chưa thấy tab iScout
        self._login = ("", "")   # email, mật khẩu để đăng nhập khi tab ở trang đăng nhập

    def bosses(self, server, email="", password=""):
        """Boss của tab cùng server với thiết bị ([] khi còn đang mở trình duyệt / đăng nhập / chờ dữ liệu). Raises IScoutError."""
        tab = self._tab(server, email, password)
        if tab is None:
            return []
        with self._lock:
            return list(tab.bosses.values())

    def ready(self, server, email="", password="") -> bool:
        """Trình duyệt đã mở, đã đăng nhập và có tab iScout cùng server với thiết bị (đã nhận dữ liệu). False khi còn đang mở trình duyệt / đăng nhập / chờ
        dữ liệu (gọi lại sau). Chưa có tab thì mở trình duyệt, y như `bosses`. Raises IScoutError."""
        return self._tab(server, email, password) is not None

    def reload(self, server) -> None:
        """Tải lại trang iScout (tab đã dùng cho `server`, chưa có thì mọi tab): iScout tự ngắt phiên sau tối đa 30 phút nên mỗi lần vào Attack Boss tải lại
        cho chắc. Dữ liệu cũ của tab bị xoá, `ready` / `bosses` chờ khung mới. Không có tab (trình duyệt chưa mở) thì không làm gì; lỗi gửi lệnh thì bỏ qua."""
        self._refresh()
        with self._lock:
            tab = self._last.get(str(server))
            tabs = [tab] if tab is not None and tab.alive else [t for t in self._tabs.values() if t.alive]
        for tab in tabs:
            try:
                ws = websocket.create_connection(tab.socket_url, suppress_origin=True, timeout=5)
                try:
                    ws.send(json.dumps({"id": RELOAD_ID, "method": "Page.reload", "params": {"ignoreCache": True}}))
                finally:
                    ws.close()
            except (websocket.WebSocketException, OSError):
                continue
            with self._lock:
                tab.reset()

    def _tab(self, server, email, password):
        """Tab đã dùng được cho `server`, hoặc None khi còn đang chờ. Raises IScoutError."""
        self._login = (email, password)
        self._refresh()
        with self._lock:
            tabs = [t for t in self._tabs.values() if t.alive]
        if not tabs:
            now = self._clock()
            if self._launched is None:
                self._launcher(self._port)
                self._launched = now
            if now - self._launched < BROWSER_START_SECONDS:
                return None
            self._launched = None
            raise IScoutNotOpen()
        self._launched = None
        with self._lock:
            tab = pick_tab(tabs, server, self._last.get(str(server)))
            if tab is not None:
                self._last[str(server)] = tab
            return tab

    def _targets(self):
        try:
            tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{self._port}/json", timeout=2))
        except (OSError, ValueError):
            return {}
        return {t["id"]: (t["url"], t["webSocketDebuggerUrl"]) for t in tabs
                if t.get("type") == "page" and "iscout.club" in t.get("url", "") and "webSocketDebuggerUrl" in t}

    def _refresh(self):
        if time.monotonic() - self._scanned < RESCAN_SECONDS:
            return
        self._scanned = time.monotonic()
        targets = self._targets()
        with self._lock:
            for target in [t for t in self._tabs if t not in targets]:
                self._tabs.pop(target).alive = False
            for target, (url, socket_url) in targets.items():
                tab = self._tabs.get(target)
                if tab is not None and tab.alive:
                    if tab.login_page != ("/login" in url):     # vừa đăng nhập (hoặc đăng xuất): trang mới, tab nghe lại từ đầu
                        tab.alive = False
                    else:
                        tab.url = url
                        continue
                tab = self._tabs[target] = Tab(url, socket_url)
                threading.Thread(target=self._listen, args=(socket_url, tab), daemon=True).start()

    def _listen(self, url, tab):
        try:
            ws = websocket.create_connection(url, suppress_origin=True, timeout=5)
            ws.send(json.dumps({"id": 1, "method": "Network.enable"}))
            asked = logged = 0.0      # không tải lại trang: socket luôn đẩy boss mới nhất; khung đọc cả khi socket đã mở trước khi ta gắn vào
            while tab.alive:
                if tab.login_page and not tab.login_sent and all(self._login) and time.monotonic() - logged >= 1:
                    logged = time.monotonic()
                    script = LOGIN_JS.replace("__EMAIL__", json.dumps(self._login[0])).replace("__PASSWORD__", json.dumps(self._login[1]))
                    ws.send(json.dumps({"id": LOGIN_ID, "method": "Runtime.evaluate", "params": {"expression": script}}))
                if tab.configured is None and time.monotonic() - asked >= EVAL_EVERY:
                    asked = time.monotonic()
                    ws.send(json.dumps({"id": EVAL_ID, "method": "Runtime.evaluate", "params": {"expression": CONFIGURED_JS}}))
                try:
                    msg = json.loads(ws.recv())
                except websocket.WebSocketTimeoutException:
                    continue
                if msg.get("id") == LOGIN_ID:
                    tab.login_sent = msg.get("result", {}).get("result", {}).get("value") == "submitted"
                    continue
                if msg.get("id") == EVAL_ID:
                    value = msg.get("result", {}).get("result", {}).get("value")
                    if value:
                        tab.configured = int(value)
                    continue
                method, params = msg.get("method"), msg.get("params", {})
                if method == "Network.webSocketFrameReceived":
                    frame = parse_frame(params["response"]["payloadData"])
                    if frame:
                        with self._lock:
                            tab.apply(*frame)
        except (websocket.WebSocketException, OSError, ValueError, KeyError):
            pass
        finally:
            tab.alive = False


_hub = None


def get_hub():
    global _hub
    if _hub is None:
        _hub = IScoutHub()
    return _hub
