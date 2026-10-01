# Flow hiện tại của EvonyBot

Tài liệu mô tả cách code hiện tại chạy activity và thông báo boss giữa các giả lập cùng server.

## 1. Các thành phần

| Thành phần | Vai trò |
| --- | --- |
| [BotManager](bot/worker/manager.py) | Quản lý worker theo serial ADB, chuyển tiếp signal cho UI, sở hữu một BossBoard dùng chung. |
| [BotWorker](bot/worker/bot_worker.py) | Một QThread cho mỗi giả lập được bật bot; điều phối các activity. |
| [BotContext](bot/context/bot_context.py) | Cung cấp thao tác thiết bị, chụp màn hình, settings và cơ chế kiểm tra ngắt. |
| [FlowMixin](bot/context/flow.py) | Kiểm tra Stop, thông báo boss, timeout; cung cấp sleep có thể ngắt. |
| [BossBoard](bot/worker/boss_board.py) | Lưu dấu các boss đã báo và bật cờ thông báo cho worker cùng server; bảo vệ dữ liệu bằng Lock. |
| [Join Monster War](bot/activities/join_monster_war/run.py) | Tìm rally để Join, báo boss cho BossBoard, trả về IDLE khi rảnh nếu được yêu cầu. |
| [ACTIVITIES](bot/activities/__init__.py) | Ánh xạ tên activity sang hàm thực thi. |

Không có luồng giám sát riêng. Các worker gọi trực tiếp BossBoard dùng chung; mỗi worker có một threading.Event để nhận thông báo boss.

```mermaid
flowchart TD
    M[BotManager] --> W1[Worker giả lập 1 - QThread]
    M --> W2[Worker giả lập 2 - QThread]
    M --> W3[Worker giả lập 3 - QThread]
    M --> B[BossBoard dùng chung]
    W1 <--> B
    W2 <--> B
    W3 <--> B
```

Các giả lập chạy đồng thời. Trong mỗi worker, các activity chạy tuần tự trên cùng luồng; `_run_activity()` không tạo luồng mới.

## 2. Bắt đầu chạy một giả lập

1. UI gọi `BotManager.start(serial, activities, settings)`.
2. Manager từ chối nếu serial đã có worker hoặc danh sách activity rỗng.
3. Manager tạo BotWorker, truyền BossBoard dùng chung, nối signal và lưu vào `_workers`.
4. `worker.start()` khởi động luồng và gọi `BotWorker.run()`.
5. Worker báo trạng thái Running, lấy thiết bị ADB và tạo BotContext.
6. Worker gắn settings, callback `report_boss` và đăng ký nhận thông báo nếu đã chọn Join Monster War.
7. Worker chọn chế độ điều phối dựa trên danh sách activity.

Server ban đầu lấy từ `settings["Initialization"]["server"]`. Nếu chưa có, `_ensure_server()` thử đọc trong game và cập nhật đăng ký với BossBoard khi đọc được. Server đã có sẽ không được đọc lại trong lượt chạy.

## 3. Chọn chế độ điều phối

```mermaid
flowchart TD
    A[BotWorker.run] --> B{Có Join Boss và activity phụ?}
    B -->|Không| C[_run_once: chạy theo thứ tự danh sách]
    B -->|Có| D[_boss_priority: ưu tiên Join Boss]
    C --> E[Kết thúc hoặc Stop hoặc lỗi]
    D --> E
    E --> F[Hủy đăng ký BossBoard và cập nhật UI]
```

### Chạy tuần tự: `_run_once()`

Áp dụng khi chỉ chọn Join Boss hoặc không chọn Join Boss:

1. Kiểm tra Stop trước mỗi activity.
2. Đảm bảo đã thử lấy giờ reset và server, theo thứ tự này. Nếu đã có thì bỏ qua việc đọc.
3. Báo activity hiện tại cho UI.
4. `_run_activity()` lấy hàm từ ACTIVITIES và gọi `run(ctx, tab_settings)`.
5. Hàm trả về thì chuyển sang activity tiếp theo.

