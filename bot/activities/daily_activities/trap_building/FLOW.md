# Flow: Trap Building

Nhiệm vụ Daily Activities. Ảnh: [constants.py](constants.py), phần làm sau Go (`after_go`): [run.py](run.py).
Phần dùng chung (mở bảng Activity, tìm dòng / thẻ, bấm Go): [../OPEN_TASK.md](../OPEN_TASK.md), [../FLOW.md](../FLOW.md).

## Luồng mới (`run.after_go`, sau khi `common.open_task` bấm Go)

Code chung với Troop Training: [../train.py](../train.py) `train_after_go`; ảnh / bước giống Gather Troops
Trap Factory (`event/gather_troops/trap_factory`, xây bẫy).

1. Go → về thành, **Trap Factory** ở giữa → bấm → menu: "Build" → màn Train bẫy. Đang có mẻ xây ("Speed Up")
   → Trap Building Speedup → Finish All mẻ đó trước (không tính) → mở lại menu.
2. Màn Train bẫy: **không tìm loại / cấp** — dùng bẫy đang hiện khi vào; **không nhập số** — giữ số mặc định của
   ô (tối đa một lần xây).
3. Số mẻ = ceil(150 / số mỗi mẻ) (`TRAP_GOAL`): mỗi mẻ ≥ 150 thì 1 mẻ (lớn hơn 150 cũng được), nhỏ hơn thì xây
   nhiều mẻ cho đủ. Mỗi mẻ: Build → nút "Training Speedup" → Trap Building Speedup → (lần đầu Speedup
   Settings, tích ô, Confirm) → Finish All.
4. Nút Build hiện lại → đánh dấu xong hôm nay, Back đóng màn Train.

Worker chạy luồng này: `priority.py` truyền `after_go` vào `daily_job` (open_task_or_finish → after_go).
