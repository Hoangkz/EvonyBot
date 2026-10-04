# Flow: Offering

Nhiệm vụ Daily Activities. Ảnh / action: [constants.py](constants.py), handler: [run.py](run.py).
Phần dùng chung (mở Quests → Activity, tìm dòng, bấm Go, state machine `run_task`): [../FLOW.md](../FLOW.md).

1. Tìm hàng `Offer.png`, kiểm tra và bấm Go.
2. Trong Shrine, xử lý `Offer1.png` hoặc `OfferGems.png`.
3. Khi thấy `Offerfins.png`, tìm `Offer+.png`, bấm Plus hai lần rồi xác nhận.
4. Ảnh `Offerdone.png` hoặc `Offerdone1.png` là tín hiệu hoàn thành.

Offering đứng ngay trước Resource Gathering vì đều đưa bot về thành.
