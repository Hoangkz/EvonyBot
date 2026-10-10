# Flow nhận quà chuẩn

## Phạm vi

Task `gift_claims` chỉ chạy sau Daily Activities và có ưu tiên thấp nhất. Toàn bộ
quà dùng một task chung. DB chỉ lưu `gift_claims` sau khi cả khu 1 và khu 2 đã
được kiểm tra xong; tiến độ giữa các lát 120 giây chỉ lưu trong RAM.

## Trình tự chung

1. Về màn thành phố.
2. Quét khu 1 ở thanh dưới, sau đó quét khu 2 ở thanh bên phải.
3. Loại mọi thành phần đỏ nằm trên biểu tượng Facebook hoặc Follow Us.
   Các mảng đỏ sát nhau trên cùng một icon phải được gộp thành một badge thật;
   không được mở lại artwork của cùng icon như một mục Unknown.
4. Bấm một dấu đỏ chưa xét và nhận diện màn vừa mở bằng tiêu đề cố định.
5. Nếu là màn cha có carousel hoặc danh sách, duyệt toàn bộ dấu đỏ trong màn cha.
6. Trong mỗi màn con, xử lý theo thứ tự:
   - bấm nút điều hướng cố định như Sprint Package, Stockpile hoặc Scores;
   - tìm các nút nhận thật: Claim, Free, Claim Free, Claimable, Daily Free,
     Claim All;
   - nếu không có nút cố định, dò một điểm lấp lánh trong vùng nội dung an toàn;
   - không bấm vùng mua hàng, thanh tài nguyên hoặc phần thưởng trả phí.
7. Xác minh từng lần nhận bằng một trong các điều kiện:
   - xuất hiện Congratulations;
   - nút nhận vừa bấm biến mất;
   - trạng thái Claimed xuất hiện tại đúng phần thưởng.
8. Việc chỉ bấm nút điều hướng không được tính là đã nhận quà.
9. Quay lại header hoặc danh sách và quét lại. Màn cha chỉ DONE khi không còn
   dấu đỏ, ngoại trừ Facebook hoặc màn được quy định bỏ qua.
   Trên carousel, mỗi dấu đỏ chỉ thuộc tab có tâm gần nó nhất; dấu của tab bên
   cạnh không được dùng để kết luận tab vừa xử lý vẫn còn đỏ.
10. Hết 120 giây thì dừng tại điểm kiểm tra gần nhất, nhường Boss và tiếp tục
    các mục chưa xét ở lát sau.
11. Nếu một màn từng còn đỏ nhưng không xuất hiện trong lần quét lại đầy đủ cả
    hai vùng, coi dấu đỏ đó đã được xóa; không để trạng thái cũ chặn task DB.

## Quy tắc từng nhóm

- Valuable Event: tách rõ tab phụ và nút nhận. Sprint Package, Stockpile và
  Scores là điều hướng; Daily Free, Free và Redeem mới là nút nhận. Redeem chỉ
  được tính sau khi bấm xác nhận và thấy Congratulations.
- Super Value Return: luôn kiểm tra Login Gifts một lần; Empire Depot và Lucky
  Raffle dùng Claimable; City Growth Plan ưu tiên Claim All rồi chỉ nhận cột
  miễn phí bên trái.
- Login Gifts: ưu tiên rương phát sáng, sau đó kiểm tra từng hàng cột miễn phí;
  chỉ tính khi có Congratulations.
- Back to Territory: với mỗi tab đỏ trên carousel, duyệt tiếp toàn bộ badge đỏ
  ở hàng Day và Daily Login/Stamina/Daily Activity bên dưới; quét dọc danh sách
  để nhận tất cả nút Claim trùng nhau. Chỉ sau đó mới dò sparkle; một sparkle
  không sinh Congratulations thì dừng tab đó. Nếu lát 120 giây ngắt giữa tab,
  tab đó chưa được ghi nhớ và phải được mở lại ở lát sau.
- Event Center: chỉ quét danh sách Limited; bỏ Bacchus Tavern, Activities và
  mọi mục Facebook. Sau mỗi event phải quay lại danh sách trước khi cuộn tiếp.

## Hợp đồng kết quả

- `attempted`: số nút nhận đã bấm.
- `verified`: số quà đã xác minh nhận thành công.
- `claimed`: chỉ đúng khi `verified > 0`.
- `cleared`: dấu đỏ của mục đã biến mất sau xử lý.
- `remaining`: vẫn còn dấu đỏ và chưa có quà được xác minh.
- `claimed_remaining`: đã nhận được quà nhưng mục vẫn còn dấu đỏ cần kiểm tra.

Không được suy ra `claimed` chỉ từ việc màn hình thay đổi hoặc từ số lần bấm.
