# Wishful Windmill Festival

1. Mở đúng hàng `Wishful Windmill Festival` trong Limited.
2. Vào `Wind Blessings` bằng icon thường, rương cũ `button_reward_chest`, hoặc
   rương có nhãn Wind mới `button_reward_chest_wind` (ngưỡng cao `0.86`).
3. Chỉ xác nhận đã mở panel khi thấy một trong hai ảnh title, gồm crop chữ mới
   `title_wind_blessings_text` từ `Screenshot_20261023-073761`.
4. Ở nguyên panel, chỉ tìm và bấm `Claim` trong vùng xanh `(3, 26, 97, 88)`.
   Sau mỗi lần nhận, đóng Congratulations bằng điểm cố định tương ứng
   `(195, 20)` trên màn 396x704 rồi tiếp tục ngay trong panel; không Back và
   không mở lại rương giữa các Claim.
5. Khi khung hiện tại hết Claim, lướt chậm bên trong vùng xanh. Hai lần lướt
   liên tiếp không di chuyển và không còn Claim là DONE 1.
6. Sau khi DONE 1 mới đóng panel một lần, mở `Wind Power Storage`, rồi bấm
   `Challenge Quest`. Phải thấy lại title Wind Blessings trước khi nhận.
7. Phần Challenge Quest dùng cùng cơ chế: ở nguyên panel, nhận/lướt vùng xanh
   đến khi không còn Claim. Đây là DONE 2.
8. Chỉ ghi DB DONE khi cả DONE 1 và DONE 2 đều hoàn tất. Nếu chạm giới hạn an
   toàn 12 lượt lướt hoặc còn Claim chưa xác minh thì giữ PENDING.
9. Chờ 1 giây trước khi xác minh trạng thái sau popup và 2 giây sau thao tác
   chính để máy chạy đồng thời không đọc phải khung hình cũ.
