# Flow: Alliance Help

Nhiệm vụ Daily Activities "Complete Alliance Help for 5 time(s)". Ảnh: [constants.py](constants.py), flow:
[run.py](run.py). Khung chung theo giờ (giống Alliance Donation): [../hourly.py](../hourly.py).

Tab UI: ô chọn giờ thay cho ô tích — **0 / 1h / 2h / 3h / 4h** (mặc định 4h, `INTERVAL_*`); 0 = không làm.

1. Chạy **cuối** Daily Activities, **ngay sau Alliance Donation** (`../run.py` `HOURLY`, không ưu tiên). Bỏ qua nếu đã
   xong hôm nay, hoặc chưa đủ số giờ kể từ lần thử trước (`TRIED_KEY` trong daily_done).
2. Màn chính → **Liên minh** → dòng **"Alliance Help"** (thấy ngay, không cần cuộn) → màn Alliance Help.
3. **"No records"** (không ai cần giúp, `NoRecords.png`) → Back, sang nhiệm vụ khác: **không** kiểm tra Activity,
   **không lưu gì vào DB** (kể cả giờ thử).
4. Có nút **"Help All"** → bấm → chờ danh sách trống ("No records" hiện lại — lúc này **vẫn** đi nhận quà, khác bước 3
   là "No records" trước khi bấm) → Back → lưu giờ thử (`TRIED_KEY`) → kiểm tra dòng / thẻ Activity như Alliance Donation
   (`../hourly.py` `check_done`, không bấm Go): xong → đánh dấu xong hôm nay (lưu DB), trong ngày không kiểm tra lại.
5. Chưa xong → `bot.again_after`: worker hẹn chạy lại Daily Activities sau số giờ đã chọn, độ ưu tiên thấp nhất.

Không có luồng C# cũ (`ACTIONS` rỗng, không chạy qua `common.run_task`).
