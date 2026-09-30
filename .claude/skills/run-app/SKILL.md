---
name: run-app
description: Cài môi trường, chạy EvonyBot (PyQt5) từ source và đọc log để debug activity trên giả lập Android qua ADB. Dùng khi người dùng muốn chạy app, "poe dev", cài venv/requirements, bot không kết nối được giả lập, hoặc cần xem log/trạng thái worker.
---

# Chạy EvonyBot từ source

Task được định nghĩa trong [pyproject.toml](../../../pyproject.toml) (poethepoet), `poe` nằm trong venv:

| Lệnh | Việc |
| --- | --- |
| `python -m venv venv` (`poe setup`) | Tạo venv — cần **Python 3.12 64-bit** (build installer đòi đúng 3.12) |
| `venv\Scripts\poe install` | `pip install -r requirements.txt` (index mirror Tencent đặt sẵn trong requirements.txt) |
| `venv\Scripts\poe dev` | Chạy app = `venv\Scripts\python.exe main.py` |
| `venv\Scripts\poe build` / `clean` | Xem skill `release` |

`poe dev` mở cửa sổ GUI và chặn cho tới khi đóng → chạy nền (`run_in_background`) và đọc output.

## Dữ liệu & log
- Database: `%LOCALAPPDATA%\EvonyBot\evonybot.db` (SQLite, bảng `devices`, mỗi tab một cột JSON). Dùng chung giữa bản source và bản cài — **cẩn thận** khi sửa/xoá, đó là cấu hình thật của người dùng.
- Log: `print` ra stdout, dạng `[<serial>] <message>` (từ `BotWorker.log` / `ctx.log`). Lỗi cuối lượt chạy: `[<serial>] Error: ...`.
- Không có file log; muốn giữ log thì chạy app qua terminal và lưu output.

## ADB / giả lập
- Kết nối qua thư viện `adbutils` (có adb server riêng), không cần `adb` trong PATH. Liệt kê thiết bị:
  ```powershell
  .\venv\Scripts\python.exe -c "import adbutils; print([(d.serial, d.window_size()) for d in adbutils.adb.device_list()])"
  ```
- Giả lập phải bật ADB; serial thường dạng `127.0.0.1:<port>` hoặc `emulator-5554`. Tab Initialization có nút quét ADB ([ui/workers/adb_scan_worker.py](../../../ui/workers/adb_scan_worker.py)).
- Game package: `com.topgamesinc.evony` (`go_home()` tự mở lại game khi đang ở launcher).
- Template so khớp theo pixel → độ phân giải giả lập phải khớp với ảnh trong `Images/` (xem skill `template-images`).

## Debug một activity
1. Chạy app, chọn đúng một activity trên một thiết bị, Start, theo dõi log.
2. Bot đứng yên / lặp BACK: màn hình hiện tại không khớp template nào trong `_targets()` → chụp màn hình và đo bằng `probe.py match` (skill `template-images`).
3. Muốn chạy thử activity không cần GUI:
   ```powershell
   .\venv\Scripts\python.exe -c "import threading, time, adbutils; from bot.context import BotContext; from bot.activities import ACTIVITIES; d=adbutils.adb.device(serial='SERIAL'); ctx=BotContext(d, threading.Event(), time.monotonic()+120, print); ACTIVITIES['Open Gift Box'](ctx, {...settings của tab...})"
   ```
   `deadline` 120 s để nó tự dừng bằng `TimedOut`. Đây là thao tác thật trên tài khoản game — hỏi người dùng trước khi chạy.
