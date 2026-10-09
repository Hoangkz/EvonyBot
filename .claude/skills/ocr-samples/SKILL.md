---
name: ocr-samples
description: Thêm mẫu chữ số cho OCR của EvonyBot (Images/OCR/<font>/) và debug khi đọc sai toạ độ boss, số, server hay giờ server. Dùng khi OCR trả None / đọc sai, cần hỗ trợ font số mới, hoặc người dùng nhắc "OCR", "đọc số", "đọc toạ độ", "read_coords", "add_sample".
---

# Mẫu OCR chữ số

OCR của project **không dùng Tesseract**: [bot/ocr/_digits.py](../../../bot/ocr/_digits.py) nhị phân hoá ảnh (Otsu), tách từng ký tự theo cột trống, scale về 12×20 rồi so với các mẫu trong `Images/OCR/<font>/`.

- Mẫu: ảnh đen trắng, cắt sát ký tự, tên `<digit>_<n>.png` (VD `7_3.png`).
- Font hiện có: `Coords` (toạ độ boss `X:Y`), `Number`, `Server` — xem `FONT = ...` trong từng `read_*.py`.
- Ký tự có điểm < `MIN_SCORE = 0.6` → cả chuỗi coi như không đọc được (`None`).
- Dấu `,`/`.` và `:` được nhận theo hình dạng, không cần mẫu.
- Nhiều mẫu cho một chữ số (các biến thể anti-alias / nền khác nhau) làm đọc ổn định hơn.

## Thêm mẫu

1. Lấy ảnh vùng số **đúng như bot crop** (VD Join Boss crop `80 × 15` ngay bên phải icon LOCATION). Cách nhanh: chụp màn hình bằng skill `template-images` (`probe.py shot`) rồi crop đúng vùng đó ra file tạm trong scratchpad.
2. Chạy từ thư mục gốc project:
   ```powershell
   .\venv\Scripts\python.exe -m bot.ocr.add_sample <Font> <ảnh.png> <text>
   ```
   `<text>` đánh vần mọi mảnh trái → phải: chữ số, `,` và `:` đúng như trong ảnh, `_` cho mảnh cần bỏ (VD cái ghim vị trí). Ví dụ:
   ```powershell
   .\venv\Scripts\python.exe -m bot.ocr.add_sample Coords shot.png _0951:0663
   ```
   Lỗi `image splits into N pieces, text has M` → `<text>` sai số mảnh (thường do hai chữ số dính nhau hoặc có mảnh nhiễu); đọc ảnh để đếm lại hoặc crop sạch hơn.
3. Script chỉ **thêm** file mới (`<digit>_<n+1>.png`), không ghi đè.
4. Kiểm tra lại:
   ```powershell
   .\venv\Scripts\python.exe -c "import cv2; from bot.ocr import read_coords; print(read_coords(cv2.imread(r'shot.png')))"
   ```

## Tên boss (font `Name`)

[bot/ocr/read_boss_name.py](../../../bot/ocr/read_boss_name.py) đọc nhãn "(Boss) <tên> [cấp]" trên thẻ rally. Nó khác OCR số ở mấy điểm:
- Tách chữ theo **màu vàng** (không dùng Otsu), mẫu lưu dạng xám mềm. Khoảng trống từ 4px là dấu cách.
- Nhãn mẫu viết **chữ thường**. Một mẫu có thể là nhiều chữ dính nhau (`ryt_1.png`, `ot_1.png`).
- Mảnh không khớp mẫu nào đọc thành `?`. [boss_names.py](../../../bot/activities/join_monster_war/boss_names.py) coi `?` là 1–3 chữ bất kỳ khi khớp với tên trong `ui/tabs/boss.py`.

Thêm mẫu khi log hiện `Boss (x, y): '...' -> không nhận ra`:
1. Cắt nhãn tên đúng như bot cắt: góc trên-trái nút Join `(x, y)`, vùng `(x - 95, y - 90)` rộng 168 cao 30 (`NAME_*` trong `run.py`). Lấy `x, y` bằng `probe.py match JoinBoss/thamgia.png --image <ảnh>` (dòng "top-left").
   - Tên dài xuống 2 dòng thì tách từng dòng bằng `read_boss_name.lines(crop)` và thêm mẫu cho từng dòng riêng.
2. Chạy thử `add_sample` với `<text>` sai. Thông báo lỗi sẽ in ra các mảnh (`#` là một mảnh, dấu cách là khoảng trống), từ đó biết chữ nào dính nhau.
3. Chạy lại với `<text>` đúng, mỗi mảnh cách nhau bằng `|`. Dùng `_` cho mảnh đã có mẫu hoặc không cần lưu:
   ```powershell
   .\venv\Scripts\python.exe -m bot.ocr.add_sample Name name.png "_|_|_|_|_|_| |y|a|s|h|a"
   ```
4. Lấy mẫu từ cả thẻ trên và thẻ dưới nếu có. Hai thẻ lệch nhau nửa pixel nên chữ nhỏ (ngoặc, `i`) trông khác nhau.
5. Thêm ảnh thẻ vào `tests/join_monster_war/screens/` và một dòng trong `test_reads_name_on_every_card`.

## Lực boss (font `Power`)

[bot/ocr/read_power.py](../../../bot/ocr/read_power.py) đọc số lực bên phải thanh trên cùng thẻ rally, VD `6.5M` thành `6500000`. Cách làm giống font `Name`: tách theo màu (chữ trắng xám), mẫu dạng xám mềm. Dấu `.` nhận theo chiều cao, không cần mẫu. Mẫu gồm chữ số và đơn vị `k`/`m`/`b`, viết chữ thường.

- Vùng cắt: `(x - 10, y - 180)`, rộng 65, cao 20, so với góc trên-trái nút Join.
- Thêm mẫu: `.\venv\Scripts\python.exe -m bot.ocr.add_sample Power power.png "6|.|5|m"`. Dùng `_` cho mảnh đã có mẫu.
- Lực chỉ được đọc cho boss có cấp mà tên không có chữ tier. Bot chọn cấp có `power` (trong `ui/tabs/boss.py`) gần nhất.

## Debug đọc sai
- Trả `None`: một ký tự dưới 0.6 → thiếu mẫu cho biến thể đó → thêm mẫu từ chính ảnh lỗi.
- Đọc nhầm chữ số (VD 3↔8): thêm mẫu đúng cho cả hai chữ số từ ảnh lỗi; nếu vẫn nhầm, kiểm tra crop có dính viền/nền không.
- Hai chữ số dính nhau: `split(..., max_ratio=...)` cắt ở cột mảnh nhất — xem reader tương ứng có truyền `max_ratio` chưa.
- Đừng xoá mẫu cũ trừ khi chắc nó sai (tên file không khớp chữ số).
