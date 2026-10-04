# Flow: Black Market

Nhiệm vụ Daily Activities. Ảnh / action: [constants.py](constants.py), handler: [run.py](run.py).
Phần dùng chung (mở Quests → Activity, tìm dòng, bấm Go, state machine `run_task`): [../FLOW.md](../FLOW.md).

1. Mở từ `ActivitiesBlackMarket.png` rồi `BuyMarket.png`.
2. Khi thấy `Market.png` hoặc `Market1.png`, tìm lần lượt các mặt hàng tài
   nguyên: food, lumber, ore, stone.
3. Mỗi lần mua bấm xác nhận tại `(190, 415)`.
4. Tối đa ba lần mua trong lượt rồi Back.
5. Không dùng tọa độ Instant Refresh cũ vì client hiện tại tính phí gem.
6. `BlackMarketFinishCurrent.png` hoặc `BlackMarketFinish.png` báo hoàn thành.