Mỗi activity được gọi một lần, nhưng có thể tự lặp bên trong. Chỉ chọn Join Boss thì activity này thường tiếp tục kiểm tra boss cho tới khi tự dừng hoặc người dùng Stop.

Tên activity không tồn tại sẽ được ghi log, chờ 1 giây qua `ctx.sleep()` rồi bỏ qua.

### Ưu tiên boss: `_boss_priority()`

`pending` là danh sách activity phụ chưa hoàn thành, giữ nguyên thứ tự ban đầu.

```mermaid
flowchart TD
    A{Còn pending?} -->|Không| B[Chạy Join Boss với settings gốc]
    B --> Z[Kết thúc khi Join Boss trả về]
    A -->|Có| C[Đảm bảo giờ reset và server]
    C --> D[Xóa cờ boss cũ; chạy Join Boss với exit_when_idle=True]
    D --> E{Trả về IDLE?}
    E -->|Không| F[Chạy nốt pending bằng _run_once]
    F --> Z
    E -->|Có| G[Đặt deadline 120 giây; bật ngắt bởi thông báo boss]
    G --> H[Kiểm tra ngắt rồi chạy pending đầu tiên]
    H -->|Trả về bình thường| I[Xóa activity khỏi pending]
    I --> J{Còn pending?}
    J -->|Có| H
    J -->|Không| K[Tắt ngắt boss; gỡ deadline]
    H -->|BossAvailable hoặc TimedOut| K
    K --> A
```

- 120 giây là ngân sách chung cho cả nhóm activity phụ trong một lượt, không phải cho từng activity.
- Khi timeout hoặc có thông báo boss, activity đang dở vẫn nằm đầu pending.
- Lượt sau gọi lại từ đầu hàm activity; worker không lưu dòng đang chạy hoặc tiến độ nội bộ.
- Activity trả về bình thường được xem là hoàn thành và bị loại khỏi pending.
- Nếu Join Boss trả về khác IDLE, worker chạy nốt pending bằng `_run_once()` rồi kết thúc. Trong nhánh này không còn deadline 120 giây hoặc ngắt để quay lại boss.
- Khi pending hết, Join Boss chạy với settings gốc; cơ chế nhường activity phụ kết thúc.

## 3b. Bubble (khiên): ưu tiên hơn mọi activity

Bật khi tích **Bubble** ở tab Initialization (`settings["Initialization"]["bubble"]`), loại dùng lấy từ ô select (`bubble_type`: 8h / 24h / 3d / 7d, mặc định 24h). Thao tác trong game là `keep_bubble()` ở [bot/common/bubble.py](bot/common/bubble.py), làm trong một lần vào game:

1. Màn hình chính: bấm icon buff (`Bubble/1.png`) để mở City Buff. Popup `exit` được đóng và nút `click` được bấm trước.
2. City Buff: dòng Truce Agreement có thanh thời gian thì OCR (font `Timer`). Còn hơn 1 tiếng thì thoát ra, không dùng. Không có thanh hoặc còn ít hơn thì bấm icon Truce.
3. Use Item: tìm tiêu đề dòng của loại đã chọn (4 dòng xếp 8h, 24h, 3d, 7d), bấm nút cùng dòng (Use hoặc giá kim cương).
4. Popup Confirm (thay bubble đang có, dùng, mua): bấm Confirm, bình thường tối đa 2 lần.
5. Về Use Item: đọc `Remaining Time` mới, BACK 2 lần về màn hình chính. Đọc 3 lần không ra thời gian mới thì tính theo loại vừa dùng.

