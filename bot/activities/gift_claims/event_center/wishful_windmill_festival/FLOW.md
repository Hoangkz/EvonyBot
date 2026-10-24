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
   đến khi không còn Claim. Đây là DONE 2.
8. Chỉ ghi DB DONE khi cả DONE 1 và DONE 2 đều hoàn tất. Nếu chạm giới hạn an
   toàn 12 lượt lướt hoặc còn Claim chưa xác minh thì giữ PENDING.
9. Chờ 1 giây sau thao tác/popup trước khi chụp và xác minh khung mới.
