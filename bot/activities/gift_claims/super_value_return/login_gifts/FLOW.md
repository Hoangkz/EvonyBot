# Flow: Login Gifts

1. Mở Super Value Return và chọn Login Gifts.
2. Tìm toàn bộ hộp quà phát sáng bằng ảnh dùng chung
   `Common/button_reward_chest`, ngưỡng `0.80`. Ảnh 47x47 được chọn từ 20
   khung chụp trên máy `21513`; điểm khớp thấp nhất đo được là `0.8305`.
3. Không thấy nút quà: coi như đã nhận, DONE, không bấm gì (VD màn danh sách ngày
   `tests/gift_claims/screens/super_value_return_login_gifts_no_button.png`).
4. Thấy nút thì bấm, chụp lại màn hình tối đa 3 lần, cách nhau 1 giây. Có
   `Congratulations!` thì đóng popup và DONE; nếu trang Login Gifts vẫn mở
   nhưng không còn ảnh hộp quà thì cũng DONE.
5. Chỉ giữ PENDING khi chưa xác nhận được trang Login Gifts, hoặc đã bấm mà không
   có Congratulations và hộp quà vẫn còn. Không dùng chấm đỏ và không quét các
   rương theo ngày ở bảng bên dưới.
