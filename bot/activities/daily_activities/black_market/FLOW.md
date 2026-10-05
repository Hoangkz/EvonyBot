# Flow: Black Market

Nhiệm vụ Daily Activities. Ảnh / action: [constants.py](constants.py), handler: [run.py](run.py).
Phần dùng chung (mở Quests → Activity, tìm dòng, bấm Go, state machine `run_task`): [../FLOW.md](../FLOW.md).

## Luồng mới (`run.after_go`, sau khi `common.open_task` bấm Go)

Giống hệt King's Path Black Market sau Go: dùng chung `event/kings_path/black_market/run.py`
(`open_black_market`, `buy_items`).

1. Go → về thành, **Chợ** ở giữa → menu → "Black Market" → màn Black Market.
2. Mỗi bước chụp 1 ảnh (6 món ở vị trí cố định):
   - vừa bấm một món mà hiện hộp "Are you sure you want to purchase ...?" → Confirm (+1 lần mua);
   - bỏ các món trả bằng **kim cương**; món còn mua được (nút giá xanh) → bấm, mỗi món 1 lần mỗi bộ hàng;
   - mua hết bộ → **Instant Refresh** (hết lượt miễn phí thì bằng kim cương, có hộp xác nhận thì Confirm) → chờ ô
     vật phẩm 1 đổi → mua tiếp bộ mới.
3. Đủ **5 lần mua** (`BUY_GOAL`) → Back, đánh dấu xong hôm nay.
4. Dừng giữa chừng (hết hàng / không thấy Instant Refresh / kẹt) → không đánh dấu, lần sau thử lại từ 0.

## Luồng cũ C# (`common.run_task` + `run.handle`, `run.py` chung vẫn đang dùng)

1. Mở từ `ActivitiesBlackMarket.png` rồi `BuyMarket.png`.
2. Khi thấy `Market.png` hoặc `Market1.png`, tìm lần lượt các mặt hàng tài
   nguyên: food, lumber, ore, stone.
3. Mỗi lần mua bấm xác nhận tại `(190, 415)`.
4. Tối đa ba lần mua trong lượt rồi Back.
5. Không dùng tọa độ Instant Refresh cũ vì client hiện tại tính phí gem.
6. `BlackMarketFinishCurrent.png` hoặc `BlackMarketFinish.png` báo hoàn thành.
