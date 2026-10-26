# Bộ ảnh mẫu cho icon nút event có animation (find_icon.py)

Icon nút event (lâu đài ma, cốc bia, giỏ trái cây... ngay dưới "Event Center") có ánh sáng chạy liên tục nên một
ảnh cắt ra chỉ khớp 0,2–0,9 với các khung khác. Cách làm: **mỗi trạng thái animation một ảnh mẫu**, bỏ hết vào
`Images/Event/ButtonIcon/`; bot nhận icon nếu **bất kỳ ảnh nào** khớp ≥ 0,8 (`bot/activities/event/button_icon.py`).
Số ảnh mỗi event không cố định (lâu đài 2, giỏ trái cây 1, cốc bia 4). **Dùng ít ảnh nhất có thể**: mỗi ảnh là thêm một lần khớp ở mỗi
lần tìm icon. Script lấy MỌI khung làm ứng viên rồi chọn bộ nhỏ nhất phủ mọi khung (phủ tập tối ưu); thêm ảnh từng cái từ khung điểm thấp
nhất cho ra gấp nhiều lần (cốc bia: 16 ảnh so với 4 ảnh tối ưu, cùng phủ ≥ 0,85).

**Mục tiêu phủ là 0,85 (`--cover`), KHÔNG sát ngưỡng 0,8 của bot**: mọi khung phải có ít nhất một ảnh khớp ≥ 0,85 để ngoài
thực tế (nền khác, ánh sáng khác) điểm có dư 0,05 trước khi tụt dưới 0,8. Khung nào dưới 0,85 thì cắt thêm ảnh.

## Quy trình (cũng là thuật toán của script)

1. Cắt một ảnh (hoặc `--seed` ảnh cắt tay).
2. Với mọi khung đã có, tính điểm khớp. Khung nào dưới **0,85** → cắt thêm ảnh từ khung đó (chọn khung phủ được nhiều khung
   chưa đạt nhất), lặp đến khi mọi khung đều khớp ≥ 0,85.
3. Khung phải **trải đủ chu kỳ animation**: chụp nhiều đợt, cách nhau vài giây (`--gap`). Script in số ảnh cần khi thêm từng đợt:
   nếu đợt sau vẫn đòi ảnh mới thì chưa gặp đủ trạng thái, tăng `--bursts`.
4. Kiểm tra bằng **chính hàm của bot** trên mọi ảnh màn thành chính trong `tests/`, lấy hàm ruy băng làm chuẩn.
5. Ảnh bị sót (ruy băng thấy nút, icon không) mà là event này → `--add-from ẢNH...` cắt thêm. Ảnh nhận được nhưng điểm
   < 0,85 (sát ngưỡng) → `--add-from near` tự cắt thêm lặp lại cho đến khi không còn ảnh nào dưới 0,85.

## Chạy

Mở giả lập ở **màn thành chính** (thấy Event Center và icon bên dưới), rồi:

```powershell
.\venv\Scripts\python.exe .claude\skills\template-images\scripts\find_icon.py --name haunted_castle
```

Chụp 6 đợt x 30 khung, nghỉ 10 giây giữa các đợt (~3–5 phút, khung ~0,45 giây). Ảnh lưu `Images/Event/ButtonIcon/<name>.png`,
nhiều ảnh thì `<name>_2.png`, `<name>_3.png`...

