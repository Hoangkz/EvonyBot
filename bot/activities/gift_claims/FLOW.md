# Flow nhận quà chuẩn

## Phạm vi

Task `gift_claims` chỉ chạy sau Daily Activities và có ưu tiên thấp nhất. Toàn bộ
quà dùng một task chung. DB chỉ lưu `gift_claims` sau khi cả khu 1 và khu 2 đã
được kiểm tra xong; tiến độ giữa các lát 120 giây chỉ lưu trong RAM.

## Cấu trúc và điểm chạy hiện tại

```
gift_claims/
├── valuable_event/              # Khu ngoài thành, không đi qua Event Center
│   ├── run.py                   # quét carousel Valuable Event
│   ├── super_value_return/run.py
│   ├── login_gifts/run.py
│   └── <từng event>/run.py
└── event_center/                # Chỉ các event mở từ Event Center
    ├── run.py                   # quét Limited / Activities / Competition
    ├── grace_of_star_trail/run.py
    ├── dwarfs_treasure/run.py
    └── <từng event>/run.py
```

Mỗi event có entry `run(bot)` trong thư mục của chính nó. Chưa có event con nào
được worker đăng ký thành job/priority riêng. Hiện worker chỉ gọi
`daily_activities.common._run_gifts()`; sau khi Daily Activities và phần
Activity Rewards hoàn thành, hàm này gọi một lần `gift_claims.run(ctx)`. Entry
chung đó quét cả hai khu. Cách chọn/gọi riêng từng `run(bot)` sẽ được thêm sau
khi có quy tắc điều phối.

## Trình tự chung

1. Về màn thành phố.
2. Quét khu 1 ở thanh dưới, sau đó quét khu 2 ở thanh bên phải.
3. Loại mọi thành phần đỏ nằm trên biểu tượng Facebook hoặc Follow Us.
   Các mảng đỏ sát nhau trên cùng một icon phải được gộp thành một badge thật;
   không được mở lại artwork của cùng icon như một mục Unknown.
4. Bấm một dấu đỏ chưa xét và nhận diện màn vừa mở bằng tiêu đề cố định.
5. Nếu là màn cha có carousel hoặc danh sách, duyệt toàn bộ dấu đỏ trong màn cha.
6. Trong mỗi màn con, xử lý theo thứ tự:
   - bấm nút điều hướng/phần thưởng cố định như Rewards, Star Trail Gift,
     Sprint Package, Stockpile hoặc Scores;
   - tìm các nút nhận thật: Claim, Free, Claim Free, Claimable, Daily Free,
     Claim All;
   - nếu thấy nút X của popup/mục không nhận được thì dùng Back để thoát, không
     bấm trực tiếp vào X;
   - dò điểm lấp lánh trong vùng nội dung an toàn tối đa 4 lần, kể cả khi một
     frame không thấy sáng; sau 4 lần không có quà xác minh thì kết thúc mục;
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
   Mục đã được mở, kiểm tra nút cố định và sparkle đủ 4 lần được coi là đã xét;
   badge trang trí hoặc badge không tự tắt không được làm luồng lặp vô hạn.
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
- Login Gifts: chỉ bấm rương vàng/phát sáng được nhận diện trong cột miễn phí;
  không dò mù các hàng. Chỉ tính khi có Congratulations.
- Back to Territory: với mỗi tab đỏ trên carousel, duyệt tiếp toàn bộ badge đỏ
  ở hàng Day và Daily Login/Stamina/Daily Activity bên dưới; quét dọc danh sách
  để nhận tất cả nút Claim trùng nhau. Chỉ sau đó mới dò sparkle; một sparkle
  không sinh Congratulations thì dừng tab đó. Nếu lát 120 giây ngắt giữa tab,
  tab đó chưa được ghi nhớ và phải được mở lại ở lát sau.
- Event Center: ưu tiên quét đủ ba nhóm theo thứ tự Limited, Activities rồi
  Competition. Precious Blazon Exchange và Hypnos' Dream chỉ mở Rewards khi
  thấy đúng phần chữ Rewards; Dwarf's Treasure tương tự với chữ Daily Free.
  Mỗi nút đặc biệt được tìm tối đa bốn lần rồi bỏ qua. Trong Activities, nếu
  thấy hàng Facebook kèm dấu đỏ thì không mở Facebook và coi nhóm đã DONE.
  Competition kiểm tra các nút nhận cố định trước, sau đó thử tối đa bốn điểm
  sparkle; sparkle chỉ thành công khi xuất hiện Congratulations. Bacchus Tavern
  vẫn được nhận diện và bỏ qua. Sau mỗi event phải quay lại danh sách trước khi
  cuộn tiếp. Sau một vòng quét đầy đủ, badge mua hàng/khóa vẫn đỏ nhưng event đã
  có checkpoint và đã thử đủ bốn lần được ghi `skip/done`; badge mới chưa từng
  xử lý vẫn chặn DONE.
- Revelation of Horus và Sealed Imperial Treasury được nhận diện theo tiêu đề,
  bỏ qua ngay và coi là DONE. Activities tạm thời bỏ qua toàn bộ theo cấu hình.
- Grace of Star Trail bấm icon `Star Trail Gift`, chờ màn con rồi bấm tiếp icon
  đồng xu có chữ `Claim`; chỉ bước thứ hai mới tính là nhận xu. Dwarf's Treasure
  dùng crop gồm cả rương `Daily Free` để tâm ảnh nằm trong vùng bấm thật.
- Limited chủ động tìm dòng Grace of Star Trail một lần ngay cả khi dòng ngoài
  không có badge đỏ. Việc cuộn danh sách dừng sớm khi ảnh ổn định ở biên; các
  nhóm đã DONE được checkpoint để lát 120 giây sau không quét lại.
- Màn xoay vòng chưa có tiêu đề cố định: vẫn tìm toàn bộ nút chữ nhận trong
  vùng nội dung, sau đó kiểm tra sparkle đủ bốn lần. Nếu không có kết quả nhận
  thì coi là badge mua hàng và bỏ qua, không để chặn task chung.

## Hợp đồng kết quả

- `attempted`: số nút nhận đã bấm.
- `verified`: số quà đã xác minh nhận thành công.
- `claimed`: chỉ đúng khi `verified > 0`.
- `cleared`: dấu đỏ của mục đã biến mất sau xử lý.
- `remaining`: vẫn còn dấu đỏ và chưa có quà được xác minh.
- `claimed_remaining`: đã nhận được quà nhưng mục vẫn còn dấu đỏ cần kiểm tra.

Không được suy ra `claimed` chỉ từ việc màn hình thay đổi hoặc từ số lần bấm.
