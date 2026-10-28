# Great Expedition

1. Vào tab **Great Expedition**, bật `Skip animation` khi chưa bật, rồi bấm
   `Roll Once Free` nếu còn.
2. Ở nhánh xúc xắc, bot luôn ưu tiên x5. Sau mỗi lần bấm x5, chờ 5 giây và
   chỉ bấm tiếp khi nhãn `Auto-Rolling` ở nút x5 đã biến mất. Khi giá x5 đỏ,
   bot chuyển sang x1 và chờ 2 giây sau mỗi lần bấm.
3. Rương map chỉ là launcher cho panel `Quests`: bot chỉ mở nó nếu thấy chấm
   đỏ trong vùng gắn với rương. Trong panel, bot nhận mọi `Claim` xanh rồi
   Back về map; rương map không phải điều kiện DONE.
4. Khi x5/x1 đã đỏ, bot mở **Expedition Trial**, vào `Challenge Quest`, quét
   hết `Claim` xanh trong khung, xử lý popup nâng cấp nếu xuất hiện, và đóng
   modal bằng nút X đỏ (không dùng Android Back). Một Claim vẫn xanh được tìm
   lại/bấm tối đa ba lần; chỉ `Claimed` xám hoặc popup nhận quà hợp lệ mới xác
   minh là đã nhận.
5. Cuối cùng bot kiểm tra rương vàng ở Expedition Trial. Không có rương, hoặc
   rương biến mất sau khi bấm/nhận, mới là `DONE`. Rương còn hiện sẽ được bấm
   lại đến khi biến mất; chỉ trạng thái Claim chưa đổi sau đủ ba lần xác minh
   mới giữ `PENDING`.
