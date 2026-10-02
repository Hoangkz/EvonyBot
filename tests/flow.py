"""
flow.py — chạy một activity trên chuỗi ảnh chụp màn hình thật (skill flow-test).

Mỗi Step(ảnh, *actions): khi thiết bị đang hiện `ảnh`, bot phải làm đúng các
action đó theo thứ tự; làm xong action cuối thì thiết bị chuyển sang ảnh của
bước kế tiếp. Bước cuối là end() nếu activity tự return; không có end() thì
làm xong bước cuối harness bật Stop và activity phải ném StopRequested.

Thời gian là đồng hồ giả: sleep/delay không chờ thật, nên test chạy nhanh.
"""
import threading
import time
from pathlib import Path
from unittest import mock

import cv2
import numpy as np
from PIL import Image

from bot.context import TEMPLATE_DIR, BotContext, StopRequested, TimedOut

TAP_THRESHOLD = 0.8     # điểm khớp tối thiểu để coi template có trên ảnh
STUCK_SECONDS = 120     # giây giả tối đa cho mỗi bước trước khi coi là kẹt
_NO_RESULT = object()


class FlowError(AssertionError):
    """Bot làm khác kịch bản."""


# ---- actions ---------------------------------------------------------
class _Action:
    kind = ""

    def match(self, event, screen) -> str | None:
        """None nếu `event` khớp, ngược lại là lý do không khớp."""
        raise NotImplementedError


class _Tap(_Action):
    kind = "tap"

    def __init__(self, template, threshold):
        self.template, self.threshold = template, threshold

    def __repr__(self):
        return f"tap({self.template!r})"

    def match(self, event, screen):
        if event[0] != "tap":
            return "không phải tap"
        tpl = cv2.imread(str(TEMPLATE_DIR / self.template))
        h, w = tpl.shape[:2]
        result = cv2.matchTemplate(screen, tpl, cv2.TM_CCOEFF_NORMED)
        best = float(result.max())
        if best < self.threshold:
            return f"template không có trên ảnh (điểm cao nhất {best:.3f})"
        x, y = event[1], event[2]
        for ty, tx in zip(*np.where(result >= self.threshold)):
            if tx - 2 <= x <= tx + w + 2 and ty - 2 <= y <= ty + h + 2:
                return None
        return "tap nằm ngoài vùng template"


class _TapAt(_Action):
    kind = "tap"

    def __init__(self, x, y, tol, percent):
        self.x, self.y, self.tol, self.percent = x, y, tol, percent

    def __repr__(self):
        return f"{'tap_pct' if self.percent else 'tap_at'}({self.x}, {self.y})"

    def match(self, event, screen):
        if event[0] != "tap":
            return "không phải tap"
        x, y = self.x, self.y
        if self.percent:
            h, w = screen.shape[:2]
            x, y = w * x / 100, h * y / 100
        if abs(event[1] - x) > self.tol or abs(event[2] - y) > self.tol:
            return f"lệch quá {self.tol}px so với ({int(x)}, {int(y)})"
        return None


class _Back(_Action):
    kind = "back"

    def __repr__(self):
        return "back()"

    def match(self, event, screen):
        return None if event[0] == "back" else "không phải back"


class _Swipe(_Action):
    kind = "swipe"

    def __init__(self, points, tol):
        self.points, self.tol = points, tol

    def __repr__(self):
        return f"swipe{tuple(self.points) if self.points else '()'}"

    def match(self, event, screen):
        if event[0] != "swipe":
            return "không phải swipe"
        if not self.points:
            return None
        h, w = screen.shape[:2]
        got = (event[1] * 100 / w, event[2] * 100 / h, event[3] * 100 / w, event[4] * 100 / h)
        if any(abs(g - p) > self.tol for g, p in zip(got, self.points)):
            return f"vuốt {tuple(round(g, 1) for g in got)} (%)"
        return None


class _Shell(_Action):
    kind = "shell"

    def __init__(self, text):
        self.text = text

    def __repr__(self):
        return f"shell({self.text!r})"

    def match(self, event, screen):
        return None if event[0] == "shell" and self.text in event[1] else "lệnh shell khác"


