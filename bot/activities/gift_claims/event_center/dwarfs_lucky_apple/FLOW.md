# Dwarf's Lucky Apple

1. Mở Event Center, chọn Activities bằng ảnh chữ và tìm đúng dòng Dwarf's Lucky Apple.
2. Xác nhận title, chọn táo xanh bằng một trong hai ảnh
   `tab_green_apple` hoặc `tab_green_apple_1`; cả hai dùng chính tâm ảnh tìm
   được làm vị trí bấm.
3. Kiểm tra riêng x100 và x10 trên táo xanh, mỗi ảnh được chụp lại tối đa ba
   lần để phân biệt nút không xuất hiện với một frame đang đổi sáng:
   - Có đủ x100, x10 và Once: bấm x100 đến xám, rồi bấm x10 đến xám.
   - Không có x100 nhưng có x10 và Once: bỏ qua x100, bấm x10 đến xám.
   - Chỉ có Once: không bấm thêm ở táo xanh.
   Once không bao giờ được dùng để bỏ qua một nút x100/x10 còn ACTIVE.
   `status_green_wish_once` và `status_green_wish_once_gray` chỉ cho phép
   chuyển sang táo đỏ sau khi mọi nút multiplier đang xuất hiện đã xám.
4. Chọn táo đỏ bằng `tab_red_apple` hoặc `tab_red_apple_1`, rồi kiểm tra x10
   trước Once:
   - Có x10 và Once: bấm `button_red_wish_x10` liên tục cho tới
     `status_red_wish_x10_done`; lúc đó DONE toàn nhiệm vụ.
   - Chỉ có Once: `status_red_wish_once` (ảnh vàng `073767`) hoặc
     `status_red_wish_once_gray` (ảnh xám `073769`) đều là DONE toàn nhiệm vụ.
   Không được kiểm tra Once trước rồi bỏ qua x10 đang ACTIVE.
5. Mỗi lần thấy `Congratulations!` đều tap cố định
   `(195, 20)` ở vùng title phía trên để đóng popup, rồi kiểm tra lại nút trên
   ảnh màn hình mới. Sau khi đóng popup phải chờ ít nhất 1 giây; tuyệt đối
   không so ảnh `DONE/ACTIVE` trên khung hình vẫn còn `Congratulations!`, và
   không dùng Back vì Back có thể thoát khỏi trang sự kiện. Ngay sau một lần
   bấm nút nhận Apple, nếu hiệu ứng làm template `Congratulations!` nhận hụt,
   bot vẫn phải tap an toàn `(195, 20)` một lần trước khi xét trạng thái mới.
6. Mọi ảnh trạng thái DONE phải xác minh thêm cả hoa văn viền trái và viền phải
   của template. Nếu thiếu một trong hai viền thì không được kết luận DONE.
7. ACTIVE/DONE còn được phân biệt bằng dải màu HSV 70x24 ở tâm nút. Nút vàng
   ACTIVE phải có độ bão hòa trung bình ít nhất `110` và tối thiểu `35%` pixel
   có saturation từ `100`; nút xám DONE phải có trung bình không quá `65` và
   tỷ lệ pixel màu không quá `20%`. Điểm template chỉ dùng để định vị; nếu ảnh
   DONE khớp cao nhưng dải vẫn vàng thì phải tiếp tục bấm, không được chuyển
   pha. DONE chỉ hợp lệ khi đồng thời đủ dải xám và hai viền hoa văn.
8. Nếu ảnh nút đang chuyển sáng làm nhận dạng mơ hồ, bot ở nguyên trong nhiệm
   vụ và chụp lại mỗi 1 giây; ba lần không đọc được không được chuyển PENDING
   hoặc Back ra danh sách. Chỉ bộ đếm 120 giây của worker mới được ngắt để quay
   lại Join Boss, rồi lần chạy sau tiếp tục nhiệm vụ chưa DONE.
   Ngay khi vào Dwarf, log ghi rõ deadline worker còn bao nhiêu giây.
   Nếu log báo không có deadline thì Join Boss không hoạt động hoặc
   worker đang chờ thể lực; Dwarf vẫn thuộc Event Center/Activities.
