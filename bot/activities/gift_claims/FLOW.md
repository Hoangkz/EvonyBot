# Flow nhận quà chuẩn

## Phạm vi

Gift Claims gồm **ba khu độc lập và nhiệm vụ Revelry Carnival**.
Worker chạy nhóm quà sau khi hoàn thành các Daily Activities và ưu tiên theo
thứ tự **Event Center -> Revelry Carnival -> Valuable Event -> Super Value Return** khi ô **Claim Event Gifts** ở tab Daily
Activities được tích (`settings["General"]["gift_claims"]`, mặc định bật):

Sau một cửa sổ Event Center đã chạy và còn PENDING, Event Center nghỉ tới mốc
120 giây tiếp theo; trong quãng chờ đó Revelry Carnival được mở khóa để làm
tiếp. Khi hết mốc chờ, Event Center lại được xét trước theo thứ tự ưu tiên.

Khu nào còn PENDING sau một lượt sẽ tạm nghỉ 120 giây thay vì chặn khu kế
tiếp. Khi cửa sổ mới bắt đầu, thứ tự trên được áp dụng lại từ Event Center.

- `gift_claims.valuable_event.run`: chỉ Valuable Event. Key tổng `gift_valuable_event`.
- `gift_claims.super_value_return.run`: Login Gifts, Empire Depot, Lucky Raffle,
  City Growth Plan Stage 1 và Refining Weekly Card. Key tổng
  `gift_super_value_return`.
- `gift_claims.event_center.run`: Back to Territory (icon ngoài) + các event con trong danh sách Limited của Event
  Center. Key tổng `gift_event_center`.
