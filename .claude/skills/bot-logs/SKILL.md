---
name: bot-logs
description: Ghi log cho EvonyBot — chọn giữa bot.log (Info, không lưu) và bot.record (History, lưu DB bảng logs), thêm sự kiện mới vào activity / worker, đọc tab Logs và bảng logs trong DB. Dùng khi viết hoặc sửa activity, thêm thông báo, người dùng nói "log", "ghi log", "lưu log", "history", "lịch sử", "tab Logs", hoặc hỏi bot đã làm gì / lỗi gì.
---

# Log của EvonyBot

Có **2 loại log**, cả hai hiện ở tab **Logs** của từng thiết bị:

| | `bot.log(msg)` | `bot.record(msg)` |
| --- | --- | --- |
| Hiện ở | Logs > **Info** (giờ `HH:MM:SS`) | Logs > **History** (ngày giờ) **và** Info |
| Lưu DB | Không — mất khi tắt app, tab giữ 2000 dòng gần nhất | Có — bảng `logs`, chỉ thêm, **không bao giờ sửa / xoá** |
| Hiện trên tab | Chỉ 1 giờ gần nhất (`SHOW_SECONDS`) | Chỉ 1 giờ gần nhất; DB vẫn giữ đủ |
| Dùng cho | Từng bước, toạ độ, điểm khớp, "đang vuốt tìm", "bấm lại" | Sự kiện người dùng cần biết sau này |

Trong test / chạy tay (`BotContext(..., log=print)`), `bot.record` mặc định = `log`, nên không cần DB.

## Khi nào dùng `bot.record`

Dùng `record` cho:
- **Bắt đầu / xong** một nhiệm vụ hoặc một nhiệm vụ con (VD `Event: xong {key}`, `{NAME}: ... done`).
- **Dừng / bỏ qua có lý do**: ngày hoặc tier còn khoá, hết vật phẩm, hết thể lực, hết búa, hết kim cương.
- **Hành động tốn tài nguyên / quan trọng**: dùng bubble, dùng thể lực, mua bằng gem, nhận thưởng, tham gia boss.
- **Khôi phục**: tắt game (force-stop), mở lại game, bấm Try Again, `go_home` khi màn hình không nhận ra.
- **Thất bại sau khi đã thử lại**: không thấy nút / màn hình sau N lần, quá số bước / số vòng rồi dừng.

Giữ `bot.log` cho các bước trung gian còn đang thử lại (VD "not found, swiping", "tapping again",
"Màn hình: ..." mỗi vòng). Mỗi lần thử mà ghi History thì History sẽ bị đầy. Chỉ ghi lần **cuối cùng** khi đã bỏ cuộc.

Nội dung nên có: tên activity / nhiệm vụ ở đầu (`f"{NAME}: ..."`), lý do, con số liên quan (tiến độ, số lần).

## Worker tự ghi (không cần thêm trong activity)

[bot/worker/bot_worker.py](../../../bot/worker/bot_worker.py) — `BotWorker.record()` đã ghi:
- Bắt đầu chạy bot (danh sách activity), bot đã dừng.
- `Bắt đầu: X` / `Xong: X` / `Tạm dừng: X (hết 120 giây | có boss mới)` / `Dừng: X (người dùng bấm Stop)`.
- `Hoàn thành: <task>` mỗi lần activity gọi `bot.mark_daily_done(task)` — không cần `record` thêm cho việc xong.
- `Đọc được server`, Join Monster War dừng hẳn, Bubble không đủ kim cương.
- **Lỗi làm bot dừng**: `Lỗi khi chạy <activity>: <Loại>: <nội dung> (tại file.py:dòng) -> bot dừng`;
  traceback đầy đủ ở Info. Activity **không cần** bắt exception chỉ để ghi log.

## Đường đi của một dòng `record`

```
activity: bot.record(msg)                    # ctx.record = BotWorker.record (gán trong BotWorker.run)
  -> BotWorker.record: self.log(msg) + history.emit(serial, msg)
  -> BotManager.history  -> MainWindow._on_history (main.py)
       -> db.add_log(serial, msg, created_at)    # đưa vào hàng đợi, thread db-writer ghi nền
       -> DeviceView.append_history -> LogsTab.history_view
```

- **Bot không chờ DB**: `Database._write` chỉ `queue.put`; signal Qt giữa thread là queued. Đừng đổi sang
  ghi đồng bộ trong worker.
- Mở app: `_register_device` nạp `db.load_logs(serial, since)` (trong 1 giờ gần nhất, tối đa 500 dòng) vào History.
- Tab Logs chỉ hiện log trong `SHOW_SECONDS` (3600) gần nhất: `LogsTab` có QTimer mỗi phút ẩn các dòng cũ hơn
  khỏi màn hình (chỉ ẩn trên UI, không đụng DB). Đổi thời gian: sửa `SHOW_SECONDS` trong `ui/tabs/logs_tab.py`.
- `bot.log` đi theo signal `log_message` -> `_on_log_message` -> `LogsTab.append` (không đụng DB).

## Thêm sự kiện mới

1. Trong activity / `bot/common`: đổi `bot.log(...)` thành `bot.record(...)` (hoặc thêm dòng mới) theo tiêu chí ở trên.
2. Trong worker: gọi `self.record(...)`.
3. Code chạy ngoài BotContext (UI, manager): emit `BotManager.history` / gọi `db.add_log(serial, msg)`.
4. **Không** thêm hàm sửa / xoá cho bảng `logs`, và không thêm nút Clear vào tab Logs (người dùng chốt).
5. Kiểm tra cú pháp nhanh: `.\venv\Scripts\python.exe -m py_compile <file>`. Chỉ chạy test khi người dùng yêu cầu
   (xem skill `test-bot`).

## Đọc log trong DB

DB: `%LOCALAPPDATA%\EvonyBot\evonybot.db`, bảng `logs(id, serial, created_at, message)`, index `(serial, id)`.

```powershell
.\venv\Scripts\python.exe -c "from database import Database; db=Database(); [print(t, m) for t, m in db.load_logs('SERIAL', 100)]; db.close()"
```

Hoặc truy vấn thẳng (VD tìm lỗi):
```powershell
.\venv\Scripts\python.exe -c "import sqlite3, os; c=sqlite3.connect(os.path.expandvars(r'%LOCALAPPDATA%\EvonyBot\evonybot.db')); [print(*r) for r in c.execute(\"SELECT serial, created_at, message FROM logs WHERE message LIKE 'Lỗi%' ORDER BY id DESC LIMIT 50\")]"
```

## File liên quan

- [ui/tabs/logs_tab.py](../../../ui/tabs/logs_tab.py) — `LogsTab` (Info + History, chỉ đọc).
- [ui/device_view.py](../../../ui/device_view.py) — tab Logs không nằm trong `get_settings` / `set_settings` / Apply ALL.
- [database.py](../../../database.py) — `add_log`, `load_logs`, bảng `logs`.
- [bot/context/bot_context.py](../../../bot/context/bot_context.py) — `self.record` mặc định = log.
- [bot/worker/manager.py](../../../bot/worker/manager.py) — chuyển tiếp `log_message`, `history`.
