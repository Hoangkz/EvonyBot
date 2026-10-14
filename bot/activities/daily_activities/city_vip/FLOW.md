# Flow: City VIP

Nhiệm vụ Daily: nhận VIP ở thành. **Không có ô tích**: luôn bật khi chạy Daily Activities, cứ tới khung giờ (và có route trong DB) là đi nhận.
Code: [run.py](run.py), hằng số: [constants.py](constants.py).

## Luật chạy (đã làm)

- **Khung giờ**: chỉ làm khi giờ **máy tính** nằm trong [0h, 1h) (`WINDOW_START` / `WINDOW_END`). Ngoài khung giờ nhiệm vụ coi như không cần làm
  (`done` trả True), worker bỏ qua; vào khung giờ thì tự thành "chưa xong" và được làm.
- **Cần route**: chỉ làm khi máy đã có route công trình trong DB (`ctx.city_map`, do worker quét khi rảnh, xem [../../../city/FLOW.md](../../../city/FLOW.md)).
  Chưa có route thì không làm.
- **Xong**: nhận được thì lưu `City VIP: claimed` (xong hôm nay, hết hạn ở lần reset server theo giờ máy, mặc định 14:00). Khung 0h–1h luôn
  nằm trong một "ngày" tính từ 14:00 hôm trước, nên mỗi ngày nhận được tối đa một lần.

- **Ưu tiên 650**: cao nhất trong Event (cao nhất 600) và Daily Activities, nên vào khung giờ là làm trước mọi nhiệm vụ event / daily khác.

## Nhận VIP trong thành (`run.claim_vip`)

Nhận VIP = quà **Server Gift** ở hộp quà nổi trên đầu Tường thành.

1. Cần route trong DB; không có thì không làm. `city_map.goto` kéo **Tường thành** vào giữa màn (không tới được thì dừng, không lưu).
2. Tìm **hộp quà** trên đầu tường (chỉ trong vùng phía trên tường, `GIFT_AREA`). **Thấy luôn thì bỏ qua bước 3.**
3. Chưa thấy: bấm tường 1 cái, chờ menu (có Patrol) hiện, bấm lại đúng chỗ đó cho menu đóng (tường ở giữa màn), rồi tìm hộp quà (tối đa 3 lần,
   1 giây / lần). Vẫn không thấy thì dừng, không lưu.
4. Bấm hộp quà, chờ 1 giây xem ra màn **Server Gift** (tiêu đề), chưa ra thì chờ thêm tối đa 5 lần (1 giây / lần); sau 5 lần vẫn chưa ra thì bấm
   lại hộp quà, tối đa 3 lần bấm. Không ra thì dừng, không lưu.
5. Màn Server Gift: bấm **Claim All** (nút ở đáy, (198, 676)) và **lưu `City VIP: claimed` ngay** (xong), không chờ popup hay Back mới lưu; sau đó chờ 2 giây và Back về thành.

**Ảnh hộp quà**: có hiệu ứng nên hình đổi theo thời gian, và nền phía sau khác nhau theo civ. Vì vậy chỉ cắt phần **bên trong vòng tròn** icon (22x22,
không lấy nền) và cắt **8 ảnh** từ 60 khung hình (thư mục `Images/DailyActivites/ActivitiesCityVip/GiftBox/`), chọn sao cho mỗi khung hình khớp ít nhất
một ảnh. Cắt trên 21933 (civ3): khớp 0,89..0,99; trên ảnh civ1 (21913) khớp 0,82..0,87; ngưỡng 0,8.