- Revelry Carnival: trước hết quét toàn bộ vùng xanh nhận quà từ đầu tới cuối
  và nhận mọi Claim xanh. Chỉ sau một lượt đầy đủ không còn Claim xanh mới
  bấm Parade Mask. Nếu sau cú bấm thấy ảnh `paradeMaskDone` (dòng "You can get
  items from:") thì DONE ngay. Nếu Mask mở popup số lượng thì chọn Max, Use,
  nhận hết Claim mới sinh ra, rồi bấm Parade Mask lần nữa; chỉ ảnh
  `paradeMaskDone` ở lần kiểm tra này mới DONE toàn nhiệm vụ. Key
  `revelry_carnival_parade_masks_used` chỉ checkpoint việc đã Use khi bị ngắt,
  không phải DONE. Sau mỗi Claim/Use, nếu hiện Congratulations thì Back đúng
  một lần và chờ popup biến mất hoặc nút Claim hiện rõ.

Mỗi nhiệm vụ con có key `daily_done` riêng (ví dụ `gift_limited_offer`). DB lưu timestamp ISO;
`BotWorker.is_daily_done()` so với lần reset server gần nhất (mặc định 14:00, lấy từ DB settings): 15:00 ngày 15/10 thì
bản ghi 21:05 ngày 14/10 là **chưa làm**, 13:59 thì vẫn **đã làm**. Key hết hạn tự động, DB không xoá khi sang ngày.

## Cấu trúc

```
gift_claims/
├── scan.py                      # vòng kiểm tra 3 lần dùng chung cho cả hai hoạt động
├── valuable_event/
│   ├── zone.py                  # run(bot) của hoạt động Valuable Event (3 lượt tìm)
│   ├── run.py                   # SPECS: ảnh tab + flow của từng event
│   ├── named_flow/              # ExactFlow / process_exact dùng chung (cả super_value_return)
│   └── <từng event>/run.py      # TASK = GiftTask(key, nhãn, run)
├── super_value_return/          # key tổng gift_super_value_return
│   ├── zone.py                  # run(bot) của hoạt động Super Value Return
│   ├── run.py                   # quét carousel Super Value Return
│   └── login_gifts/, empire_depot/, lucky_raffle/, city_growth_plan/, refining_weekly_card/
├── back_to_territory/           # Thanh phải ngoài thành, tính vào hoạt động Event Center
│   └── run.py
└── event_center/
    ├── zone.py                  # run(bot) của hoạt động Event Center
    ├── run.py                   # quét Limited trước, rồi Activities
    └── <từng event>/run.py
```

## Trình tự (`scan.run_zone`)

1. Hoạt động đã có key tổng hôm nay: bỏ qua. Nhiệm vụ con đã xong hôm nay: bỏ qua, chỉ làm các nhiệm vụ còn lại.
2. Một **lượt** = tìm từng event còn lại (mở trang cha bằng vị trí/launcher cố định, không dựa vào chấm đỏ):
   - Thấy: nhận quà theo quy tắc nhóm bên dưới, ghi key xong của event đó, đưa số lần "không thấy" về 0.
   - Không thấy: back về màn chính, ghi thêm một lần "không thấy" (key `<key>_miss_1..3`).
3. Mỗi cửa sổ chạy Event Center ghi tối đa một lượt `miss` cho từng category đã
   quét đủ. Lượt kế tiếp sau 120 giây đọc lại `miss_1/2/3` từ DB; event không
   thấy trong đủ 3 lượt = hôm nay không có, ghi key xong. Nếu Limited đã quét
   đủ nhưng timeout xảy ra trong Activities, checkpoint Limited vẫn được giữ.
   Đồng thời DB lưu category cần chạy trước: Limited xong thì lượt kế tiếp ưu
   tiên Activities; Activities xong thì chuyển lại Limited. Vì vậy một category
   dài không thể chiếm đầu mọi cửa sổ 120 giây.
   Valuable Event và Super Value Return cũng dùng các key `miss_1/2/3`; thấy
   event ở bất kỳ lượt nào thì đưa bộ đếm không thấy về 0.
4. Không mở được trang cha (launcher/Event Center không hiện) **không** tính là "không thấy": lượt đó dừng, chờ lần chạy sau.
5. Mọi nhiệm vụ con xong thì ghi key tổng của hoạt động.
6. Số lần "không thấy" lưu trong DB nên nhường Join Boss hay khởi động lại vẫn đếm tiếp. Hết giới hạn 120 giây hoặc có
   boss mới thì không ghi DONE cho bước đang dở.

Facebook/Follow Us luôn bị loại. Các mảng đỏ sát nhau trên cùng một icon phải được gộp thành một badge thật.

Trong Valuable Event và Super Value Return, ba lượt quét của cùng một lần chạy
giữ nguyên màn cha đang mở. Task nhìn thấy nhưng chưa đạt điều kiện DONE được
giữ PENDING; bot tiếp tục làm task kế tiếp. Chỉ task không xuất hiện trong cả
một lượt quét mới được cộng `miss`, và chỉ thoát màn cha sau khi toàn khu kết
thúc hoặc lượt chạy bị ngắt.

Mỗi vị trí carousel chỉ xử lý một tab từ một ảnh chụp: hoàn tất toàn bộ flow
vùng dưới, chốt DONE/PENDING, nghỉ 1 giây, chụp lại rồi mới lướt vùng trên.
Không tái sử dụng tọa độ của các tab còn lại từ ảnh cũ. Carousel lướt trong 1
giây và chờ 1 giây để các máy chạy đồng thời có thời gian ổn định giao diện.

## Valuable Event (`valuable_event/zone.py`)

Không dùng `scan.run_zone` / đếm "không thấy" từng event: đếm theo LƯỢT TÌM, tối đa 3 lượt mỗi ngày (key DB
`gift_valuable_event_pass_1..3`, hết hạn theo mốc reset; Start lại vẫn đếm tiếp).

Một lượt tìm (`search_pass`):

1. Mở từ màn chính (`open_valuable_event`): ở màn chính (có nút •••; không ở đó thì `return_home`) truyền ảnh vào
   `bot/ocr/find_valuable_event.py` `find_valuable_event` (so mẫu chữ "Event" trong `Images/GiftClaims/ValuableEvent/event_text/`,
   không khớp thì OCR). Thấy thì bấm icon (cao hơn tâm chữ "Event" 30 px), cứ 1 giây chụp kiểm tra tiêu đề `ValuableEvent/title`,
   tối đa 8 lần. Không thấy nút / 8 lần chưa vào: làm lại, tối đa 3 lần; vẫn chưa vào thì trả False
   (key tổng chưa có trong DB: worker gọi lại lần sau).
2. `do_visible`: làm các event cần làm đang thấy ở hàng tab (`run.py` `_tab`: ưu tiên ảnh icon KHÔNG chữ `<Event>/tab_icon.png` — dải thông báo chạy chữ hay đè lên dòng tên tab — ngưỡng 0.8; chưa có icon thì dùng ảnh có chữ trong `SPECS`; Super Blazon Sale có icon giống hệt Journey to Glory nên phải khớp thêm chữ tên cùng cột): bấm tab bên trái nhất (`open_tab`: tab đã được chọn sẵn (nền sáng: dải y 16.4-17.1% dưới chữ tên tab, độ sáng TB >= 60, tab thường ~33) thì không bấm tab, chỉ bấm x 50% y 5% (chỗ tiêu đề) rồi nghỉ 1s; còn lại trước khi bấm cắt ô x 2-30% y 20-30% dưới hàng tab; bấm vào chính giữa ô tab (x của tab tìm được, y 13% màn: ô tab y 62-122 trên màn 704; bấm vào tâm icon y ~75 thì Optional Package không nhận); cứ 1s kiểm tra ô đó đã đổi chưa (khớp < 0.9 = đã sang event; sang rồi thì bấm x 50% y 5% (chỗ tiêu đề), nghỉ 1s), tối đa 5 lần; chưa thì bấm lại tab 1 lần, chờ tiếp 5 lần; vẫn chưa thì bỏ qua event trong lượt này, lượt sau làm tiếp), chạy flow riêng
   (`process_exact`), xong thì DONE, chưa xong thì giữ PENDING và không thử lại trong lượt; chụp lại, lặp tới khi không còn.
3. `swipe_to_left_edge` (một lần mỗi lượt), tối đa 8 cú: cú đầu kéo dài x 5% -> 1000%, từ cú thứ 2 kéo ngắn x 5% -> 95%, y 12%;
   sau mỗi cú nghỉ 1s rồi cắt một icon ở hàng tab; sau cú kế tiếp icon đó vẫn thấy (khớp >= 0.8) và lệch <= 20 px = đã tới giới
   hạn bên trái. Rồi `do_visible`.
4. `scan_to_right_edge`: kéo ngắn x 60% -> 5%, y 12% (phải sang trái), tối đa 30 cú, mỗi chỗ `do_visible`; trước mỗi cú cắt icon
   ngoài cùng bên trái, kéo xong nghỉ 1s icon đó vẫn đứng nguyên chỗ (khớp >= 0.8, lệch <= 2 px; đổi chỗ thì chưa phải) = hàng tab không dịch; phải 2 cú liên tiếp không dịch mới là chạm bên phải (popup sau khi nhận quà phủ lên làm cú kéo không dịch, từng làm bot báo chạm phải khi mới tới Super Blazon Sale). 95% -> 5% dịch ~4 tab một
   cú nên sót tab; 60% -> 5% đi hết 12 cú, mọi tab đều hiện đủ (thử trên 21913). Icon tab có khung cánh vàng giống nhau nên phải
   xét cả độ lệch, không chỉ "còn thấy".
   Sau MỖI cú kéo (dài / ngắn), nghỉ 1s rồi chụp: thấy dấu X đỏ của dải thông báo chạy chữ (y 92-116) thì bấm tắt
   (`find_notice_x`: chỉ nhận hình dấu X — cụm đỏ nét mảnh, phủ cả hai đường chéo — không đọc chữ thông báo vì mỗi lần mỗi khác).
   Trước MỌI cú kéo (cả kéo về trái lẫn kéo ngắn): `wait_title_clear` — thanh tiêu đề (y 0-6%) phải khớp ảnh cắt lúc vừa vào màn
   (`capture_title`, mỗi lượt cắt lại; chỉ là biến truyền giữa các hàm của lượt, không gắn lên bot — hết lượt / sang nhiệm vụ khác là không còn) ở ngưỡng 0.99, so chênh lệch điểm ảnh (1 - chênh lệch TB / 255) để nhạy cả lớp phủ tối
   (chụp lúc khác nhau giống 1.0; phủ tối 10% -> 0.978). Không khớp thì chờ 1s, tối đa 5 lần; vẫn không khớp thì Back rồi kiểm tra
   lại; vẫn không khớp thì dừng lượt (không tính).
5. Chạm bên phải (hoặc mọi event cần làm đã xong): ghi `gift_valuable_event_pass_N`, bấm Back, lượt mới làm lại từ bước 1.
   Lượt nào thấy event MỚI (chưa thấy ở các lượt trước của lần chạy này) thì đếm lại: xoá các key lượt, lượt đó tính là lượt 1
   (VD lượt 1 không thấy A, lượt 2 thấy A -> lượt 2 là lượt 1). Event lượt nào cũng thấy mà chưa DONE chỉ reset lần đầu, không lặp mãi.
   Lưu ở đâu: số lượt ghi DB (`gift_valuable_event_pass_N`, còn qua Stop/Start, tự hết hạn theo mốc reset); event đã thấy hôm nay
   để trên context (`seen_today`, còn qua các lần bị ngắt trong lần Start, Start lại / qua mốc reset thì rỗng); event đã thử trong
   lượt (`attempted`) chỉ là biến của lượt đó.
   Lượt chưa đi hết (không mở được / 30 cú chưa chạm phải) không được tính; lần chạy sau làm lại.

Đủ 3 lượt (hoặc mọi event đã xong): ghi DONE mọi event của hoạt động và key tổng `gift_valuable_event`.

## Trong từng trang con

1. Bấm nút điều hướng/phần thưởng cố định như Rewards, Star Trail Gift, Sprint Package, Stockpile hoặc Scores.
2. Tìm các nút nhận thật: Claim, Free, Claim Free, Claimable, Daily Free, Claim All.
3. Thấy nút X của popup/mục không nhận được thì dùng Back để thoát, không bấm trực tiếp vào X.
4. Dò điểm lấp lánh trong vùng nội dung an toàn (Valuable Event cần 3 vòng liên tiếp không nhận thêm quà, Event Center lấy
   3 mẫu mỗi lượt); không bấm vùng mua hàng, thanh tài nguyên hoặc phần thưởng trả phí.
5. Xác minh mỗi lần nhận bằng Congratulations, nút vừa bấm biến mất, hoặc trạng thái Claimed ở đúng phần thưởng. Chỉ bấm
   nút điều hướng không được tính là đã nhận quà.
6. Trên carousel, mỗi dấu đỏ chỉ thuộc tab có tâm gần nó nhất.

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
- Ảnh tab nhiệm vụ trên carousel dùng ngưỡng cao `0.82`. Không thấy một tab
  sau một lượt quét đầy đủ chỉ ghi `miss 1/3`; đủ ba lượt quét đầy đủ không
  thấy mới ghi task đó DONE. Không còn chấm đỏ trong một lượt cũng không được
  bỏ qua quy tắc ba lượt này.
- Super Value Return: thấy tab nào thì xử lý tab đó, không ưu tiên theo danh
  sách. Empire Depot và Lucky Raffle dùng Claimable; City Growth Plan ưu tiên
  Claim All rồi chỉ nhận cột miễn phí bên trái. Hall of Historic Generals dùng
  chữ + dải màu để tách Claim xanh khỏi Claimed xám và chỉ ghi DB DONE sau một
  lượt xác nhận toàn bộ Claimed. Soul of Spiritual Beast quét dọc riêng hai tab
  Daily Tasks và Seasonal trong vùng nhiệm vụ; có Claim trong lượt thì nhận hết,
  quay lại màn Challenge Quest và vét rương. Rương biến mất là điều kiện kết
  thúc kể cả khi Congratulations không xuất hiện. Lượt có nhận chỉ ghi DONE_1;
  chỉ khi cả hai tab đã toàn bộ Claimed mới ghi DONE tổng.
- Login Gifts: chỉ bấm khi tìm đúng ảnh `button_reward_chest`; nếu không thấy
  thì giữ PENDING, không dùng tọa độ dự phòng. Không dùng chấm đỏ hay quét rương theo từng hàng. Sau
  khi bấm phải chờ và đóng Congratulations nếu có, sau đó chụp lại. Chỉ khi
  trang Login Gifts vẫn mở và hai frame liên tiếp không còn nút rương mới DONE;
  Congratulations một mình không đủ điều kiện.
- Back to Territory nằm ở thanh phải cùng vùng ngoài thành với Event Center,
  nhưng là màn ngang cấp và không phải event con của Event Center. Với mỗi tab
  đỏ trên carousel, duyệt tiếp toàn bộ badge đỏ
  ở hàng Day và Daily Login/Stamina/Daily Activity bên dưới; quét dọc danh sách
  để nhận tất cả nút Claim trùng nhau. Chỉ sau đó mới dò sparkle; một sparkle
  không sinh Congratulations thì dừng tab đó. Nếu người dùng bấm Stop giữa
  tab, tab đó chưa được ghi nhớ và phải được mở lại ở lần chạy sau.
- Event Center: không nhận diện hoặc bấm theo dấu đỏ ngoài danh sách. Bot chỉ
  tìm và mở các nhiệm vụ đã được đăng ký bằng ảnh tên dòng trong code; các dòng
  mua hàng/xã hội hoặc nhiệm vụ chưa có ảnh tên sẽ bị bỏ qua. Quét xong toàn bộ
  nhóm Limited trước rồi luôn chuyển sang
  Activities; không vào Competition. Một nhiệm vụ đã thấy nhưng chạy hết flow
  riêng mà chưa DONE được giữ PENDING và không được mở lại trong cùng lượt
  120 giây. Mỗi nhóm
  đưa danh sách về biên đầu rồi quét đến biên cuối, mỗi biên chỉ được xác nhận
  sau hai cú lướt ổn định liên tiếp không làm danh sách di chuyển. Event Center
  dùng Hamming trên cấu trúc dọc 96 dải của phần trái danh sách, ngưỡng `8/96`,
  để bỏ qua artwork, đồng hồ và dòng mô tả động. Không có
  giới hạn cứng số vị trí; Stop/deadline 120 giây là giới hạn an toàn. Ở
  từng vị trí bot log rõ danh sách tên nhiệm vụ còn pending trước khi dò và
  bấm. Event không xuất hiện trong một lượt quét đầy đủ được log `lần 1/3`,
  `2/3`, `3/3`; sau ba lượt mới coi là hôm nay không có và ghi DONE.
  Eagle of Freedom mở đúng trang theo title, quét dọc tới khi danh sách không
  di chuyển hai lần liên tiếp, nhận từng nút Claim và chỉ DONE sau khi đã lướt
  hết mà không còn Claim. Ảnh `Claimed` được loại trừ trước khi tìm `Claim`,
  vì template của từ ngắn có thể khớp nhầm vào đầu từ dài.
  Legion Hunting cũng mở bằng dòng tên và xác nhận bằng title riêng; bot chỉ
  lướt trong khung nhiệm vụ màu xanh, nhận mọi nút Claim và chỉ DONE sau một
  lượt quét đầy đủ từ đầu tới đáy không còn Claim.
  Một tọa độ Claim chỉ được bấm một lần trong cùng một vùng để tránh lặp vô hạn
  khi giao diện lag hoặc nút chưa kịp biến mất.
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
  cuộn tiếp. Sau một vòng quét đầy đủ, trạng thái hoàn tất chỉ dựa trên các
  nhiệm vụ tên đã đăng ký và key DB; dấu đỏ còn lại không chặn DONE.
- Revelation of Horus và Sealed Imperial Treasury được nhận diện theo tiêu đề,
  bỏ qua ngay và coi là DONE.
- Grace of Star Trail bấm icon `Star Trail Gift`, chờ màn con rồi bấm tiếp icon
  đồng xu có chữ `Claim`; chỉ bước thứ hai mới tính là nhận xu. Dwarf's Treasure
  dùng crop gồm cả rương `Daily Free` để tâm ảnh nằm trong vùng bấm thật.
- Limited chủ động tìm mọi dòng tên đã đăng ký, bao gồm Grace of Star Trail.
  Việc cuộn danh sách dừng sớm khi ảnh ổn định ở biên; các
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
