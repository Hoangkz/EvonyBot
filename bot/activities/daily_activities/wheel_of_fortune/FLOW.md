# Flow: Wheel of Fortune

Nhiệm vụ Daily Activities. Ảnh: [constants.py](constants.py), phần làm sau Go (`after_go`): [run.py](run.py).
Phần dùng chung (mở bảng Activity, tìm dòng / thẻ, bấm Go): [../OPEN_TASK.md](../OPEN_TASK.md), [../FLOW.md](../FLOW.md).

## Luồng mới (`run.after_go`, sau khi `common.open_task` bấm Go)

Như King's Path Wheel sau Go: dùng chung `event/kings_path/wheel/run.py` `spin_wheel`, nhưng chỉ 1 lần 10 Spins
(`max_spins_10=SPINS_10_GOAL`).

1. Go → game mở thẳng màn **Wheel of Fortune** (chờ tối đa 10 s).
2. Có nút **"100 Spins"** (đủ chip) → bấm → Back → xong hôm nay.
3. Không có → bấm **"10 Spins"** đúng **1 lần** (`SPINS_10_GOAL`) → Back → xong hôm nay. Không quay tới hết chip,
   không vào màn Purchase Chips. (Hết chip ngay lần bấm đầu: game tự mở **Purchase Chips** → Back → xong hôm nay.)
4. Không thấy màn Wheel / quá số bước → không đánh dấu.
