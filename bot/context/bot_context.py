"""
bot_context.py — BotContext: one adbutils device plus the worker's stop
flag and deadline, with the helpers from the mixins.
"""
import threading

import numpy as np

from .device_input import InputMixin
from .flow import FlowMixin
from .screen import ScreenMixin


class BotContext(FlowMixin, InputMixin, ScreenMixin):
    def __init__(self, device, stop_event: threading.Event, deadline: float | None, log):
        self.device = device
        self.serial = device.serial
        self._stop = stop_event
        self._deadline = deadline    # time.monotonic() value, or None for no limit
        self._boss_event = threading.Event()
        self._boss_interrupt_enabled = False
        # Việc `idle_only` đang chạy: hàm trả True khi có nhiệm vụ khác tới lượt (worker gán, gỡ sau khi xong); check() ném YieldToTask.
        self._idle_abort = None
        # time.monotonic() lúc cần quay lại xử lý bubble (None = không theo dõi).
        self._bubble_due_at: float | None = None
        # time.monotonic() lúc tới giờ Auto Times Out: đóng game (None = không theo dõi).
        self._restart_due_at: float | None = None
        # time.monotonic() lúc tới mốc reset server kế tiếp: tắt game bật lại, kể cả khi đang chạy nhiệm vụ must_finish
        # (None = không theo dõi). Khác Bubble / Auto Times Out, không bị hoãn bởi must_finish.
        self._reset_due_at: float | None = None
        self.report_boss = lambda coords: None
        # Server của tài khoản (số trong "S. 1257", chuỗi rỗng = chưa biết): worker gán khi đọc được; boss_scan dùng làm khoá danh sách boss đã chia sẻ.
        self.server = ""
        # Daily Activities: task đã xong từ lần reset gần nhất chưa / đánh dấu xong.
        self.is_daily_done = lambda task: False
        self.mark_daily_done = lambda task: None
        # Giờ (ISO) lưu `task` trong daily_done, kể cả ngày cũ; None nếu chưa có.
        self.done_at = lambda task: None
        # Xoá key khỏi daily_done (worker xoá cả trong DB).
        self.forget_daily = lambda task: None
        # Craft: một trang bị vừa chế tạo xong (id "ring/05_Tên"); worker báo UI trừ 1 ở tab Craft và lưu DB.
        self.craft_done = lambda item_id: None
        # Mọi key đang có trong daily_done (kể cả ngày cũ), VD tìm "<key>_reached_<mục tiêu>".
        self.daily_keys = lambda: []
        # Giờ reset server "HH:MM" (màn Home); worker gán BotWorker.server_time.
        self.server_time = lambda: "14:00"
        # Nền văn minh của tài khoản (1 .. 7, None = chưa biết), bot tự xếp từ ảnh công trình
        # (activities/event/city_building.py); worker gán set_civilization để lưu DB.
        self.civilization: int | None = None
        self.set_civilization = lambda civ: setattr(self, "civilization", civ)
        # Bản đồ thành của thiết bị ({công trình: [x, y]}, bot/city/city_map.py); worker gán set_city_map
        # để lưu DB.
        self.city_map: dict = {}
        self.set_city_map = lambda city_map: setattr(self, "city_map", dict(city_map))
        self._log = log
        # Sự kiện đáng lưu lịch sử (DB + tab Logs > History); worker gán BotWorker.record,
        # mặc định (test / chạy tay) chỉ là log thường.
        self.record = log
        self._templates: dict[str, np.ndarray] = {}
        self._window_size: tuple[int, int] | None = None
        # Every tab's config ({tab title: settings}), for activities that
        # chain into another one (e.g. Open Gift Box -> Black Market).
        self.settings: dict = {}
