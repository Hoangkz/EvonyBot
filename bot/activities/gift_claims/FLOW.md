# Flow nhận quà chuẩn

## Phạm vi

Task `gift_claims` được đăng ký ở cuối nhóm Daily Activities, sau
`daily_rewards`, với priority 299. Khi có Join Boss, mỗi lượt chạy tối đa 120
giây; hết thời gian hoặc có boss mới thì nhường Join Boss rồi gọi lại từ các
key DB còn PENDING. Mỗi điểm nhận có một key DB riêng (ví dụ `gift_limited_offer`), còn `gift_claims`
chỉ là key tổng để scheduler biết cả hai khu đã xong. Registry tại
`gift_claims/registry.py` là danh sách bắt buộc phải kiểm tra; chấm đỏ không
được dùng để kết luận một task đã xong.

Mỗi key được DB lưu timestamp ISO, ví dụ `gift_limited_offer:
2026-10-14T21:05:00`. `BotWorker.is_daily_done()` so timestamp với lần reset
server gần nhất (mặc định 14:00, lấy từ DB settings). Vì vậy lúc 15:00 ngày
15/10, bản ghi 21:05 ngày 14/10 là **chưa làm**; lúc 13:59 thì vẫn **đã làm**.
DB không xoá key khi sang ngày mới.

## Cấu trúc và điểm chạy hiện tại

```
gift_claims/
├── valuable_event/              # Khu ngoài thành, không đi qua Event Center
│   ├── run.py                   # quét carousel Valuable Event
│   ├── super_value_return/run.py
│   ├── login_gifts/run.py
│   └── <từng event>/run.py
└── event_center/                # Chỉ các event mở từ Event Center
    ├── run.py                   # chỉ quét danh sách Limited
    ├── grace_of_star_trail/run.py
    ├── dwarfs_treasure/run.py
    └── <từng event>/run.py
```

Mỗi event có entry `run(bot)` trong thư mục của chính nó. Entry tổng
`gift_claims.run_job(ctx, settings)` là job scheduler; key tổng trong DB là
điều kiện để worker bỏ qua toàn bộ hoạt động trong phần còn lại của ngày server.

## Trình tự chung

1. Đọc registry và bỏ qua duy nhất những key đã DONE trong ngày server hiện
   tại. Key chưa DONE luôn phải đi tới đúng màn và kiểm tra, kể cả khi không
   còn chấm đỏ.
2. Về màn thành phố; kiểm tra Vùng 1 trước, sau đó Vùng 2:
   - Vùng 1 là toàn bộ điểm nhận quà không nằm trong Event Center, gồm
     Valuable Event và Super Value Return (Empire Depot, Lucky Raffle,
     City Growth Plan, Login Gifts).
   - Vùng 2 là Event Center và toàn bộ event con được mở từ đó.
3. Mở Valuable Event bằng vị trí launcher cố định ở thanh dưới và Event Center
   bằng template launcher cố định ở thanh phải; không chạm vào chấm đỏ.
   Facebook/Follow Us luôn bị loại.
   Các mảng đỏ sát nhau trên cùng một icon phải được gộp thành một badge thật;
   không được mở lại artwork của cùng icon như một mục Unknown.
4. Dò label cố định từ đầu tới cuối. Label nào còn PENDING trong DB thì mở và
   chạy flow của event đó, kể cả không có dấu đỏ. Dấu đỏ chỉ là tín hiệu phụ
   cho event chưa có label cố định.
5. Nếu là màn cha có carousel hoặc danh sách, duyệt toàn bộ dấu đỏ trong màn cha.
6. Trong mỗi màn con, xử lý theo thứ tự:
   - bấm nút điều hướng/phần thưởng cố định như Rewards, Star Trail Gift,
     Sprint Package, Stockpile hoặc Scores;
   - tìm các nút nhận thật: Claim, Free, Claim Free, Claimable, Daily Free,
     Claim All;
   - nếu thấy nút X của popup/mục không nhận được thì dùng Back để thoát, không
     bấm trực tiếp vào X;
   - dò điểm lấp lánh trong vùng nội dung an toàn; Valuable Event cần 3 vòng
     liên tiếp không nhận thêm quà, Event Center lấy 3 mẫu cho mỗi lượt kiểm;
   - không bấm vùng mua hàng, thanh tài nguyên hoặc phần thưởng trả phí.
7. Xác minh từng lần nhận bằng một trong các điều kiện:
   - xuất hiện Congratulations;
   - nút nhận vừa bấm biến mất;
   - trạng thái Claimed xuất hiện tại đúng phần thưởng.
8. Việc chỉ bấm nút điều hướng không được tính là đã nhận quà.
9. Quay lại header hoặc danh sách và xác minh flow của đúng event đã hoàn tất.
   Chỉ lúc đó key riêng của event mới được ghi timestamp. Màn cha/aggregate
   chỉ DONE khi tất cả key trong registry của cả hai khu đều current.
   Trên carousel, mỗi dấu đỏ chỉ thuộc tab có tâm gần nó nhất; dấu của tab bên
   cạnh không được dùng để kết luận tab vừa xử lý vẫn còn đỏ.
   Mục đã được mở, vét nút cố định và đủ số vòng kiểm tra sparkle được coi là đã xét;
   badge trang trí hoặc badge không tự tắt không được làm luồng lặp vô hạn.