```mermaid
flowchart TD
    A[Trước mỗi activity / Get Server / Get Server Time] --> B{Tích Bubble và tới lượt kiểm tra?}
    B -->|Không| R[Chạy activity]
    B -->|Có| C[Tắt tạm deadline 120s và ngắt boss]
    C --> D[Đọc thời gian bubble còn lại]
    D --> E{Còn <= 1 tiếng hoặc không có bubble?}
    E -->|Có| F[Dùng bubble loại đã chọn, đọc lại thời gian]
    E -->|Không| G
    F --> G[Khôi phục deadline / ngắt boss; hẹn lần sau]
    G --> R
    R -->|ctx.check: tới hẹn -> BubbleDue| C
```

- Hẹn lần sau: bubble còn hơn 1 tiếng thì hẹn đúng lúc còn 1 tiếng; đọc hoặc dùng không được thì 5 phút sau thử lại (`BUBBLE_RETRY`), không đọc lại trước từng activity.
- Tới hẹn, `ctx.check()` ném `BubbleDue` ở bất kỳ activity nào, kể cả Join Boss. Thứ tự ưu tiên: Stop → Bubble → thông báo boss → timeout.
- `_with_bubble()` bắt `BubbleDue`, xử lý bubble rồi gọi lại activity từ đầu (giống khi timeout). Bước bubble không bị deadline 120 giây hoặc thông báo boss cắt ngang.
- Mỗi lần biết thời gian, worker phát `bubble_found(serial, giây)`; UI đếm ngược ở tab Initialization và ẩn khi không có bubble.

## 4. Khi nào Join Boss phát thông báo?

Trong `_Boss._join()`:

1. Tìm nút Join trong vùng màn hình hợp lệ.
2. Loại các nút đã xử lý trong màn hình hiện tại.
3. Nếu có template hỗ trợ, OCR tọa độ boss; bỏ qua tọa độ còn trong `BossMemory` của giả lập (đã tham gia hoặc đã bỏ qua trong 6 phút gần nhất).
4. OCR tên boss; bỏ qua boss không được tích ở tab Join Monster War (hoặc không nhận ra tên) và nút có chữ đỏ.
5. Gọi `bot.report_boss(coords)` ngay trước khi tap Join.
6. Tap Join, ghi nhớ boss đã xử lý và tiếp tục flow tham gia rally.

Thông báo được phát trước khi xác nhận tham gia thành công. Nó phản ánh một ứng viên Join mà worker phát hiện, không đảm bảo mọi tài khoản đều tham gia được. Boss bị worker nguồn bỏ qua ở các bước lọc trên sẽ không được báo.

## 5. Dữ liệu dùng chung và lọc server

BossBoard hiện dùng dictionary trong bộ nhớ:

```text
_bosses[(server, (x, y))] = thời điểm hết hạn
_listeners[serial] = (server, event của worker)
```

Khi `publish(serial, server, coords)` được gọi:

1. Chuyển server thành chuỗi và bỏ khoảng trắng hai đầu.
2. Nếu server rỗng thì không phát thông báo.
3. Trong Lock, dọn bản ghi hết hạn.
4. Nếu khóa boss còn tồn tại thì bỏ qua thông báo trùng.
5. Lưu bản ghi mới và bật event cho listener cùng server, ngoại trừ worker nguồn.

| Trường hợp | Khóa chống trùng | Thời hạn |
| --- | --- | --- |
| Đọc được tọa độ | `(server, (x, y))` | 120 giây mặc định |
| Không đọc được tọa độ | `(server, None)` | 10 giây |

Thời hạn này chỉ dùng chống thông báo trùng, không phải thời gian còn lại của rally trong game. Thông báo trùng không gia hạn bản ghi. Bản ghi hết hạn được dọn khi có lần publish tiếp theo.

Các worker nhận thông báo phải bật Join Monster War. Việc so khớp chỉ dựa trên chuỗi server sau khi bỏ khoảng trắng; không lọc liên minh. Worker mới đăng ký không được phát lại các thông báo cũ.

BossBoard không chuyển tọa độ cho worker nhận để chọn đúng rally. Event chỉ yêu cầu worker chuyển sang Join Boss; worker đó tự quét danh sách rally trên màn hình của mình. Nhiều thông báo có thể gộp thành một cờ đang bật.

