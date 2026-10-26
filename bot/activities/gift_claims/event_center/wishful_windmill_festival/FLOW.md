# Wishful Windmill Festival

1. Mở đúng hàng `Wishful Windmill Festival` trong Limited.
2. Vào `Wind Blessings` bằng icon thường, rương cũ `button_reward_chest`, hoặc
   rương có nhãn Wind mới `button_reward_chest_wind` (ngưỡng cao `0.86`).
   Không có bước dừng 2 giây chờ trang/rương ổn định: tìm và bấm
   ngay; sau mỗi thao tác chỉ chờ 1 giây.
3. Chỉ xác nhận đã mở panel khi thấy một trong hai ảnh title, gồm crop chữ mới
   `title_wind_blessings_text` từ `Screenshot_20261023-073761`.
4. Vừa mở Wind Blessings, chỉ tìm `Claim All` trong panel. Có nút thì bấm một
   lần và đóng Congratulations bằng điểm cố định `(195, 20)`; không có nút
   sau ba khung hình ổn định thì DONE 1. Pha này không tìm, bấm hoặc lướt các
   nút `Claim` riêng lẻ.
5. Sau khi DONE 1 mới đóng panel một lần, mở `Wind Power Storage`, rồi bấm
   `Challenge Quest`. Phải thấy lại title Wind Blessings trước khi nhận.
6. Phần Challenge Quest dùng cơ chế Claim riêng: ở nguyên panel, nhận/lướt vùng xanh
   đến khi không còn Claim. Đây là kiểm tra DONE 2.
7. Sau DONE 2 có hai nhánh:
   - Nếu không có Claim, hoặc có nhưng không bấm nhận được Claim nào: DONE ngay.
   - Nếu đã nhận được ít nhất một Claim và đã nhận hết: Back về Wind Power
     Storage, tìm rương cuối bằng ảnh median 40x40 trong vùng `(2,15,28,35)` ở
     ngưỡng `0.70`, rồi bấm rương. Thấy `Congratulations!` thì DONE; nếu không
     thấy popup, kiểm tra lại đúng vùng và rương đã biến mất thì cũng DONE.
8. Ảnh rương cuối đo từ 60 frame thật trên 21513: điểm thấp nhất/trung vị/cao
   nhất `0.7728/0.9442/0.9736`, nhiễu ngoài vùng cao nhất `0.2478`.
9. Nếu chạm giới hạn an toàn 12 lượt lướt, còn Claim chưa nhận hết, thiếu
    rương cuối, hoặc bấm xong không có Congratulations và rương vẫn còn thì
    giữ PENDING.
10. Chờ 1 giây sau thao tác/popup trước khi chụp và xác minh khung mới.
