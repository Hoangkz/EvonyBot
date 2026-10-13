# Bản đồ thành và route công trình — việc còn lại


Luồng + hướng dẫn đo route cho nền văn minh mới: [FLOW.md](FLOW.md). Dữ liệu route ([city_tour.py](city_tour.py)) hiện **chỉ đúng civ1** (`SUPPORTED_CIVS`).

0. **Black Market chỉ chạy khi DB có route?** Hiện `_market` bỏ quét (không còn Go Gold Levy rồi quét), vẫn thử Chợ trên màn, bản đồ DB, rồi Go nhiệm vụ mua Black Market / Tax. Nếu muốn Black Market chỉ làm khi DB đã có route thì bỏ luôn bước Go nhiệm vụ.
1. **Route cho các nền văn minh khác (civ 2 .. 7)** — người dùng tự làm sau. Bố cục thành khác nhau theo civ nên `FIXED`,
   `ANCHOR_SHIFT`, `ROUTES`, `DATA` phải đo lại từng civ (máy 21933 là civ7; quét thử trên đó lệch trái 130 .. 220 px). Cần
   tách bảng theo civ (VD `CIV_DATA = {1: {...}, 7: {...}}`) rồi `city_map` chọn theo civ; hiện `SUPPORTED_CIVS = (1,)` chặn
   các civ khác (ghi log "chưa có route", không vuốt).
2. **Chạy thật cả luồng qua worker**: hết nhiệm vụ + Join Boss rảnh -> `scan_city` -> boss tăng thì vào Join Boss rồi vuốt tiếp
   -> lưu DB (`devices.city_map`). Mới chạy từng phần trên giả lập (21913 quét trọn 13 ô, 30 cú, 21 công trình; 21923 / 21943 từng
   đoạn); phần boss tăng chỉ test bằng mock. Bản đồ quét chưa được lưu vào DB của máy nào.
3. **Tắt bật game giữa lúc quét** (Auto Times Out / reset server): camera về chỗ mặc định, bot vẫn vuốt theo kế hoạch cũ. Cần phát
   hiện (game vừa mở lại / về thế giới) rồi bỏ phần đã quét, làm lại từ `find_keep`.
4. **Đường cố định mới chỉ thử một chiều**: Tháp cung thủ -> Walls -> Keep (9 cú, lệch ~70 px), Research Factory -> Tháp canh,
   Rally Spot -> Keep, Art Hall <-> Research Factory, Pasture <-> Keep, Keep -> Walls (đã thử, chiều ngược chưa). Chiều ngược
   hiện là đảo dấu số đo. Các đường nối nhiều cú (qua Walls / Research Factory) chưa thử cả đường.
5. **Vuốt tránh icon** (`city_map._swipe_checked`): ảnh không đổi sau cú vuốt thì vuốt lại bằng điểm đầu khác (`RETRY_SHIFTS`).
   Mới có test với ảnh giả, chưa thử thật khi điểm đầu rơi đúng rương / dấu hỏi.
6. **`find_keep` khi chưa biết civ**: `civ_of` chỉ biết civ khi thấy Keep / mốc cố định trên màn; chưa thấy mốc nào thì vẫn dò vòng
    xoáy rồi mới chặn civ chưa có route. Dò hết 40 cú ~ 3 phút. Nếu tốn thì chặn sớm theo `bot.civilization` (DB).
7. **Số boss OCR** (`bot/ocr/read_boss_count.py`, font `Images/OCR/BossCount`): mới có mẫu 0 .. 12; số >= 13 chưa thấy ảnh. Thêm
    bằng `add_sample BossCount` (xem skill ocr-samples) khi có ảnh huy hiệu.
8. **Toạ độ mốc cố định đo giữa các máy**: Walls / Research Factory đo trên 21943, Tavern / Tháp / Art Hall / Pasture / Rally Spot
    trên 21923, chưa kiểm chéo từng cái trên máy khác cùng civ1. Quét thật trên 21913 lệch số đo sẵn 20 .. 40 px (Research
    Factory [918, 31] so với [955, 49], Tavern [58, -244] so với [97, -231], Art Hall [1162, -82] so với [1190, -64]).
9. **Ảnh mẫu công trình civ 2 .. 7**: Prison và Trap Factory civ1 từng bị cắt nhầm (đã sửa); kiểm tra civ 2 .. 7 xem ảnh Prison,
    Trap Factory (và Keep / Walls / Research Factory...) đúng công trình. Bản đồ cũ trong DB còn key `defense_force` (đã đổi
    `trap_factory`) — xoá bản đồ cũ để quét lại.
10. **Test đang fail không do thay đổi này** (kiểm tra có sẵn ở bản gốc): `tests.worker.test_scheduler`
    (`test_negative_priority_not_in_task_list`, `test_event_sub_tasks`), `tests/event/gather_troops/siege_machine` + `trap_factory`
    flow test (16 test, cú bấm công trình lệch quá 15 px), `test_ui_tasks_match_execution_tasks` (UI thiếu Greet Champion).
11. Commit các thay đổi chưa commit (city_map / city_tour, đổi tên `trap_factory`, `alliance_research`, OCR BossCount, ảnh
    `listboss.png` mới, key `daily_done`).
