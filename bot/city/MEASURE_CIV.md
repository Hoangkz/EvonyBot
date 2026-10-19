# Đo route thành cho một nền văn minh mới — cách đã làm với civ2

Bổ sung cho mục "Hướng dẫn đo route" trong [FLOW.md](FLOW.md). Công cụ ở [tests/city/measure/](../../tests/city/measure/): chạy bằng
`.\venv\Scripts\python.exe tests\city\measure\<tên>.py ...`, máy và civ đặt bằng biến môi trường `EVONY_SERIAL` (mặc định `127.0.0.1:21933`) và `EVONY_CIV` (mặc định `2`).
Ví dụ PowerShell: `$env:EVONY_SERIAL="127.0.0.1:21943"; $env:EVONY_CIV="3"`. Các script chỉ in ra màn hình, ảnh chụp lưu ở thư mục tạm (`%TEMP%`).

## Chuẩn bị
1. Tạo `bot/city/civ<N>/__init__.py` + `city_tour.py` (copy khung của civ2: `COMPLETE = False`, `FIXED / ANCHOR_SHIFT / ROUTES = {}`, `DATA = []`) và thêm civ vào `ALL` trong [tours.py](tours.py).
2. Máy ở màn thành, có ảnh mẫu `Images/Building/civ<N>/<công trình>/1.png` (kiểm bằng `look.py`). **Ảnh mẫu cắt ở GIỮA công trình, nhỏ (~60-100 px), không lấy nước / nền đất** (tài khoản khác nước, ô đất xung quanh khác).
   Ảnh cũ cắt xấu khớp chỉ 0,3 - 0,55; ảnh cắt đúng khớp 0,9 - 1,0. Cắt lại: `probe.py shot` rồi `probe.py crop <ảnh> x y w h -o <đường dẫn> --force`, xem ảnh cắt, kiểm `probe.py match`.
3. Về Thành chính ở giữa màn mà không cần vuốt: `go_keep.py` (mở Activity -> Gold Levy -> Go). Dùng mỗi khi lạc đường, vì sai số cộng dồn nhanh.

## Quy ước toạ độ (đã kiểm chứng)
- Vuốt `finger = (dx, dy)` làm nội dung dịch (dx, dy). Công trình ở `lech = (vị trí ảnh mẫu - (197, 345))`: lệch trái thì tăng dx, lệch trên thì tăng dy, nghĩa là bù = `-lech`.
- `view` = tổng ngón tay từ Thành chính tới khi công trình ra giữa màn. Cú vuốt `city_map.swipe(finger)` đối xứng quanh (190, 340).
- Cú vuốt dài > ~320 px không ổn định (lệch tới 60 px, quán tính / camera chạm mép thành): chia nhiều cú bằng nhau; chiều đi và chiều về có thể chênh 40-130 px nên **ghi riêng từng chiều theo số đo thật**.
- Công trình cố định (Walls, Research Factory, Tavern, Archer Tower, Watchtower, Art Hall, Pasture, Rally Spot) ở vị trí gần giống civ1 (người dùng xác nhận): lấy `FIXED` của civ1 làm ước lượng ban đầu.

## Quy trình đo
1. **Dò khắp thành (`explore.py <file.json>`)**: đi zigzag (sửa `path` trong file), mỗi bước chụp màn và ghi mọi công trình khớp >= 0,5; camera theo dõi bằng công trình trùng nhau giữa 2 ảnh (không có thì lấy tổng vuốt). Sau đó gộp: `view = camera - (vị trí ảnh mẫu - (197, 345))`, trung bình các lần thấy (cùng công trình lệch nhau 10-30 px). Cho ra `view` của 11 / 13 ô.
2. **Công trình không nhận ra**: nhìn ảnh chụp (`look.py <ảnh.png> dx,dy ...` vuốt rồi chụp + in điểm khớp), hỏi người dùng chỉ vị trí, cắt lại ảnh mẫu, tính `view` từ ảnh mẫu mới.
3. **Sinh `DATA` (`gen.py <giới_hạn_dx>`)**: sửa danh sách `views` trong file, chia cú đều (ô gần 1 cú, ô xa nhiều cú, giới hạn mỗi cú ~(320, 260)), ghi `DATA` vào `civ<N>/city_tour.py`.
4. **Chạy thử tour (`tour_test.py [ô,ô,...]`)**: từ Thành chính đi qua các ô theo `DATA`, in công trình ra giữa màn và lệch. Chấp nhận lệch <= ~50 px (scan có bước kéo bù, `TOLERANCE` 25). Đường thẳng giữa 2 ô bất kỳ: `pairs.py 5-11 9-2 ...` (về Thành chính, tới ô A, rồi thẳng tới ô B).
5. **Mốc cố định**: `leg.py <từ> <tới> <tổngDX> <tổngDY> <n> [fromkeep]` vuốt n cú bằng nhau rồi **tìm xung quanh**, bù tới khi công trình ra giữa (<= 12 px) và in `ROUTE` đo thật. Làm lần lượt Walls, Archer Tower (qua Walls), Research Factory, Watchtower / Art Hall (qua Research Factory), Pasture (qua Art Hall), Tavern, Rally Spot. Chiều về cũng đo bằng `leg.py` (không chỉ đảo dấu).
   `ANCHOR_SHIFT`: công trình có 2 phần (Tháp cung thủ) thì "giữa" là tâm cả hai; ghi vị trí ảnh mẫu khi tâm ở giữa màn trừ (197, 345).
6. **Kiểm từng route đã ghi (`rr.py <từ> <tới> [fromkeep]`)**: chạy đúng `ROUTES[(từ, tới)]`, in lệch của đích (đã cộng `ANCHOR_SHIFT`). Chạy từng đôi đi + về, luôn bắt đầu từ Thành chính chuẩn (`fromkeep`), vì chạy nối tiếp thì sai số của đoạn trước cộng vào đoạn sau. Lệch > ~50 px thì chỉnh lại số đó (chạy lại từ Thành chính lệch thì trừ phần lệch).
7. Khi 13 ô và mọi `(mốc, 'keep')` đều chạy được: `COMPLETE = True`, cập nhật `tests/city/test_city_map.py` (xem FLOW.md bước 5), chạy `scan_city` thật (FLOW.md bước 6).

## Mẹo / lỗi gặp
- `visible()` dùng ngưỡng 0,9 nên bỏ sót công trình có ảnh mẫu yếu; khi dò dùng ngưỡng thấp (0,5) kèm kiểm bằng mắt, rồi cắt lại ảnh mẫu.
- Điểm vuốt đầu trúng icon (rương, dấu hỏi) thì không dịch: `city_map.swipe` đã vuốt lại bằng điểm khác (`RETRY_SHIFTS`).
- Chương trình lạc đường -> `go_keep.py`. Nếu báo "Activity list not opened" thì chạy lại (popup che màn).
- Công trình giả khớp (VD `stables` / `battlefield` khớp ~0,5 ở nhiều nơi): chỉ tin điểm >= 0,8 hoặc kèm xác nhận bằng mắt.
