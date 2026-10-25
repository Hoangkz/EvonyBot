# Flow: Super Value Return (hoạt động độc lập)

1. Mở Super Value Return (`zone.open_super_value_return`): ở màn thành chính có nút ••• (đang ở bản đồ thế giới thì vào thành
   trước), tìm nút vào bằng `launcher.find_super_value_return`, xét theo thứ tự ưu tiên:
   - TH1: icon Login Gifts góc trên bên phải (`login_gifts_top`, vùng x 70-100% y 10-50%).
   - TH2: một icon trong `Images/GiftClaims/SuperValueReturn/launcher_icons/` ở vùng x 0-50% y 70-88%. Ảnh mẫu chỉ là vùng
     nhỏ trong icon, không có chữ, không chạm chấm đỏ. Nhiều chỗ khớp thì lấy chỗ có x bé nhất.
   - TH3: mũi tên đi lên (`arrow_up`, vùng x 0-30% y 70-88%): nút vào nằm ngay dưới, thấp hơn tâm mũi tên 40 px.
   - TH4: mũi tên đi xuống (`arrow_down`, vùng x 0-30% y 55-80%): bấm vào, nghỉ 1s cho thành mũi tên đi lên, rồi xét TH3.
   - TH5: lấy y của icon Valuable Event (`find_valuable_event`, cao hơn chữ "Event" 30 px), x = 40.
   Bấm rồi cứ 1s xem có tiêu đề Super Value Return chưa, tối đa 8 lần:
   - Vào được màn có tiêu đề Super Value Return: đúng, làm tiếp.
   - Vẫn ở màn thành: bấm lại nút đó 1 lần, chờ như trên; vẫn không vào thì bỏ Super Value Return khỏi danh sách nhiệm vụ
     tới khi bấm Start lại.
   - Sang màn khác: về thành, bỏ Super Value Return khỏi danh sách nhiệm vụ tới khi bấm Start lại.
   Bỏ qua = `skip_for_run` ghi trên context (không ghi DB); `gift_claims.job` coi là xong trong lần Start này.
Sau khi vào màn: giống Valuable Event (code riêng trong `zone.py`, không dùng chung file với Valuable Event).

2. `do_visible`: đóng popup che hàng tab (Depot Rewards Boost: `button_close_popup`; panel có nút X: Back). Tìm tab các event
   chưa xong (ảnh tab trong `run.py` `SPECS`, vùng y 7-19%), làm tab bên trái nhất trước: tab đã chọn sẵn thì không bấm; còn lại
   bấm chính giữa ô tab (x của tab, y 13%), cứ 1s xem trang đã đổi chưa, tối đa 5 lần, bấm lại 1 lần; sang trang rồi bấm chỗ
   tiêu đề (x 50% y 5%), nghỉ 1s, chạy flow riêng của event:
   - Login Gifts: `login_gifts.claim_opened` (nút `button_reward_chest`, không thấy thì bấm (45, 190); Congratulations hoặc
     hộp quà biến mất = DONE).
   - Refining Weekly Card: `refining_weekly_card.claim_opened` (quét khung xanh tới khi một lượt quét sạch nút Claim).
   - Empire Depot, Lucky Raffle, City Growth Plan Stage 1: `process_exact` với flow trong `SPECS` (City Growth Plan chỉ DONE khi
     thấy hàng 15 có dấu tích xanh).
   DONE thì lưu key của event; chưa thì giữ PENDING, không thử lại trong lượt.
3. Kéo dài hàng tab về giới hạn bên trái: cú đầu x 5% -> 500%, từ cú thứ 2 kéo ngắn 5% -> 95%, tối đa 8 cú; làm tiếp các event
   vừa hiện ra.
4. Kéo ngắn từ phải sang trái (60% -> 5%), mỗi chỗ làm các event đang thấy; icon ngoài cùng bên trái đứng nguyên chỗ 2 cú liên
   tiếp = chạm bên phải. Trước mỗi cú kéo, thanh tiêu đề phải khớp ảnh cắt lúc vừa vào màn (popup che thì chờ 1s x 5 rồi Back);
   sau mỗi cú thấy dấu X của dải thông báo thì bấm tắt.
5. Chạm bên phải: lưu DB đã xong lượt tìm N (`gift_super_value_return_pass_N`), Back, làm lại từ bước 1. Lượt thấy event mới
   thì đếm lại từ lượt 1. Đủ 3 lượt (hoặc mọi event đã xong): đánh dấu mọi event và key tổng `gift_super_value_return` là xong
   hôm nay, về màn thành.
