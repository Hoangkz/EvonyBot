# Flow: Super Value Return (hoạt động độc lập)

1. Mở Super Value Return khi có badge đỏ ở vùng ngoài thành.
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
7. Quét lại carousel theo hai hướng. Task đã thấy nhưng chưa đạt điều kiện DONE
   được giữ PENDING và bot tiếp tục tab kế tiếp; chỉ task không xuất hiện trong
   một lượt quét đầy đủ mới được cộng một lần không thấy, đủ 3 lần mới DONE.
8. Quay về màn thành.

Badge của tab khác không được dùng để kết luận tab hiện tại chưa xong.
