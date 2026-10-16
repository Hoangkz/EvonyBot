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
3. Làm **hết 10 lượt trong ngày** (`PATROL_GOAL` = 10 × 10, dù nhiệm vụ "Patrol for 3 time(s)" chỉ cần 1 lượt), dừng
   sớm khi nút Refresh xám / Refresh không ra bộ mới → Back, đánh dấu xong hôm nay.
4. Không nhận ra màn / nút giữa chừng → dừng, không đánh dấu.