10. Gift Claims giữ nguyên deadline và cờ ngắt Join Boss của worker. Hết 120
    giây hoặc có boss mới thì không ghi DONE cho bước đang dở; sau Join Boss,
    hàm chạy lại và chỉ lấy các key chưa DONE trong DB.
11. Sau một lượt dò đầy đủ cả hai vùng mà vẫn còn label không xuất hiện, lưu
    lần lượt `gift_claims_scan_1`, `gift_claims_scan_2`,
    `gift_claims_scan_3`. Chỉ khi đủ ba lượt trong cùng ngày server mới ghi
    DONE cho các event còn thiếu và ghi key tổng `gift_claims`. Không thấy
    launcher/màn cha sau một lần tìm đầy đủ được tính là lượt rỗng; bị ngắt
    giữa lượt bởi 120 giây/Join Boss thì không tăng số lượt quét.

## Quy tắc từng nhóm

- Valuable Event: tách rõ tab phụ và nút nhận. Sprint Package, Stockpile và
  Scores là điều hướng; Daily Free, Free và Redeem mới là nút nhận. Redeem chỉ
  được tính sau khi bấm xác nhận và thấy Congratulations.
- Resource Consumption Sprint có tab riêng và dùng crop toàn nút Free, không
  dùng nhầm tên Refining Stone Sprint. Ancient Dynasty Treasury có tab riêng
  và mở đúng nút Daily Free bên phải trước khi xét nội dung.
- Trong mỗi tab Valuable Event, bot vét toàn bộ Claim/Daily Free/Free đã biết
  trước, sau đó mới thử một điểm lấp lánh và quay lại vét nút chữ. Sau 3 vòng
  liên tiếp không xác minh thêm được quà, phần lấp lánh còn lại được coi là
  nội dung trả phí/trang trí. Sau đó bot quét lại toàn bộ carousel phía trên;
  nếu badge vẫn còn thì chạy lại mục ở vòng tổng thứ hai. Badge vẫn tồn tại
  sau vòng tổng thứ hai được coi là trả phí/trang trí và key được DONE hôm nay.
- Super Value Return: luôn kiểm tra Login Gifts một lần; Empire Depot và Lucky
  Raffle dùng Claimable; City Growth Plan ưu tiên Claim All rồi chỉ nhận cột
  miễn phí bên trái.
- Login Gifts: chỉ bấm rương vàng/phát sáng được nhận diện trong cột miễn phí;
  không dò mù các hàng. Chỉ tính khi có Congratulations.
- Back to Territory: với mỗi tab đỏ trên carousel, duyệt tiếp toàn bộ badge đỏ
  ở hàng Day và Daily Login/Stamina/Daily Activity bên dưới; quét dọc danh sách
  để nhận tất cả nút Claim trùng nhau. Chỉ sau đó mới dò sparkle; một sparkle
  không sinh Congratulations thì dừng tab đó. Nếu người dùng bấm Stop giữa
  tab, tab đó chưa được ghi nhớ và phải được mở lại ở lần chạy sau.
- Event Center: chỉ quét nhóm Limited; không vào Activities hoặc Competition.
  Precious Blazon Exchange và Hypnos' Dream chỉ mở Rewards khi
  thấy đúng phần chữ Rewards; Dwarf's Treasure tương tự với chữ Daily Free.
  Poseidon's Day phải nhận diện đúng tiêu đề, bấm tab Ocean Offering có dấu đỏ,
  rồi bấm đúng rương Daily Free. Các event có nút riêng này kết thúc ngay sau
  khi kiểm tra nút, không chạy fallback sparkle để tránh mở nhầm màn trả phí.
  Mỗi event được kiểm tra nội dung tối đa hai lượt nếu chưa có Congratulations,
  nút biến mất hoặc trạng thái nhận thành công. Sau hai lượt không nhận thêm
  được gì, event được coi là đã cạn quà và DONE hôm nay. Mỗi lượt vẫn cho phép
  nút đặc biệt xuất hiện trễ trong số lần dò hữu hạn. Bacchus Tavern vẫn được
  nhận diện và bỏ qua. Sau mỗi event phải quay lại danh sách trước khi
  cuộn tiếp. Sau một vòng quét đầy đủ, badge mua hàng/khóa vẫn đỏ nhưng event đã
  có checkpoint và đã thử đủ bốn lần được ghi `skip/done`; badge mới chưa từng
  xử lý vẫn chặn DONE.
- Revelation of Horus và Sealed Imperial Treasury được nhận diện theo tiêu đề,
  bỏ qua ngay và coi là DONE.
- Grace of Star Trail bấm icon `Star Trail Gift`, chờ màn con rồi bấm tiếp icon
  đồng xu có chữ `Claim`; chỉ bước thứ hai mới tính là nhận xu. Dwarf's Treasure
  dùng crop gồm cả rương `Daily Free` để tâm ảnh nằm trong vùng bấm thật.
- Limited chủ động tìm dòng Grace of Star Trail một lần ngay cả khi dòng ngoài
  không có badge đỏ. Việc cuộn danh sách dừng sớm khi ảnh ổn định ở biên; các
  nhóm đã DONE được checkpoint để lần chạy sau không quét lại.
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
