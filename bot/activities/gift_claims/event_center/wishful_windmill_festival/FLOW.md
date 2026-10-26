# Wishful Windmill Festival

1. Mở đúng hàng `Wishful Windmill Festival` trong Limited.
2. Mở rương Wind Blessings và chỉ xử lý các nút `Claim` trong khung xanh.
3. Nếu mọi nút trong khung đã là `status_claimed` thì phần đó DONE.
4. Sau khi bấm `Claim`, nếu đúng dòng đổi thành `status_claimed` thì phần đó DONE ngay.
5. Không nhầm chữ `Claim` nằm bên trong `Claimed`; hoàn tất phần rương trước rồi mới sang Challenge Quest.
2. Vào `Wind Blessings` bằng icon thường, rương cũ `button_reward_chest`, hoặc
   rương có nhãn Wind mới `button_reward_chest_wind` (ngưỡng cao `0.86`).
   Không có bước dừng 2 giây chờ trang/rương ổn định: tìm và bấm
   ngay; sau mỗi thao tác chỉ chờ 1 giây.
3. Chỉ xác nhận đã mở panel khi thấy một trong hai ảnh title, gồm crop chữ mới
   `title_wind_blessings_text` từ `Screenshot_20261023-073761`.
4. Ở nguyên panel, chỉ tìm và bấm `Claim` trong vùng xanh `(3, 26, 97, 88)`.
   Sau mỗi lần nhận, đóng Congratulations bằng điểm cố định tương ứng
   `(195, 20)` trên màn 396x704 rồi tiếp tục ngay trong panel; không Back và
   không mở lại rương giữa các Claim.
5. Khi khung hiện tại hết Claim, lướt chậm bên trong vùng xanh. Hai lần lướt
   liên tiếp không di chuyển và không còn Claim là DONE 1. Ngoài ra, ngay sau
   khi bấm một Claim ở pha này, nếu thấy
   `status_done_one_claim_limit` (Screenshot `073771`, dòng
   `Claim failed. The limit has been...`) thì kết luận DONE 1 ngay và chuyển
   sang kiểm tra DONE 2; không tiếp tục lướt hoặc bấm Claim của DONE 1.
6. Sau khi DONE 1 mới đóng panel một lần, mở `Wind Power Storage`, rồi bấm
   `Challenge Quest`. Phải thấy lại title Wind Blessings trước khi nhận.
7. Phần Challenge Quest dùng cùng cơ chế: ở nguyên panel, nhận/lướt vùng xanh
   đến khi không còn Claim. Đây là kiểm tra DONE 2.
8. Sau DONE 2 có hai nhánh:
   - Nếu không có Claim, hoặc có nhưng không bấm nhận được Claim nào: DONE ngay.
   - Nếu đã nhận được ít nhất một Claim và đã nhận hết: Back về Wind Power
     Storage, tìm rương cuối bằng ảnh median 40x40 trong vùng `(2,15,28,35)` ở
     ngưỡng `0.70`, rồi bấm rương. Thấy `Congratulations!` thì DONE; nếu không
     thấy popup, kiểm tra lại đúng vùng và rương đã biến mất thì cũng DONE.
9. Ảnh rương cuối đo từ 60 frame thật trên 21513: điểm thấp nhất/trung vị/cao
   nhất `0.7728/0.9442/0.9736`, nhiễu ngoài vùng cao nhất `0.2478`.
10. Nếu chạm giới hạn an toàn 12 lượt lướt, còn Claim chưa nhận hết, thiếu
    rương cuối, hoặc bấm xong không có Congratulations và rương vẫn còn thì
    giữ PENDING.
11. Chờ 1 giây sau thao tác/popup trước khi chụp và xác minh khung mới.