def tap(template: str, threshold: float = TAP_THRESHOLD):
    """Tap nằm trong khung của `template` (đường dẫn dưới Images/) trên ảnh hiện tại."""
    return _Tap(template, threshold)


def tap_at(x: int, y: int, tol: int = 15):
    return _TapAt(x, y, tol, percent=False)


def tap_pct(x: float, y: float, count: int = 1, tol: int = 15):
    return [_TapAt(x, y, tol, percent=True) for _ in range(count)]


def back(count: int = 1):
    return [_Back() for _ in range(count)]


def swipe(x1=None, y1=None, x2=None, y2=None, tol: float = 3):
    """Vuốt theo % màn hình; không truyền toạ độ = chấp nhận mọi lần vuốt."""
    points = None if x1 is None else (x1, y1, x2, y2)
    return _Swipe(points, tol)


def shell(text: str):
    return _Shell(text)


class end:
    """Activity phải return ở bước này (và trả về `result` nếu có)."""

    def __init__(self, result=_NO_RESULT):
        self.result = result


class Step:
    def __init__(self, screen: str, *actions):
        self.screen = screen
        self.end = None
        self.actions: list[_Action] = []
        for a in actions:
            if isinstance(a, end):
                self.end = a
            elif isinstance(a, list):
                self.actions.extend(a)
            else:
                self.actions.append(a)
        if not self.actions and self.end is None:
            raise ValueError(f"{screen}: bước không có action phải là end()")


# ---- thiết bị & context giả -----------------------------------------
class _Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


class FlowDevice:
    serial = "flow-test"

    def __init__(self, steps, images, clock, stop):
        self.steps, self.images, self.clock, self.stop = steps, images, clock, stop
        self.index = 0          # bước hiện tại
        self.done = 0           # số action đã làm trong bước hiện tại
        self.finished = False   # đã làm hết mọi action của bước cuối
        self.events = []        # mọi thao tác bot đã gửi
        self.reported = []      # toạ độ bot.report_boss()
        self.shells = []
        self.shots = 0          # số lần bot chụp màn hình

    # -- trạng thái
    def fake_time(self):
        """Context manager: time.monotonic() trả đồng hồ giả của lần chạy, để
        assert trạng thái có hạn (VD BossMemory) sau khi run_flow trả về."""
        return mock.patch.object(time, "monotonic", self.clock)

    @property
    def step(self) -> Step:
        return self.steps[self.index]

    def where(self) -> str:
        return f"bước {self.index + 1:02d} ({self.step.screen})"

    def _screen(self) -> np.ndarray:
        return self.images[self.step.screen][1]

    # -- API adbutils mà BotContext dùng
    def screenshot(self):
        self.shots += 1
        self.clock.now += 0.05
        return self.images[self.step.screen][0]

    def window_size(self):
        h, w = self._screen().shape[:2]
        return w, h

    def click(self, x, y):
        self._event(("tap", int(x), int(y)))

    def swipe(self, x1, y1, x2, y2, duration=0.3):
        self._event(("swipe", x1, y1, x2, y2))

    def keyevent(self, key):
        self._event(("back",) if "BACK" in str(key) else ("key", key))

    def shell(self, command):
        if "dumpsys window" in command:
            return "  mCurrentFocus=Window{0 u0 com.topgamesinc.evony/com.tap4fun.GameActivity}"
        expected = self._expected()
        if expected is not None and expected.kind == "shell":
            self._event(("shell", command))
        else:
            self.shells.append(command)
        return ""

    # -- so khớp
    def _expected(self):
        if self.finished or self.done >= len(self.step.actions):
            return None
        return self.step.actions[self.done]

    def _event(self, event):
        self.events.append((self.index, event))
        expected = self._expected()
        if expected is None:
            raise FlowError(f"{self.where()}: kịch bản đã hết action nhưng bot còn gửi {event}")
        reason = expected.match(event, self._screen())
        if reason is not None:
            raise FlowError(f"{self.where()}, action {self.done + 1}: mong đợi {expected!r}, "
                            f"bot gửi {event} — {reason}")
        self.done += 1
        if self.done == len(self.step.actions):
            if self.index + 1 < len(self.steps):
                self.index += 1
                self.done = 0
            elif self.step.end is None:
                self.finished = True
                self.stop.set()     # hết kịch bản -> lần check() kế tiếp ném StopRequested


