# Flow: Patrol

Nhiệm vụ Daily Activities. Ảnh / action: [constants.py](constants.py), handler: [run.py](run.py).
Phần dùng chung (mở Quests → Activity, tìm dòng, bấm Go, state machine `run_task`): [../FLOW.md](../FLOW.md).

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

## Luồng cũ C# (`common.run_task` + `run.handle`, `run.py` chung vẫn đang dùng)

1. Mở từ `ActivitiesPatrol.png`.
2. `Patrol.png`: vào màn Patrol.
3. Với `Patrol1.png`, chạy ba lượt:
   - Lượt đầu: Select All → Patrol.
   - Lượt hai và ba: Refresh bằng gold → Select All → Patrol.
4. Back sau ba lượt.
5. `PatrolFinishCurrent.png` hoặc `PatrolFinish.png` báo hoàn thành.
