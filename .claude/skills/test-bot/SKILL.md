---
name: test-bot
description: Viết và chạy unit test cho EvonyBot không cần giả lập — giả lập BotContext/thiết bị bằng ảnh chụp tĩnh, test BossBoard, lịch ưu tiên boss của BotWorker, daily_reset, OCR. Dùng khi sửa bot/worker, bot/context, bot/common, logic activity, hoặc người dùng nói "test", "viết test", "chạy test", "kiểm thử".
---

# Test EvonyBot

Chạy từ thư mục gốc (Windows):
```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -t . -v
```

Test flow chính của activity theo chuỗi ảnh chụp màn hình (`tests/<activity>/screens/` + `tests/flow.py`) có skill riêng: `flow-test`. Skill này chỉ nói về unit test logic (worker, BossBoard, context, OCR...).
Dùng `unittest` chuẩn, không có pytest. File test đặt ở `tests/test_*.py`; thư mục con trong `tests/` cần `__init__.py` thì discover mới thấy.

## Tạo BotContext không cần thiết bị
`BotContext(device, stop_event, deadline, log)` chỉ đọc `device.serial` khi khởi tạo, nên:
```python
import threading
from types import SimpleNamespace
from bot.context import BotContext

ctx = BotContext(SimpleNamespace(serial="t"), threading.Event(), None, lambda _: None)
```
Để test logic nhận diện trên ảnh thật, truyền `screen=` cho `find/find_all/find_first` (không cần `screenshot()`), hoặc thay device bằng fake:
```python
from PIL import Image

class FakeDevice:
    serial = "t"
    def __init__(self, shots): self.shots, self.taps = list(shots), []
    def screenshot(self): return Image.open(self.shots.pop(0) if len(self.shots) > 1 else self.shots[0])
    def click(self, x, y): self.taps.append((x, y))
    def swipe(self, *a): pass
    def keyevent(self, key): self.taps.append(key)
    def shell(self, cmd): return ""
    def window_size(self): return (960, 540)   # khớp độ phân giải ảnh chụp
```
Activity chạy vòng `while True` → dừng test bằng `deadline` (`time.monotonic() + 2`) và `assertRaises(TimedOut)`, hoặc set `stop_event` từ trong fake (VD sau N lần tap) rồi `assertRaises(StopRequested)`. Patch `bot.common.delay` / truyền deadline ngắn để test không chậm.

Ảnh chụp màn hình dùng cho test để trong `tests/<activity>/screens/` (theo skill `flow-test`), không để trong `Images/` (thư mục đó ship theo installer).

## Các mẫu test đã có (xem `git show HEAD:tests/test_boss_notifications.py`)
- **BossBoard**: `BossBoard(clock=lambda: now[0])` để điều khiển thời gian; kiểm tra lọc server, không báo lại worker nguồn, chống trùng 120 s / 10 s khi không có toạ độ, `unregister`.
- **Ngắt**: `ctx._boss_event.set()` chỉ ném `BossAvailable` khi `ctx._boss_interrupt_enabled = True`; Stop luôn ưu tiên trước.
- **Lịch ưu tiên boss**: tạo `BotWorker(serial, [JOIN_BOSS, "x"], {"Initialization": {"server": "1"}}, boss_board=board, server_clock=ServerClock("known"))`, gán `worker.ctx`, thay `worker._run_activity` bằng hàm ghi lại lời gọi và trả `BOSS_IDLE`, rồi gọi thẳng `worker._run_tasks()` (không `start()` QThread). Vòng lặp sống tới khi Stop: trong hàm giả, đủ kịch bản thì `worker._stop.set()` và bắt `StopRequested` (hoặc vòng lặp thoát ở `while`). Độ ưu tiên: patch `bot_worker.load_priorities`. Assert thứ tự `calls` (mỗi vòng 1 lượt Join Boss + 1 nhiệm vụ) và `ctx._deadline is None`, `_boss_interrupt_enabled is False` sau cùng. Mẫu: tests/test_scheduler.py, tests/test_boss_notifications.py.
- **daily_reset**: truyền `now=` cố định vào `last_reset` / `done_today`.

## Lưu ý
- Hành vi tổng thể worker được mô tả ở [bot/worker/FLOW.md](../../../bot/worker/FLOW.md) và Join Boss ở [bot/activities/join_monster_war/FLOW.md](../../../bot/activities/join_monster_war/FLOW.md). Khi đổi hành vi, cập nhật FLOW.md tương ứng và test.
- Test chỉ xác nhận logic; báo rõ cho người dùng là chưa kiểm trên giả lập thật nếu chưa chạy app.
