# Flow: Monster Killing

Nhiệm vụ Daily Activities. Ảnh / action: [constants.py](constants.py), handler: [run.py](run.py).
Phần dùng chung (mở Quests → Activity, tìm dòng, bấm Go, state machine `run_task`): [../FLOW.md](../FLOW.md).

Monster Killing có hai mốc Daily liên tiếp: đánh 2 lần, sau đó đánh thêm 3 lần.

```mermaid
flowchart TD
    A[Tìm hàng Attack Monsters 2 times] --> B{Hàng còn Go?}
    B -->|Có| C[Mở Find Monster]
    C --> D[Chọn tab Monster và Search]
    D --> E[Bấm Attack]
    E --> F[Gửi March]
    F --> G{Đã gửi đủ 2 march?}
    G -->|Chưa| C
    G -->|Đủ| H[Về Activity]
    H --> I[Hàng đầu không còn Go; claim để hiện hàng sau]
    I --> J[Đặt trạng thái deferred]
    J --> K[Làm 5 task khác; hoặc 4 nếu đã hết task khả dụng]
    K --> L[Tìm hàng Attack Monsters 3 times]
    L --> M[Đánh thêm 3 march]
    M --> N[Về Activity]
    N --> O{Hàng thứ hai còn Go?}
    O -->|Không| P[Hoàn thành]
    O -->|Có| L
```

Chi tiết thao tác:

- `FindMonster.png` mở giao diện tìm kiếm.
- `TapMonster.png` chọn tab Monster trước khi bấm Search.
- Giao diện mới dùng nút xanh `AttackButtonCurrent.png`; giao diện cũ giữ
  fallback `AttackMonster.png`.
- Màn March ưu tiên `FullTiersCurrent.png`. Nếu nút này chỉ điền đội hình mà
  chưa gửi, bot bấm `MarchButtonCurrent.png`.
- Chỉ tăng bộ đếm march khi ảnh `March.png` biến mất sau thao tác gửi.
- Nếu tìm quái chưa sẵn sàng ba lần, bot chờ 5 giây; không bấm Back.
- Sau march 2 và march 5, bot quay lại Activity để kiểm tra trạng thái.
