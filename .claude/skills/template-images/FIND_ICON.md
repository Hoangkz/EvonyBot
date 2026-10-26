# Tự tìm ảnh mẫu cho icon có hiệu ứng (find_icon.py)

Icon nút event (VD lâu đài ma dưới "Event Center") có ánh sáng chạy liên tục, nên một ảnh cắt
ngẫu nhiên có thể chỉ khớp 0,18–0,8 với chính nó ở khung khác. Script
[scripts/find_icon.py](scripts/find_icon.py) tự chụp nhiều khung, thử các cách cắt và chọn **ít ảnh
nhất** sao cho khung nào cũng khớp ≥ 0,8, rồi tự kiểm tra lại trên khung mới.

## Chạy

Mở giả lập ở **màn hình chính** (thấy chữ Event Center và icon bên dưới), rồi:

```powershell
.\venv\Scripts\python.exe .claude\skills\template-images\scripts\find_icon.py --name haunted_castle
```

Mất khoảng 2–4 phút (chụp 4 đợt x 30 khung, ~0,45 giây/khung; phần còn lại là tính). Ảnh lưu vào
`Images/Event/ButtonIcon/<name>.png` (nhiều ảnh thì `<name>_1.png`, `<name>_2.png`...).

| Tham số | Mặc định | Ý nghĩa |
|---|---|---|
| `--name` | (bắt buộc) | tên file ảnh lưu ra |
| `-s` | thiết bị đầu tiên | serial giả lập, VD `127.0.0.1:21923` |
| `--bursts` / `--frames` | 4 / 30 | số đợt / số khung mỗi đợt. Cần >= 3 đợt để kiểm tra chéo. Chạy cuối báo chưa đạt thì tăng |
| `--threshold` | 0.8 | ngưỡng khớp cần đạt |
| `--region X0 Y0 X1 Y1` | 60 0 100 50 | vùng tìm (% màn hình), mặc định góc trên phải |
| `--anchor` | `Event/eventCenter.png` | ảnh neo để biết icon nằm đâu |
| `--core DX DY W H` | -12 32 26 20 | lõi icon: lệch so với **tâm neo** và kích thước. Đúng cho icon dưới Event Center |
| `--abs X Y` | | bỏ neo, đặt thẳng góc trái-trên của lõi (pixel) |
| `--out` | `Event/ButtonIcon` | thư mục lưu trong `Images/` |
| `--no-save` | | chỉ đo, không lưu |

## Đọc kết quả

1. Dòng đầu in vị trí lõi và đường dẫn ảnh `find_icon_core.png` (thư mục tạm, phóng 8 lần). **Mở ra
   xem**: lõi chỉ được chứa phần bên trong icon, không dính viền, chấm đỏ, ruy băng đếm ngược. Nếu dính
   thì chỉnh `--core` nhỏ lại (hoặc đổi `DX DY`) rồi chạy lại.
2. Bảng từng ô thử: `ô 18x12 tại (4,0): 1 ảnh, chéo 1.000, thấp nhất 0.87`.
   - *chéo* = tỉ lệ khung đạt ≥ ngưỡng khi ảnh được chọn từ các đợt khác (đo độ tổng quát, không bị quá khớp).
   - *thấp nhất* = điểm thấp nhất trong phép đo chéo.
3. Dòng `CHỌN`: ô được chọn = chéo 100% trước, rồi ít ảnh nhất, rồi điểm thấp nhất cao nhất.
4. `KIỂM TRA`: một đợt khung **mới**, tìm trong cả vùng góc trên phải. Mong muốn: đạt `N/N`, đúng
   vị trí `N/N`, chỗ khác trong vùng tìm thấp hơn 0,65 (tức cách ngưỡng ít nhất 0,15).
5. `KẾT LUẬN: ổn` mới nên dùng. Nếu `CHƯA ĐẠT`: tăng `--bursts 6 --frames 40`, hoặc icon đang bị che
   (popup, chấm đỏ đổi chỗ) -> về màn hình chính sạch rồi chạy lại.

## Dùng ảnh trong bot

Ảnh lưu là ảnh màu bình thường, **nhưng chỉ đạt điểm trên khi khớp qua hàm `laplacian()`** (xám -> mờ 5x5
-> Laplacian) áp lên cả ảnh mẫu và vùng tìm. `bot.find()` hiện so ảnh màu thẳng nên **không dùng
được trực tiếp**: dùng `find_icon(screen, templates, region, threshold)` trong script làm mẫu và viết
hàm riêng cho activity (xem ghi nhớ "viết riêng, không refactor `valuable_event`").

- Tìm trong **vùng góc trên phải** (mặc định `60 0 100 50`), không tìm cả màn hình: ảnh nhỏ (18x12)
  nên tìm cả màn hình dễ khớp nhầm.
- Toạ độ trả về là góc trái-trên của ảnh mẫu; icon có thể lệch 1–4 px giữa các khung. Muốn bấm thì
  bấm tâm ảnh (+ nửa kích thước), đừng dùng toạ độ cố định.
- Không thấy ở lần chụp đầu thì chụp lại tối đa 3 lần cách nhau 1 giây trước khi kết luận.

## Số đo thực tế (icon lâu đài ma, máy 21923, 2026-10-26)

- 8 đợt x 30 khung = 240 khung, mỗi khung ~0,45 giây.
- Ảnh màu thẳng (không biến đổi): cần 7–10 ảnh, chéo ~98%, điểm thấp nhất 0,71–0,75.
- Laplacian có mờ 5x5, ô 18x12 tại (4,0) trong lõi 26x20 (lõi tại (347,205) trên màn 396x704): **1 ảnh**,
  chéo 100%, thấp nhất 0,87; 60 khung mới 60/60 đạt (thấp nhất 0,847), chỗ khác trong vùng tìm 0,49.
- Đã thử và bỏ: cạnh Canny, hue, saturation, mặt nạ màu vàng, mặt nạ vùng tối (cần hàng chục đến hàng
  trăm ảnh).

## Giới hạn

- Chỉ đo trên một máy, tài khoản và màn hình chính. Event khác / máy khác phải chạy lại.
- Hàng trăm khung chụp trong vài phút có thể chưa phủ hết chu kỳ hiệu ứng dài. Muốn chắc hơn, chạy
  script vài lần ở các thời điểm khác nhau (`--no-save` để chỉ đo với ảnh đang có thì phải sửa thêm;
  hiện chạy lại sẽ chọn ảnh mới).
- Khi event đổi giao diện icon thì phải chạy lại.
