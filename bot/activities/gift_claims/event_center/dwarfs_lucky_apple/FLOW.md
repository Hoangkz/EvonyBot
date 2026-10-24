# Dwarf's Lucky Apple

1. Mở Event Center và chọn Activities bằng ảnh chữ. Riêng danh sách này không
   dùng nhịp chờ chung 1,5–2 giây của Limited:
   - vuốt về đỉnh, mỗi cú vuốt chờ `0,8 giây`; hai cú liên tiếp không làm danh
     sách đổi mới xác nhận đã tới đỉnh;
   - từ đỉnh, chụp và tìm đúng `DwarfsLuckyApple/list_row`, rồi vuốt xuống từng
     bước; sau mỗi bước chờ `0,8 giây` mới chụp và tìm tiếp;
   - hai cú vuốt liên tiếp không đổi ảnh mới xác nhận đã tới đáy;
   - chưa thấy thì đảo chiều, tiếp tục quét từ đáy lên đỉnh với cùng nhịp
     `0,8 giây`;
   - chỉ bấm khi vừa tìm lại được đúng ảnh dòng Dwarf's Lucky Apple. Không còn
     bước đứng yên chờ thêm `1,5 giây` rồi quét trùng cùng một vị trí.
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
   Riêng layout thật sau khi vừa bấm đỏ x10 có thể làm ảnh DONE cũ chỉ đạt
   khoảng `0.507`: nếu chính lượt này đã nhận diện và bấm đỏ x10 ACTIVE, vị
   trí khớp yếu của x10 đã có dải xám (`S <= 65`, tỷ lệ màu `<= 20%`) và đồng
   thời nhận diện chính xác `status_red_wish_once` hoặc
   `status_red_wish_once_gray`, thì xác nhận đỏ x10 DONE. Điều kiện kết hợp
   này không được dùng trước khi bot đã bấm một nút đỏ x10 ACTIVE.
8. Nếu ảnh nút đang chuyển sáng làm nhận dạng mơ hồ, bot ở nguyên trong nhiệm
   vụ và chụp lại mỗi 1 giây; ba lần không đọc được không được chuyển PENDING
   hoặc Back ra danh sách. Chỉ bộ đếm 120 giây của worker mới được ngắt để quay
   lại Join Boss, rồi lần chạy sau tiếp tục nhiệm vụ chưa DONE.
   Ngay khi vào Dwarf, log ghi rõ deadline worker còn bao nhiêu giây.
   Nếu log báo không có deadline thì Join Boss không hoạt động hoặc
   worker đang chờ thể lực; Dwarf vẫn thuộc Event Center/Activities.