| Tham số | Mặc định | Ý nghĩa |
|---|---|---|
| `--name` | (bắt buộc) | tên file ảnh lưu ra |
| `-s` | thiết bị đầu tiên | serial giả lập, VD `127.0.0.1:21923` |
| `--bursts` / `--frames` / `--gap` | 6 / 30 / 10 | số đợt / số khung mỗi đợt / giây nghỉ giữa các đợt |
| `--images GLOB...` | | dùng ảnh chụp có sẵn (glob từ gốc repo) thay vì chụp giả lập |
| `--seed ẢNH` | | ảnh cắt tay làm ảnh đầu tiên; ô cắt lấy theo ảnh này (VD cốc bia 32x20) |
| `--add-from ẢNH...` / `near` | | chỉ cắt THÊM ảnh mẫu từ các ảnh này (ảnh bị sót), hoặc `near` = mọi ảnh điểm < `--cover`; rồi đo lại |
| `--cover` | 0.85 | điểm tối thiểu bộ ảnh phải phủ trên **mọi** khung (cao hơn ngưỡng bot để có dư địa) |
| `--threshold` | 0.8 | ngưỡng khớp của bot (`BUTTON_ICON_THRESHOLD`), dùng khi đo bằng hàm của bot |
| `--core DX DY W H` | -12 32 26 20 | lõi tìm ô cắt, lệch so với **tâm chữ Event Center**. KHÔNG được dính viền, chấm đỏ, ruy băng |
| `--corpus GLOB...` | `tests/**/*.png` | ảnh dùng để kiểm tra bằng hàm của bot |
| `--out` | `Event/ButtonIcon` | thư mục lưu trong `Images/` |
| `--no-save` | | chỉ đo, không lưu |

Ví dụ: cắt tay cốc bia rồi để script thêm ảnh còn thiếu từ các ảnh chụp có sẵn:

```powershell
find_icon.py --name beer_mugs --seed beer_crop.png --images "tests/event/screens/event_center/*.png" "tests/event/*/screens/03_main.png"
find_icon.py --name beer_mugs --add-from tests/event/city_building/screens/civ5/war_hall/01.png
```

## Đọc kết quả

1. Dòng đầu in đường dẫn `find_icon_core.png` (lõi icon phóng 8 lần, trong thư mục tạm). **Mở ra xem**: chỉ được có phần bên trong icon.
   Dính viền / chấm đỏ / chữ đếm ngược thì chỉnh `--core`.
2. Bảng từng ô thử: `ô 18x12 tại (-8,32): 2 ảnh, chéo 1.000, thấp nhất 0.87`. *Chéo* = tỉ lệ khung đạt ≥ ngưỡng khi bộ ảnh được
   chọn từ các đợt khác (đo độ tổng quát). Ô được chọn: chéo 100% → ít ảnh nhất → ô lớn nhất → điểm thấp nhất cao nhất.
3. **Số ảnh cần khi thêm từng đợt**: phải ngừng tăng và đợt sau được phủ hết thì mới đủ trạng thái animation.
4. **Kiểm tra bằng hàm của bot**: *đúng nút* = icon và ruy băng trỏ cùng nút (lệch ≤ 25 px); *ruy băng không thấy nút* = thường do popup
   che (vẫn tốt); **icon nhận sai nút phải bằng 0**; **sát ngưỡng (điểm < 0,85) phải bằng 0**, còn thì `--add-from near`;
   *ruy băng thấy nút, icon không nhận* = event khác chưa có mẫu, hoặc khung
   của event này còn sót → `--add-from`. Màn có menu/popup che nút event (VD menu Keep) làm ruy băng báo nút ma: bỏ qua.
5. `KẾT LUẬN: ổn` mới nên dùng.

## Chỉ đo trên màn thành chính

Icon chỉ được tìm khi bot đã ở màn thành chính (nút "•••", `MAIN_SCREEN`). Mọi phép đo (khớp nhầm, bị sót) chỉ dùng ảnh màn thành chính trong
`tests/` (lọc bằng `ctx.find(MAIN_SCREEN, screen=img)`); bỏ qua popup, menu, màn khác. `find_icon.py` làm sẵn việc này.

## Cách bot khớp (button_icon.py)

- Vùng dò `BUTTON_ICON_REGIONS` (% màn hình): vùng 1 x 70–100 / y 25–55, vùng 2 x 60–90 / y 0–55 (`bot/activities/event/constants.py`).
  Nút event ở 3 chỗ tuỳ layout: cột phải dưới Event Center, cột trái dưới Event Center (283, 145), cột trái hàng trên (283, 77) khi
  Event Center bị đẩy xuống đáy; hai vùng phủ cả ba.
