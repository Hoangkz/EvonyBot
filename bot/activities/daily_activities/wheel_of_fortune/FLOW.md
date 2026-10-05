# Flow: Wheel of Fortune

Nhiệm vụ Daily Activities. Ảnh / action: [constants.py](constants.py), handler: [run.py](run.py).
Phần dùng chung (mở Quests → Activity, tìm dòng, bấm Go, state machine `run_task`): [../FLOW.md](../FLOW.md).

## Luồng mới (`run.after_go`, sau khi `common.open_task` bấm Go)

Giống hệt King's Path Wheel sau Go: dùng chung `event/kings_path/wheel/run.py` `spin_wheel`.

1. Go → game mở thẳng màn **Wheel of Fortune** (chờ tối đa 10 s).
2. Có nút **"100 Spins"** (đủ chip) → bấm → Back → xong hôm nay.
3. Không có → bấm **"10 Spins"** liên tục (không cần đóng bảng kết quả) tới khi hết chip: game tự mở màn
   **Purchase Chips** → Back → xong hôm nay.
4. Không thấy màn Wheel / quá số bước → không đánh dấu.

## Luồng cũ C# (`common.run_task` + `run.handle`, `run.py` chung vẫn đang dùng)

1. Mở từ `ActivitiesWheelofFortune.png`.
2. `WheelofFortune.png`: tìm `SpinOnce.png` và quay một lần.
3. Bấm đóng/phần thưởng tại `(170, 550)` rồi Back.
4. `SpinFinishCurrent.png` hoặc `SpinFinish.png` báo hoàn thành.
