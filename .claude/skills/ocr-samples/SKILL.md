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

## Debug đọc sai
- Trả `None`: một ký tự dưới 0.6 → thiếu mẫu cho biến thể đó → thêm mẫu từ chính ảnh lỗi.
- Đọc nhầm chữ số (VD 3↔8): thêm mẫu đúng cho cả hai chữ số từ ảnh lỗi; nếu vẫn nhầm, kiểm tra crop có dính viền/nền không.
- Hai chữ số dính nhau: `split(..., max_ratio=...)` cắt ở cột mảnh nhất — xem reader tương ứng có truyền `max_ratio` chưa.
- Đừng xoá mẫu cũ trừ khi chắc nó sai (tên file không khớp chữ số).
