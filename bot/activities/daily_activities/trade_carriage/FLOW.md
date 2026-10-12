# Flow: Trade Carriage

Nhiệm vụ Daily Activities "Dispatch Trade Carriages 1 time(s)" (ô tích **Trade Carriage** ở tab Daily Activities, ưu
tiên 301: nhiệm vụ cuối cùng trước nhận thưởng Activity). Ảnh / hằng số: [constants.py](constants.py), code:
[run.py](run.py). Phần chung (mở Quests → Activity, tìm dòng, bấm Go): [../OPEN_TASK.md](../OPEN_TASK.md).

```mermaid
flowchart TD
    A[Go -> ra thẳng màn Trade Carriage] --> B{Có hộp quà trên xe?}
    B -->|có| C[Bấm hộp quà nhận thưởng] --> B
    B -->|không| D[Bấm Dispatch -> bảng hàng hoá]
    D -->|không hiện bảng| X[Hết lượt hôm nay: báo xong]
    D --> E{Còn dòng First Refresh Free?}
    E -->|có| F[Bấm Refresh Goods]
    F --> G{Hiện popup Refresh anyway?}
    G -->|có: xe đã cam| H[Back, giữ hàng cũ]
    G -->|không| I[Hàng đã đổi]
    E -->|không| J
    H --> J[Bấm Select Formation]
    I --> J
    J --> K["Bấm tab My Carriage đóng bảng"]
    K -->|chưa đủ 4 lần| B
    K -->|đủ 4 lần| Z[Báo xong hôm nay, Back về thành]
```

- Mỗi ngày game cho 4 lượt ("Transports Left Today"); bot Dispatch tối đa `DISPATCH_MAX` = 4 lần.
- Chỉ bấm Refresh Goods khi còn chữ "First Refresh Free" (lượt free); hết free thì không bấm (tránh tốn vật phẩm).
- Ảnh mẫu cắt từ ảnh chụp giả lập 396x704 (2026-10-13), thư mục `Images/DailyActivites/ActivitiesTradeCarriage/`.