class FlowContext(BotContext):
    def __init__(self, device, stop, clock, log):
        super().__init__(device, stop, None, log)
        self._clock = clock

    def sleep(self, seconds: float):
        self.check()
        self._clock.now += seconds
        self.check()


# ---- chạy ------------------------------------------------------------
def run_flow(testcase, run, screens_dir: Path, flow: list[Step], settings: dict, *,
             ctx_settings: dict | None = None, daily_done: dict | None = None,
             setup=None, variants: dict | None = None) -> FlowDevice:
    """Chạy `run(ctx, settings)` trên các ảnh của `flow`; fail/skip `testcase`
    nếu bot làm khác kịch bản hoặc còn thiếu ảnh. `setup(ctx)` được gọi ngay
    trước khi chạy (trong đồng hồ giả), VD để nạp sẵn trạng thái. Trả về
    FlowDevice để assert thêm (`device.ctx` là BotContext đã dùng).

    Ảnh "<file>.png?<biến thể>" là ảnh <file> đã qua `variants[<biến thể>]`
    (hàm nhận ảnh BGR, trả ảnh BGR): ảnh TỔNG HỢP cho trạng thái chưa có ảnh
    chụp thật, chỉ dùng khi chỗ bị sửa không liên quan tới điều đang test."""
    screens_dir = Path(screens_dir)
    variants = variants or {}
    missing = sorted({s.screen.split("?")[0] for s in flow
                      if not (screens_dir / s.screen.split("?")[0]).exists()})
    if missing:
        testcase.skipTest(f"thiếu ảnh trong {screens_dir}: " + ", ".join(missing))
    for s in flow:
        for a in s.actions:
            if isinstance(a, _Tap) and not (TEMPLATE_DIR / a.template).exists():
                testcase.fail(f"{s.screen}: template không tồn tại: Images/{a.template}")

    images = {}
    for name in {s.screen for s in flow}:
        file, _, variant = name.partition("?")
        bgr = cv2.cvtColor(np.array(Image.open(screens_dir / file).convert("RGB")), cv2.COLOR_RGB2BGR)
        if variant:
            bgr = variants[variant](bgr.copy())
        images[name] = (Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)), bgr)

    clock, stop, logs = _Clock(), threading.Event(), []
    device = FlowDevice(flow, images, clock, stop)
    ctx = FlowContext(device, stop, clock, logs.append)
    ctx.settings = ctx_settings or {}
    ctx.report_boss = device.reported.append
    done = dict(daily_done or {})
    ctx.is_daily_done = lambda task: task in done
    ctx.mark_daily_done = lambda task: done.__setitem__(task, "flow-test")
    device.daily_done = done
    device.logs = logs
    device.ctx = ctx

    with mock.patch.object(time, "monotonic", clock):
        if setup is not None:
            setup(ctx)
        ctx._deadline = clock.now + STUCK_SECONDS * len(flow)
        try:
            result = run(ctx, settings)
        except StopRequested:
            if not device.finished:
                testcase.fail(f"StopRequested ngoài dự kiến ở {device.where()}")
            return device
        except TimedOut:
            testcase.fail(f"kẹt ở {device.where()}: đã làm {device.done}/{len(device.step.actions)} "
                          f"action, thao tác cuối: {device.events[-3:]}, log: {logs[-5:]}")
        except FlowError as e:
            testcase.fail(str(e))

    step = device.step
    if step.end is None or device.done < len(step.actions):
        testcase.fail(f"activity return sớm ({result!r}) ở {device.where()}")
    if step.end.result is not _NO_RESULT:
        testcase.assertEqual(result, step.end.result, f"giá trị trả về ở {device.where()}")
    return device
