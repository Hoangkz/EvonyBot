# Flow: Super Value Return (hoạt động độc lập)

1. Mở Super Value Return bằng `find_super_value_return`: thử ảnh vàng
   `Screenshot_20261025-192710` và các ảnh First Purchase, Empire Depot, Lucky
   Raffle, Login Gifts. First Purchase dùng ảnh trung vị toàn nút tạo từ 50/50
   frame hợp lệ chụp trên máy 21503. Login Gifts dùng ảnh trung vị toàn launcher
   tạo từ 50/50 frame mới trên máy 21513: điểm thật thấp nhất `0.9631`, nhiễu
   cao nhất `0.1544`. Không lưu từng pha animation. Dãy ngưỡng là
   `0.95, 0.90, 0.85`; lúc chạy bot chụp lại tối đa 4 frame. Ảnh Login Gifts
   được quy đổi lên phần icon; ảnh toàn nút và ảnh vàng bấm đúng tâm.
   Không còn fallback tọa độ `(30, 560)` hoặc bất kỳ tọa độ launcher cứng nào.
2. Chạy lần lượt Login Gifts, Empire Depot, Lucky Raffle, City Growth Plan
   Stage 1 và Refining Weekly Card; mỗi task dùng DB key riêng.
3. City Growth Plan Stage 1 chỉ DONE khi trong khung thưởng đã cuộn tới ảnh
   chứa đồng thời hàng số 15 và dấu tích xanh đã nhận. Ảnh tham chiếu thuộc tab
   này; Refining Weekly Card thật dùng các mốc Daily Activity 20/50/80.
4. Mỗi vị trí carousel chỉ chọn **một** tab. Sau khi bấm Login Gifts hoặc một
   tab khác, bot phải chờ toàn bộ thao tác nhận quà ở vùng dưới trả về DONE hay
   PENDING, ghi trạng thái và nghỉ 1 giây; chỉ sau đó mới được lướt carousel
   phía trên để tìm tab tiếp theo. Không tái sử dụng tọa độ tab lấy từ ảnh cũ.
   Login Gifts luôn được mở để chạy flow riêng, không dùng trạng thái chấm đỏ
   làm điều kiện DONE.
5. Trong Login Gifts, tìm ảnh `button_reward_chest`; không thấy thì tap dự
   phòng `(45, 190)`. `Congratulations!` hoặc ảnh chụp mới không còn hộp quà
   đều xác nhận DONE.
6. Với các tab còn lại, chạy flow riêng của Empire Depot, Lucky Raffle, City
   Growth Plan hoặc Refining Weekly Card.
7. Đưa carousel về biên đầu, rồi đảo chiều quét tới biên cuối. Mỗi biên chỉ
   được xác nhận sau **hai cú lướt liên tiếp** mà dấu vân tay vùng chữ tên task
   không đổi; hình động phía trên tên bị loại khỏi vùng so sánh. Không có giới
   hạn số cú lướt cục bộ; Stop/timeout chung của bot vẫn có thể ngắt an toàn.
   Task đã thấy nhưng chưa đạt điều kiện DONE được giữ PENDING; chỉ task không
   xuất hiện sau lượt đã xác nhận đủ hai biên mới được cộng một lần không thấy,
   đủ 3 lần mới DONE.
8. Quay về màn thành.

Badge của tab khác không được dùng để kết luận tab hiện tại chưa xong.
