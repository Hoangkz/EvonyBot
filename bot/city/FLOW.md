# Flow: Bản đồ thành và route công trình (bot/city)

Dùng chung, không thuộc activity nào. Code: [city_map.py](city_map.py), dữ liệu: [city_tour.py](city_tour.py) (chỉ đúng civ1,
`SUPPORTED_CIVS`). Việc còn lại: [TODO.md](TODO.md). Black Market chỉ **dùng** bản đồ trong DB để tới Chợ
(`goto`), **không quét** — quét do worker làm khi rảnh.

## Tìm route công trình (city_map.scan_city) — chạy khi rảnh

Khi **không còn nhiệm vụ nào và Join Boss rảnh** mà máy chưa có bản đồ thành (DB `devices.city_map`), worker gọi `scan_city`
([bot_worker.py](../worker/bot_worker.py), mỗi lượt Start thử một lần). Ở vị trí bất kỳ:

1. **Tìm Thành chính trước** (`find_keep`): thấy Thành chính thì kéo bù vào giữa; thấy một công trình cố định (`FIXED` trong
   [city_tour.py](city_tour.py): Walls, Research Factory, Tavern, Archer Tower, Watchtower, Art Hall, Pasture, Rally Spot) thì đi
   đúng đường cố định `ROUTES` về Thành chính; không thấy gì thì dò vòng xoáy quanh chỗ đứng (`spiral_swipes`, tối đa 40 cú).
2. **Quét từng ô** (`scan`, 13 ô trong `DATA`): ghi toạ độ công trình nhận ra được.
3. **Lưu vào DB** (`bot.set_city_map`); không lưu file.

Điểm tựa vuốt: mọi cú vuốt đi qua `city_map.swipe` / `swipe_from_to`; cứ 3 cú gọi `watch` (worker `_watch_boss_count`): đọc số
boss trên huy hiệu đỏ của icon `Images/JoinBoss/listboss.png` (OCR `bot/ocr/read_boss_count.py`, font `Images/OCR/BossCount`, không
có icon = 0). Bằng thì vuốt tiếp; giảm thì ghi đè số cũ; tăng thì vào Join Boss tới khi rảnh rồi đọc lại số và vuốt tiếp.
Test: `tests/city/test_city_map.py`, `tests/worker/test_boss_watch.py`, `tests/join_monster_war/test_boss_count.py`.

## Hướng dẫn đo route cho một nền văn minh

Làm khi cần quét thành trên máy civ N (N khác 1). Bố cục thành khác nhau theo civ nên **không dùng số civ1**. Dữ liệu cần đo, trong
[city_tour.py](city_tour.py): `FIXED` (toạ độ các công trình cố định so với Thành chính), `ROUTES` (đường vuốt giữa Keep và từng
mốc), `ANCHOR_SHIFT` (độ lệch tâm "chính giữa"), `DATA` (13 ô quét). Số liệu civ1 là mẫu để đối chiếu (tên, thứ tự).

**1. Chuẩn bị**
- Máy civ N đang ở màn thành (không phải thế giới; ở thế giới bấm nút toà thành góc dưới phải). `bot.civilization` hoặc ảnh mẫu
  phải nhận ra civ: kiểm tra ảnh `Images/Event/Building/civ<N>/<công trình>/` có đủ Keep, Walls, Research Factory, Tavern, Archer
  Tower, Watchtower, Art Hall, Pasture, Rally Spot, Trap Factory, Prison... và **đúng công trình** (từng có ảnh Prison cắt nhầm Trap
  Factory). Kiểm tra điểm khớp: `.\venv\Scripts\python.exe .claude\skills\template-images\scripts\probe.py match <ảnh> -s <serial>`
  (>= 0,9 khi công trình ở giữa màn).
- Chụp màn: `probe.py shot -s 127.0.0.1:<cổng> -o shot.png`. Đọc ảnh để biết đang ở công trình nào.

**2. Cách vuốt khi đo** (rất quan trọng)
- Vuốt chậm: 2,5 giây, chờ 2 giây cho camera dừng (`city_map.SWIPE_TIME`, `SWIPE_WAIT`). Một cú dài tối đa (240, 260) px; xa hơn thì
  chia nhiều cú giống nhau (thẳng hàng).
- **Điểm đầu và cuối phải ở đất trống**, không trúng icon / rương / dấu hỏi trên đám lính: game coi là bấm, camera không dịch (dễ nhầm
  là camera chạm mép thành). Sau mỗi cú so ảnh trước / sau; không đổi thì vuốt lại bằng điểm khác.
- Ngón tay vuốt sang trái thì nội dung dịch sang trái (công trình đi sang trái màn).

**3. Đo từng mốc** (từ Keep ở giữa màn)
1. Kéo Keep vào chính giữa màn (như người chơi thấy là giữa). Ghi vị trí ảnh mẫu Keep lúc đó; nếu không ở (197, 345) thì ghi độ lệch
   vào `ANCHOR_SHIFT` (Walls (49, 0) và Tháp cung thủ (-68, -41) ở civ1 đều có độ lệch vì ảnh mẫu không đúng giữa công trình).
2. Vuốt tới công trình cố định (chia cú đều nhau), đến khi nó ở **chính giữa** (người đo xác nhận). Cộng tổng các cú vuốt = vector
   Keep -> công trình. Ghi `FIXED[công trình] = vector` và `ROUTES[("keep", công trình)] = [cú] * số cú`.
3. Đo chiều ngược lại (`(công trình, "keep")`) bằng cách vuốt thật, không chỉ đảo dấu; công trình ở xa Keep thì nối qua công trình
   gần hơn (Tháp cung thủ qua Walls, Tháp canh / Art Hall qua Research Factory, Pasture qua Art Hall).
4. Hai công trình cùng một màn: lấy hiệu toạ độ ảnh mẫu trên **cùng một ảnh** thay vì cộng nhiều cú (không cộng dồn sai số).

**4. Đo 13 ô quét (`DATA`)**: với mỗi ô, một cú vuốt từ Keep (hoặc từ ô trước) tới khi công trình của ô ở giữa màn; ghi `swipes`, `view`
(toạ độ camera) và công trình thấy ở đó. Chạy `scan` thử một vòng, so toạ độ quét với `view` (lệch tới ~90 px là bình thường vì quét
có bước kéo bù).

**5. Ghi dữ liệu và bật civ**
- Tách bảng theo civ trong `city_tour.py` (xem TODO mục 5), thêm civ N vào `SUPPORTED_CIVS` **chỉ khi đã có đủ** bảng của civ đó.
- Cập nhật test `tests/city/test_city_map.py` (danh sách tên ô, `FIXED`, `ROUTES` khớp hiệu toạ độ trong 20 px) rồi chạy:
  `.\venv\Scripts\python.exe -m unittest tests.city.test_city_map`.

**6. Chạy thật để kiểm**: quét một vòng trên máy civ N (script gọi `city_map.scan_city(bot, "City scan", watch)`; kiểm tra log "found,
fixed route to the Keep" và đủ 13 ô, `scan_city -> True`), đứng ở nhiều chỗ khác nhau (kể cả bản đồ thế giới, chỗ không thấy mốc nào)
để thử `find_keep`. Sau khi quét, `goto` thử vài công trình (Chợ, Walls...) xem vào giữa màn trong 25 px (`TOLERANCE`).
