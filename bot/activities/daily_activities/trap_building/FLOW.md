# Flow: Trap Building

Nhiệm vụ Daily Activities. Ảnh / action: [constants.py](constants.py), handler: [run.py](run.py).
Phần dùng chung (mở Quests → Activity, tìm dòng, bấm Go, state machine `run_task`): [../FLOW.md](../FLOW.md).

## Luồng mới (`run.after_go`, sau khi `common.open_task` bấm Go)

Code chung với Troop Training: [../train.py](../train.py) `train_after_go`; ảnh / bước giống Gather Troops
Defense Force (`event/gather_troops/defense_force`, xây bẫy).

1. Go → về thành, **Trap Factory** ở giữa → bấm → menu: "Build" → màn Train bẫy. Đang có mẻ xây ("Speed Up")
   → Trap Building Speedup → Finish All mẻ đó trước (không tính) → mở lại menu.
2. Màn Train bẫy: **không tìm loại / cấp** — dùng bẫy đang hiện khi vào; **không nhập số** — giữ số mặc định của
   ô (tối đa một lần xây).
3. Số mẻ = ceil(150 / số mỗi mẻ) (`TRAP_GOAL`): mỗi mẻ ≥ 150 thì 1 mẻ (lớn hơn 150 cũng được), nhỏ hơn thì xây
   nhiều mẻ cho đủ. Mỗi mẻ: Build → nút "Training Speedup" → Trap Building Speedup → (lần đầu Speedup
   Settings, tích ô, Confirm) → Finish All.
4. Nút Build hiện lại → đánh dấu xong hôm nay, Back đóng màn Train.

## Luồng cũ C# (`common.run_task` + `run.handle`, `run.py` chung vẫn đang dùng)

1. Mở từ `ActivitiesBuildTrap1.png` rồi `Build.png`.
2. `BuildInterface.png`: chọn trap tier I hiện tại, nhập 150 và xây.
3. `Trap-i.png`: trường hợp đã ở màn chọn trap, nhập 150 và xây trực tiếp.
4. `TrapSpeed.png`: dùng speedup, sau đó Back.
5. `TrapFinish.png` hoặc `TrapFinish1.png` báo hoàn thành.
