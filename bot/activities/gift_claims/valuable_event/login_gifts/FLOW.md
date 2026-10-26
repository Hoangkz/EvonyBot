# Flow: Login Gifts

1. Mở Super Value Return và chọn Login Gifts.
2. Tìm toàn bộ hộp quà phát sáng bằng ảnh dùng chung
   `Common/button_reward_chest` chỉ trong vùng xanh cố định `(2,22,18,34)`,
   ngưỡng `0.78`. Hai bộ độc lập, tổng cộng 100 frame trên máy `21503`, cho
   điểm thật `0.8033..0.9455`; nhiễu ngoài vùng cao nhất `0.3881`. Crop đầy đủ
   62x66 bị animation làm điểm chỉ còn `0.1942..0.2141` nên không được dùng.
3. Nếu không thấy ảnh thì giữ PENDING; không bấm vị trí dự phòng hoặc bất kỳ
   tọa độ cố định nào.
4. Sau khi bấm, chờ `1.5s`, rồi chờ `Congratulations!` tối đa 6 lần, cách nhau
   1 giây. Nếu thấy thì đóng popup nhưng chưa được coi là DONE.
5. Chụp lại trang Login Gifts. Chỉ DONE sau hai frame liên tiếp vẫn đúng trang
   và không còn ảnh hộp quà trong vùng xanh. Congratulations xuất hiện nhưng
   rương vẫn còn thì giữ PENDING. Không dùng chấm đỏ và không quét các rương
   theo ngày ở bảng bên dưới.
