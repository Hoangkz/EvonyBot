# Flow: Troop Training

Nhiệm vụ Daily Activities. Ảnh / action: [constants.py](constants.py), handler: [run.py](run.py).
Phần dùng chung (mở Quests → Activity, tìm dòng, bấm Go, state machine `run_task`): [../FLOW.md](../FLOW.md).

## Luồng mới (`run.after_go`, sau khi `common.open_task` bấm Go)

Code chung với Trap Building: [../train.py](../train.py) `train_after_go`.
Giống King's Path Train Troop (`event/kings_path/train_troop`), dùng lại các bước của
`event/gather_troops/train_troop` (ảnh màn Train, Training Speedup, Finish All).

1. Go → về thành, game kéo tới công trình train **ngẫu nhiên 1 trong 4 loại** (Barracks / Archer Camp / Stables /
   Workshop) → bấm công trình → menu.
   - Menu có "Train" → bấm.
   - Công trình đang train (menu có "Speed Up") → Speed Up → Finish All mẻ đó (không tính) → mở lại menu.
2. Màn Train (nút "i" góc trên): còn mẻ đang train ("Training Speedup") → bấm, Finish All trước.
3. Chọn **cấp I** (`kings_path/train_troop/tier.py`).
4. **Không nhập số**: giữ số mặc định của ô (tối đa một lần train, OCR `read_train_count`).
   Số mẻ = ceil(300 / số mỗi mẻ) (`TRAIN_GOAL`); số mặc định lớn hơn 300 thì train cả mẻ lớn hơn.
5. Mỗi mẻ: Train → nút thành "Training Speedup" → bấm → lần đầu "Speedup Settings" → tích ô dùng speedup
   thường → Confirm → **Finish All** → về màn Train.
6. Đủ mẻ, nút Train hiện lại → đánh dấu xong hôm nay (`mark_task_done`), Back đóng màn Train.
7. Quá `MAX_STEPS` vòng / không chọn được cấp I / không đọc được số mỗi mẻ → ghi lịch sử, không đánh dấu.

## Luồng cũ C# (`common.run_task` + `run.handle`, `run.py` chung vẫn đang dùng)

1. Mở từ hàng `TrainTroop.png`.
2. `Train.png`: bấm vào mục Train chung.
3. `TrainInterface.png`: vuốt ngang carousel quân.
4. `TrainSoldierCurrent.png`, `TrainSoldierSelectedCurrent.png` hoặc
   `TrainSoldier1.png`: nhập số lượng 500 và xác nhận.
5. `TroopSpeed.png`: dùng nút speedup hiện tại.
6. `TroopFinish.png` hoặc `TroopFinish1.png` báo hoàn thành.
