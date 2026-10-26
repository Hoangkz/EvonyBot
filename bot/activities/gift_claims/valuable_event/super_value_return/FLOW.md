# Flow: Super Value Return (hoạt động độc lập)

1. Mở Super Value Return bằng `find_super_value_return`: thử ảnh vàng
   `Screenshot_20261025-192710` và các ảnh First Purchase, Empire Depot, Lucky
   Raffle, Login Gifts. First Purchase dùng ảnh trung vị toàn nút tạo từ 50/50
   frame hợp lệ chụp trên máy 21503. Login Gifts dùng ảnh trung vị toàn launcher
   tạo từ 50/50 frame mới trên máy 21513: điểm thật thấp nhất `0.9631`, nhiễu
   cao nhất `0.1544`. Không lưu từng pha animation. Dãy ngưỡng chung là
   `0.95, 0.90, 0.85`; Empire Depot có fallback ảnh riêng `0.62` đo từ 50
   frame máy 21513 (điểm thật thấp nhất `0.6505`, nhiễu cao nhất `0.5443`).
   Ảnh Login Gifts
   được quy đổi lên phần icon; ảnh toàn nút và ảnh vàng bấm đúng tâm.
   Không còn fallback tọa độ `(30, 560)` hoặc bất kỳ tọa độ launcher cứng nào.
   Không mở hoặc chuyển qua Valuable Event khi không thấy launcher; theo dõi
   tối đa 50 frame animation rồi giữ PENDING.
2. Thấy tab nhiệm vụ nào trước trên màn hình thì xử lý tab đó, không ưu tiên
   theo danh sách cấu hình. Login Gifts, Empire Depot, Hall of Historic
   Generals, Soul of Spiritual Beast, Lucky Raffle, City Growth Plan Stage 1
   và Refining Weekly Card dùng DB key riêng.
3. City Growth Plan Stage 1 chỉ DONE khi trong khung thưởng đã cuộn tới ảnh
   chứa đồng thời hàng số 15 và dấu tích xanh đã nhận. Ảnh tham chiếu thuộc tab
   này; Refining Weekly Card thật dùng các mốc Daily Activity 20/50/80.
4. Mỗi vị trí carousel chỉ chọn **một** tab. Sau khi bấm Login Gifts hoặc một
   tab khác, bot phải chờ toàn bộ thao tác nhận quà ở vùng dưới trả về DONE hay
   PENDING, ghi trạng thái và nghỉ 1 giây; chỉ sau đó mới được lướt carousel
   phía trên để tìm tab tiếp theo. Không tái sử dụng tọa độ tab lấy từ ảnh cũ.
   Login Gifts luôn được mở để chạy flow riêng, không dùng trạng thái chấm đỏ
   làm điều kiện DONE.
5. Trong Login Gifts, chỉ bấm khi tìm thấy ảnh `button_reward_chest`; không thấy
   thì giữ PENDING và không bấm tọa độ dự phòng. Sau khi bấm phải chờ popup,
   đóng Congratulations nếu có, rồi quét lại. Chỉ hai frame liên tiếp không
   còn hộp quà mới xác nhận DONE.
6. Với các tab còn lại, chạy flow riêng của Empire Depot, Lucky Raffle, City
   Growth Plan hoặc Refining Weekly Card.
7. Hall of Historic Generals: chọn tab tên, xác nhận `Challenge Quest`, mở
   `How to Earn Scores`, rồi quét dọc vùng xanh. `Claim` cần cả chữ và dải xanh;
   `Claimed` cần cả chữ đầy đủ và dải xám. Sau khi nhận quà phải quét lại toàn
   bộ từ đầu tới cuối; chỉ lượt xác minh không còn Claim mới trả `DONE_1` và
   nhường nhiệm vụ khác. Chỉ toàn bộ Claimed mới ghi DONE.
8. Soul of Spiritual Beast: xác nhận màn chính bằng Challenge Quest, nhận lặp
   rương dùng chung với Login Gifts trong vùng riêng, rồi quét Daily Tasks và
   Seasonal trong popup Quests. Claim cần chữ + dải xanh, Claimed cần chữ +
   dải xám. Có nhận Claim thì kết thúc cửa sổ bằng DONE_1 sau khi quay lại nhận
   hết rương; chỉ hai tab toàn bộ Claimed mới ghi DONE.
9. Đưa carousel về biên đầu, rồi đảo chiều quét tới biên cuối. Mỗi biên chỉ
   được xác nhận sau **hai cú lướt liên tiếp** mà dấu vân tay vùng chữ tên task
   không đổi; hình động phía trên tên bị loại khỏi vùng so sánh. Không có giới
   hạn số cú lướt cục bộ; chiều quét dùng cú dài `90% -> 10%` vì cú ngắn cũ
   không làm carousel dịch chuyển trên máy 21513. Stop/timeout chung của bot
   vẫn có thể ngắt an toàn.
   Task đã thấy nhưng chưa đạt điều kiện DONE được giữ PENDING; chỉ task không
   xuất hiện sau lượt đã xác nhận đủ hai biên mới được cộng một lần không thấy,
   đủ 3 lần mới DONE.
10. Quay về màn thành.

Badge của tab khác không được dùng để kết luận tab hiện tại chưa xong.