- Điểm của một ảnh mẫu = **điểm cao hơn của khớp màu thẳng và khớp Laplacian** (xám → mờ 5x5 → Laplacian, áp lên cả ảnh mẫu và vùng tìm).
  Ảnh nhỏ nhiều nét: Laplacian tốt hơn. Ảnh to phẳng (bọt cốc bia 32x20): chỉ khớp màu thẳng tốt (0,81–0,89), Laplacian tự khớp chính
  khung cắt chỉ 0,4–0,65 vì hiệu ứng viền.
- Toạ độ bấm = tâm ảnh mẫu khớp tốt nhất; icon lệch 1–4 px giữa các khung nên không dùng toạ độ cố định.
- Không có ảnh nào khớp (event mới chưa có mẫu, popup che...) → rơi về tìm đuôi ruy băng như trước.
- Khi đo, **đừng coi chỗ không nằm dưới Event Center là khớp nhầm**: ở layout cột trái nút event nằm chỗ khác (đã từng đo sai kiểu này,
  báo 341 "khớp nhầm" cho cốc bia, thật ra là nút đúng). Chuẩn đúng/sai là hàm ruy băng.

## Số đo thực tế (517 ảnh màn thành chính trong tests/, 2026-10-26)

| Event | Ảnh mẫu | Nhận trên | Đúng nút | Sai nút |
|---|---|---|---|---|
| Cốc bia | 4 (`beer_mugs`, `beer_mugs_2` … `_4`; 32x20; phủ riêng 463 / 430 / 269 / 2 khung, ảnh thứ 4 là trạng thái hiếm "hết bọt") | 480 | 480 | 0 |
| Lâu đài ma | 2 (`haunted_castle`, `haunted_castle_2`; 18x12) | 20 | 20 | 0 |
| Giỏ trái cây | 1 (`fruit_basket`; 10x8) | 15 | 14 | 1 (`city_exit_dialog`: ruy băng báo điểm khác, icon trỏ đúng nút dưới Event Center) |

Tất cả ảnh có nút event trong `tests/` đều thuộc 3 event này; ảnh duy nhất bị sót là menu Keep (không có nút event).
**Phân bố điểm tốt nhất trên 510 ảnh có nút event** (bộ 7 ảnh): ≥ 0,90: 274; 0,85–0,90: 235; **0,80–0,85: 0**; < 0,80: 1 (menu Keep, 0,77).
Lịch sử cốc bia: 3 ảnh ban đầu → 93 ảnh trong 0,80–0,85 (thấp nhất 0,801); thêm từng ảnh bằng `--add-from near` → 16 ảnh mới hết dưới 0,85;
phủ tập tối ưu trên 475 khung → **4 ảnh** phủ ≥ 0,85 (2 ảnh nếu chỉ cần ≥ 0,80, 3 ảnh nếu ≥ 0,83).
Kiểm tra tổng quát (chọn từ một nửa số khung, thử trên nửa còn lại, 8 lần chia): 100% khung đạt ≥ 0,80 và 95–100% đạt ≥ 0,85 (lần dùng 3 ảnh tụt 0,577 ở
trạng thái hiếm → giữ ảnh thứ 4); chia theo nhóm thư mục test (nền khác hẳn): 100% đạt ≥ 0,85.

Bài học khi chọn ảnh: ô càng to càng nhạy với lấp lánh nên càng cần nhiều ảnh (cốc bia ô 38x27 cần 12 ảnh cho 13 khung, không tổng quát được);
ảnh phẳng nhỏ (10x8 bọt trắng) khớp mọi vật sáng. Cắt tay một ảnh 32x20 gồm cả viền cốc rồi thêm ảnh theo quy trình trên hiệu quả nhất.

## Giới hạn

- Số đo trên ảnh test, một máy / tài khoản; chưa chạy live với bộ ảnh mới. Event mới / máy khác: chạy `find_icon.py` lại.
- Hàng trăm khung trong vài phút có thể chưa phủ hết chu kỳ dài: đọc bảng "số ảnh cần khi thêm từng đợt", chạy lại ở thời điểm khác nếu còn tăng.
- Khi event đổi giao diện icon thì phải chụp lại.
