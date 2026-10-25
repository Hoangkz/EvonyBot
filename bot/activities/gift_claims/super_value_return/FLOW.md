# Flow: Super Value Return (hoạt động độc lập)

1. Mở Super Value Return (`zone.open_super_value_return`): ở màn thành chính có nút ••• (đang ở bản đồ thế giới thì vào thành
   trước), tìm nút vào bằng `launcher.find_super_value_return`, xét theo thứ tự ưu tiên:
   - TH1: icon Login Gifts góc trên bên phải (`login_gifts_top`, vùng x 70-100% y 10-50%).
   - TH2: một icon trong `Images/GiftClaims/SuperValueReturn/launcher_icons/` ở vùng x 0-50% y 70-88%. Ảnh mẫu chỉ là vùng
     nhỏ trong icon, không có chữ, không chạm chấm đỏ. Nhiều chỗ khớp thì lấy chỗ có x bé nhất.
   - TH3: mũi tên đi lên (`arrow_up`, vùng x 0-30% y 70-88%): nút vào nằm ngay dưới, thấp hơn tâm mũi tên 40 px.
   - TH4: mũi tên đi xuống (`arrow_down`, vùng x 0-30% y 55-80%): bấm vào, nghỉ 1s cho thành mũi tên đi lên, rồi xét TH3.
   - TH5: lấy y của icon Valuable Event (`find_valuable_event`, cao hơn chữ "Event" 30 px), x = 40.
   Bấm rồi chờ tiêu đề Super Value Return, cứ 1s xem lại, tối đa 8 lần; chưa vào thì về màn chính làm lại, tối đa 3 lần.
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
