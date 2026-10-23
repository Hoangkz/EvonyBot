# Flow: Alliance VIP

Nhiệm vụ Daily: mua sách "100 VIP Points" ở Alliance Shop, hai loại (Monthly và Daily). Ô tích **Alliance VIP** ở tab Daily
Activities, mặc định tích (thiếu cấu hình = tích). Ảnh / hằng số: [constants.py](constants.py), code: [run.py](run.py). Không nhận thưởng
sau khi mua: mua xong là xong.

Mỗi loại có dấu "xong hôm nay" riêng trong `daily_done`: `Alliance VIP: Monthly`, `Alliance VIP: Daily`. Cả hai có thì nhiệm vụ xong
(`JOB["done"]`); chỉ phần còn thiếu được làm.

```mermaid
flowchart TD
    A[Màn chính -> Liên minh -> Alliance Shop] --> B{Cần Monthly?}
    B -->|có| C[Sách VIP TRÊN tiêu đề Daily Sale]
    C --> D{Nút giá xanh?}
    D -->|xám| E[Không mua, lưu Monthly xong]
    D -->|xanh| F[Bấm nút giá -> popup mua]
    F --> G[+ 5 lần -> bấm mua -> Confirm -> lưu Monthly xong]
    E --> H
    G --> H{Cần Daily?}
    B -->|không| H
    H -->|có| I[Kéo thật nhanh xuống cuối trang]
    I --> J[Sách VIP giữa Daily Sale và Weekly Sale]
    J -->|thấy| D2{Nút giá xanh?}
    D2 -->|xám| K[Lưu Daily xong]
    D2 -->|xanh| L[Giá -> popup -> + 5 lần -> mua -> Confirm -> lưu Daily xong]
    J -->|tới tiêu đề Weekly Sale mà không có sách| K
```

- **Phân biệt hai sách bằng tiêu đề nhóm**: Monthly nằm trên tiêu đề "Daily Sale" (`DailySale.png`, đầu trang), Daily nằm giữa "Daily Sale"
  và "Weekly Sale" (`WeeklySale.png`, ở cuối trang, ngay dưới sách Daily). Tiêu đề nào ra khỏi màn thì dùng tiêu đề còn lại.
- **Nút giá**: xanh (độ bão hoà màu >= 100) = mua được; xám (VD chưa có thẻ tháng, độ bão hoà ~35) = coi như đã mua, đánh dấu xong
  luôn. Bấm **nút giá** mới hiện popup mua (bấm vào sách thì không).
- **Ba Truce Agreement** dùng cùng hình con chim nên không chỉ dựa vào
  điểm template. Sau khi khớp hình, bot so thêm histogram HSV của nền:
  `8h` tím, `24h` cam, `3d` vàng. Bot luôn chọn loại có dải màu
  gần nhất, không có nhánh PENDING do ngưỡng màu. Nếu khung hiếm khi
  không đủ pixel bão hòa, bot phân loại bằng độ tương đồng full-colour.
- **Popup mua**: bấm giá xong chờ 1 giây, chưa có popup (tìm nút "+") thì chờ thêm tối đa 5 lần (1 giây / lần); sau 5 lần vẫn không có
  popup thì vẫn lưu xong. Có popup: bấm "+" 5 lần rồi bấm nút mua (dưới thanh số lượng) -> hiện hộp xác nhận -> bấm **Confirm** mới là mua thật, SAU ĐÓ mới lưu DB. Chờ Confirm tối đa 5 giây; không có Confirm mà popup mua còn mở, hoặc sau Confirm hộp vẫn còn thì Back, không lưu.
- **Cuộn**: vừa vào shop đưa danh sách về đầu để ưu tiên Tribute và 100 VIP
  Points. Sau đó quét/mua mọi món đang thấy rồi mới vuốt chậm 1 giây và chờ
  thêm 1 giây. Trần an toàn là 32 lượt. `Weekly Sale` là mốc
  cuối: ngay khi nhận diện được mốc này, bot vẫn lướt và quét thêm
  đúng 2 khung rồi mới xác nhận đã tới cuối.
- **Lỗi / không tới được shop**: không lưu dấu, lần sau làm lại; lỗi lưu `daily_alliance_vip_error` vào DB.

## Số đo (máy 21913, 396x704)
- Dòng "Alliance Shop" ở màn Liên minh 1,00; tiêu đề shop 1,00. Sách VIP: Monthly (206, 218) 1,00, Daily 0,90..0,92 (ngưỡng 0,85).
- Tiêu đề "Daily Sale" (199, 494) 1,00; "Weekly Sale" (199, 543 khi hiện) 1,00. Nút "+" của popup khớp 0,98 với ảnh của Buy Stamina.
