---
name: template-images
description: Chụp màn hình giả lập, cắt ảnh template vào Images/ và đo điểm khớp (threshold) của template trên màn hình thật cho EvonyBot. Dùng khi thêm/sửa ảnh nhận diện, bot không bấm được nút, khớp nhầm, cần chọn threshold hoặc region, hoặc debug "tại sao find() trả None".
---

# Ảnh template & nhận diện màn hình

## Cách nhận diện hoạt động
- Template là file `.png` trong [Images/](../../../Images/), gọi bằng đường dẫn tương đối: `"JoinBoss/hettheluc.png"` ([bot/context/templates.py](../../../bot/context/templates.py)).
- `bot.find()` dùng `cv2.matchTemplate(..., TM_CCOEFF_NORMED)` trên ảnh BGR, **so khớp theo pixel, không co giãn** → template phải cắt từ giả lập cùng độ phân giải/DPI với máy chạy bot.
- Ngưỡng mặc định `DEFAULT_THRESHOLD = 0.9`. Ảnh dễ thay đổi (chữ, số, nền động) thường dùng 0.7–0.8.
- `region=(x0, y0, x1, y1)` theo **% màn hình** giới hạn vùng tìm; toạ độ trả về vẫn là toạ độ toàn màn hình.
- Thư mục dùng chung:
  - `Images/exit/` — popup đóng bằng BACK (`exit_images()`)
  - `Images/click/` — nút cứ thấy là bấm (`click_images()`)
  - `Images/en/`, `Images/vi/` — ảnh phụ thuộc ngôn ngữ game
  - `Images/OCR/` — mẫu chữ số cho OCR (xem skill `ocr-samples`), **không** phải template nút
- `images_in(folder)` lấy mọi `.png` trong thư mục, sắp theo tên → thêm file vào thư mục là tự được dùng; đặt tên có số (`1.png`, `2.png`) nếu thứ tự quan trọng.

## Công cụ: scripts/probe.py

[scripts/probe.py](scripts/probe.py) chạy bằng venv của project, dùng adbutils có sẵn (không cần adb trong PATH):

```powershell
# Liệt kê thiết bị
.\venv\Scripts\python.exe .claude\skills\template-images\scripts\probe.py devices

# Chụp màn hình về file
.\venv\Scripts\python.exe .claude\skills\template-images\scripts\probe.py shot -s 127.0.0.1:5555 -o shot.png

# Cắt template từ ảnh chụp (x y w h theo pixel) và lưu vào Images/
.\venv\Scripts\python.exe .claude\skills\template-images\scripts\probe.py crop shot.png 812 540 96 40 -o JoinBoss/newbutton.png

# Đo template trên thiết bị (hoặc trên file với --image): in điểm cao nhất, vị trí, và mọi hit >= threshold
.\venv\Scripts\python.exe .claude\skills\template-images\scripts\probe.py match JoinBoss/thamgia.png -s 127.0.0.1:5555 --threshold 0.8 --region 0 30 100 90
```

Lưu ảnh chụp tạm vào thư mục scratchpad, không commit vào repo.

## Quy trình thêm template
1. Chụp màn hình đúng trạng thái cần nhận diện (`shot`). Đọc ảnh bằng Read để xem và xác định toạ độ.
2. Cắt vùng **nhỏ, đặc trưng, ít thay đổi** (tránh số đếm, thời gian, avatar, nền trong suốt/động). Có thể cắt hẹp vào icon/chữ thay vì cả nút.
3. `match` trên chính ảnh đó → điểm ≈ 1.0. Rồi `match` trên vài màn hình **khác** (màn hình gần giống, trạng thái khác) để chắc điểm của chúng thấp hơn ngưỡng rõ ràng.
4. Chọn threshold nằm giữa hai mức đó; nếu khoảng cách hẹp, thêm `region` hoặc cắt template khác.
5. Thêm vào `_targets()` / constants của activity đúng thứ tự ưu tiên.

## Debug "không bấm" / "bấm nhầm"
- `find()` trả None: chạy `match` → điểm cao nhất là bao nhiêu? Gần ngưỡng → hạ threshold hoặc cắt lại template; rất thấp → sai độ phân giải/ngôn ngữ, hoặc màn hình không như mong đợi.
- Khớp nhầm: kiểm tra template nào đứng **trước** trong `_targets()` cũng khớp màn hình đó; thêm region hoặc đổi thứ tự.
- `find_all` gộp hit chồng nhau trong nửa kích thước template.
- Template lớn hơn vùng tìm → `_match` trả None (không lỗi).
