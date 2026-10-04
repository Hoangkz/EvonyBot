# Flow: Gold Levy

Nhiệm vụ Daily Activities. Ảnh / action: [constants.py](constants.py), handler: [run.py](run.py).
Phần dùng chung (mở Quests → Activity, tìm dòng, bấm Go, state machine `run_task`): [../FLOW.md](../FLOW.md).

1. Tìm `LevyGoldActivityCurrent.png` hoặc `LevyGoldActivity1.png`, bấm Go.
2. Về thành, bấm giữa (Thành chính) → menu tròn → `Levy.png`: bấm Levy.
3. Popup Levy: `FreeLevyAll.png` (nút vàng) → bấm → đánh dấu xong hôm nay, Back đóng popup.
   `FreeLevyAllDone.png` (nút xám, hết lượt free) → cũng đánh dấu xong. Không dùng Gems Levy.
4. Ảnh `Levy1.png`, `GemsLevyTimes.png` của luồng C# cũ (nhập 5 lượt Gems Levy) không còn dùng.
5. `LevyGoldFinish.png` hoặc `LevyGoldFinish1.png` báo hoàn thành.
