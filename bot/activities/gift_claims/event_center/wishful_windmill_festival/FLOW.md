# Wishful Windmill Festival

1. Mở đúng hàng `Wishful Windmill Festival` trong Limited.
2. Vào `Wind Blessings` bằng icon thường, rương cũ `button_reward_chest`, hoặc
   rương có nhãn Wind mới `button_reward_chest_wind` (ngưỡng cao `0.86`).
   Không có bước dừng 2 giây chờ trang/rương ổn định: tìm và bấm
   ngay; sau mỗi thao tác chỉ chờ 1 giây.
3. Chỉ xác nhận đã mở panel khi thấy một trong hai ảnh title, gồm crop chữ mới
   `title_wind_blessings_text` từ `Screenshot_20261023-073761`.
4. Ở nguyên panel, chỉ tìm và bấm `Claim` có dải xanh trong vùng
   `(3, 26, 97, 88)`. `Claimed` phải đồng thời khớp ảnh trạng thái và dải xám;
   không để chữ `Claim` nằm trong `Claimed` trở thành nút bấm. Sau mỗi lần
   nhận, đóng Congratulations bằng điểm cố định tương ứng
   `(195, 20)` trên màn 396x704 rồi tiếp tục ngay trong panel; không Back và
   không mở lại rương giữa các Claim.
5. Khi khung hiện tại hết Claim, lướt chậm bên trong vùng xanh. Hai lần lướt
   liên tiếp không di chuyển và không còn **Claim xanh** mới hoàn tất lượt
   quét. Một khung chỉ có `Claimed` không được kết luận DONE mà vẫn phải lướt
   tới biên. Ngoài ra, ngay sau khi bấm một Claim ở pha này, nếu thấy
   `status_done_one_claim_limit` (Screenshot `073771`, dòng
   `Claim failed. The limit has been...`) thì kết luận DONE 1 ngay và chuyển
   sang kiểm tra DONE 2; không tiếp tục lướt hoặc bấm Claim của DONE 1.
6. Sau khi DONE 1 mới đóng panel một lần, mở `Wind Power Storage`, rồi bấm
   `Challenge Quest`. Phải thấy lại title Wind Blessings trước khi nhận.
7. Phần Challenge Quest chỉ có Claim ở trang đầu. Sau mỗi cú bấm, dùng
   `wait_for` trong đúng dòng vừa bấm để chờ trạng thái `Claimed`, tránh đọc
   nhầm khung hiệu ứng chuyển tiếp. Khi trang đầu đã chờ kiểm tra và không còn
   Claim xanh thì sang DONE 2, không lướt thêm vô ích.
8. Sau khi quét sạch Challenge Quest, **luôn** Back về Wind Power Storage, tìm
   rương cuối bằng ảnh median 40x40 chỉ trong khung xanh `(2,17,20,28)` ở
   ngưỡng `0.70`,
   rồi bấm rương. Nếu **không có rương** sau toàn bộ lượt tìm ở vùng này thì
   cũng ghi DONE 2. Nếu có rương, bot luôn tìm lại đúng ảnh và bấm tiếp cho
   tới khi rương biến mất khỏi đúng vùng. `Congratulations!` chỉ là dấu hiệu
   nhận quà; vẫn phải quét lại để xác nhận rương đã mất rồi mới ghi DONE 2.
9. Ảnh rương cuối đo từ 60 frame thật trên 21513: điểm thấp nhất/trung vị/cao
   nhất `0.7728/0.9442/0.9736`, nhiễu ngoài vùng cao nhất `0.2478`.
10. Không có giới hạn cứng số lượt lướt; biên dùng hai khung Hamming liên tiếp
    không di chuyển. Còn Claim chưa xác minh, hoặc bấm rương xong không có
    Congratulations và rương vẫn còn thì giữ PENDING.
11. Chờ 1 giây sau thao tác/popup trước khi chụp và xác minh khung mới.
