# Flow: Resource Gathering

Nhiệm vụ Daily Activities. Ảnh / action: [constants.py](constants.py), handler: [run.py](run.py).
Phần dùng chung (mở Quests → Activity, tìm dòng, bấm Go, state machine `run_task`): [../FLOW.md](../FLOW.md).

1. Chạy ngay sau Offering.
2. Tìm hàng `GatherCityCurrent.png`, bấm Go nếu còn.
3. Trong thành, tìm `HandCurrent.png` và bấm bàn tay để thu các tài nguyên sẵn
   sàng.
4. Mở lại Quests → Activity.
5. Xác nhận từ đúng hàng task: không còn Go thì hoàn thành.

Resource Gathering đứng ngay sau Offering vì đều đưa bot về thành.