## 6. Ví dụ hai giả lập cùng server

```mermaid
sequenceDiagram
    participant W1 as Worker 1 - Server 100
    participant B as BossBoard
    participant W2 as Worker 2 - Server 100
    participant W3 as Worker 3 - Server 200
    Note over W1: Đang chạy activity phụ
    W2->>W2: Phát hiện ứng viên Join mới
    W2->>B: publish(serial, server=100, coords)
    B->>B: Kiểm tra trùng và lưu bản ghi
    B->>W1: Bật _boss_event
    Note over W3: Khác server nên không nhận thông báo
    W1->>W1: ctx.check() ném BossAvailable
    W1->>W1: Giữ pending, tắt ngắt boss, gỡ deadline
    W1->>W1: Xóa cờ và chạy Join Boss
    W2->>W2: Tiếp tục tap Join
```

Nếu một thông báo đến trong lúc worker đang Join Boss, nó không ngắt Join Boss. Cờ có thể khiến worker quay lại kiểm tra boss ngay khi chuẩn bị chạy activity phụ. Cờ được xóa trước mỗi lượt Join Boss trong vòng ưu tiên.

## 7. Ý nghĩa của “chuyển ngay”

`BotContext.check()` kiểm tra theo thứ tự:

1. Stop → ném `StopRequested`.
2. Đang cho phép ngắt boss và event đã bật → ném `BossAvailable`.
3. Đã hết deadline → ném `TimedOut`.

Ngắt boss chỉ được bật trong cửa sổ chạy activity phụ của `_boss_priority()`. Nó không ngắt chính Join Boss.

Worker phản hồi tại lần check kế tiếp. `ctx.sleep()` kiểm tra tối đa mỗi khoảng 0,2 giây trong vòng chờ; lời gọi ADB hoặc thao tác chặn đang chạy phải kết thúc trước khi worker có thể check tiếp. Không có cơ chế cưỡng chế dừng thread.

Sau ngắt, worker gọi flow Join Boss hiện có từ màn hình đang đứng; không có bước phục hồi màn hình riêng trong scheduler. Join Boss tự xử lý màn hình qua nhận diện, Back và fallback `go_home()`.

Nếu tất cả worker đều đang làm activity phụ, không có worker quét boss liên tục để phát thông báo. Deadline 120 giây vẫn giúp các worker quay lại kiểm tra.

## 8. Stop, lỗi và kết thúc

1. `BotManager.stop(serial)` đặt cờ Stop của worker và báo UI trạng thái Stopping.
2. Activity gặp `ctx.check()` sẽ ném StopRequested; Stop được ưu tiên hơn thông báo boss và timeout.
3. Khi thoát cửa sổ activity phụ, khối finally luôn tắt ngắt boss và gỡ deadline.
4. `BotWorker.run()` bắt BotInterrupted và kết thúc với Stopped; lỗi khác được ghi log và trả trạng thái Error kèm nội dung lỗi.
5. Khối finally của worker hủy đăng ký BossBoard, đặt activity hiển thị thành `"None"` và phát trạng thái cuối.
6. Khi QThread phát finished, manager xóa worker khỏi `_workers`, gọi deleteLater và báo `running_changed(serial, False)`.

## 9. Kiểm thử hiện có

File [tests/test_boss_notifications.py](tests/test_boss_notifications.py) kiểm tra:

- Lọc đúng server, không báo lại worker nguồn, chống trùng, hết hạn và hủy đăng ký.
- Chỉ ngắt activity phụ; Stop được ưu tiên.
- Thông báo đưa worker về Join Boss, giữ activity đang dở để gọi lại và dọn deadline đúng cách.

Chạy trên Windows từ thư mục dự án:

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```

Các kiểm thử này mô phỏng điều phối trong code, không xác nhận thao tác Join thực tế trên giả lập.
