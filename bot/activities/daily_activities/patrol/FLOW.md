# Flow: Patrol

Nhiệm vụ Daily Activities. Ảnh: [constants.py](constants.py), phần làm sau Go (`after_go`): [run.py](run.py).
Phần dùng chung (mở bảng Activity, tìm dòng / thẻ, bấm Go): [../OPEN_TASK.md](../OPEN_TASK.md), [../FLOW.md](../FLOW.md).

## Luồng mới (`run.after_go`, sau khi `common.open_task` bấm Go)

Giống hệt King's Path Patrol sau Go: dùng chung `event/kings_path/patrol/run.py` `patrol_rounds`.

1. Go → về thành, **Tường thành** ở giữa → menu "Patrol" → màn Patrol (`open_building`).
2. Mỗi bước chụp 1 ảnh:
   - đã patrol lượt hiện tại (phần thưởng có dấu tích lớn) → Refresh (ra bộ mới);
   - ô "Select All" chưa tích → bấm ô;
   - đã tích → "Patrol" → chờ màn chuyển sang "đã patrol" → +10 tiến độ, lưu lượt hôm nay (`round_key`, đếm riêng:
     `daily_patrol_round_<n>`; King's Path đếm riêng của nó, hết lượt thật thì nút Refresh xám → tự dừng).
3. Đủ `PATROL_REQUIRED` = 1 lượt (nhiệm vụ "Patrol for 3 time(s)" chỉ cần 1 lượt): **lưu ngay "xong hôm nay" (`daily_patrol`) vào DB**,
   rồi patrol tiếp trong cùng lần chạy tới khi bị ngắt (hết thời gian / boss mới) hoặc đủ 10 lượt (`PATROL_GOAL`) / nút Refresh xám /
   Refresh không ra bộ mới → Back, lưu thêm `daily_patrol_more`. Không còn `must_finish`.
4. Không nhận ra màn / nút giữa chừng → dừng, không đánh dấu.

## Việc nối tiếp `daily_patrol_more` (`run.MORE_JOB`, không đi qua Go)

Cùng ưu tiên 387, xếp ngay sau Daily Patrol. Bỏ qua khi Daily Patrol chưa xong, hoặc `daily_patrol_more` đã lưu, hoặc đủ 10 lượt.
Chạy: về thành → tìm thành (`open_building`, Tường thành ở giữa) → màn Patrol → `patrol_rounds` (cùng key `daily_patrol`, nên
đếm tiếp lượt đã làm) → đủ 10 lượt / hết Refresh → Back, lưu `daily_patrol_more`. Bị ngắt: lượt sau làm tiếp từ lượt đã đếm.

Bước tới Tường thành của `daily_patrol_more` (`city_map.reach_building`, dùng chung với Greet Champion):
1. Về thành, **thấy Tường thành trên màn** → làm Patrol luôn.
2. Không thấy, máy **đã có route** (`bot.city_map` trong DB) → `city_map.goto` vuốt thẳng tới Tường thành.
3. Không thấy, máy **chưa có route** → `city_map.scan_city` tìm route và **lưu vào DB** (`bot.set_city_map`, lần sau dùng lại), rồi `goto`.
4. Không tới được (không tìm được route / không thấy mốc) → bỏ lượt này, lượt sau thử lại.
