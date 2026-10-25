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
7. Worker chạy vòng lặp nhiệm vụ `_run_tasks()` (mục 3).

Server ban đầu lấy từ `settings["Initialization"]["server"]`. Nếu chưa có, `_ensure_server()` thử đọc trong game và cập nhật đăng ký với BossBoard khi đọc được. Server đã có sẽ không được đọc lại trong lượt chạy.

## 3. Vòng lặp nhiệm vụ: `_run_tasks()`

Worker chạy theo **một danh sách nhiệm vụ** và chỉ làm ba việc: lấy nhiệm vụ trong danh sách, kiểm tra nó **đã xong chưa** (đọc
DB), chưa xong thì chạy, xong rồi thì bỏ qua. **Worker không ghi kết quả nhiệm vụ vào DB**: mỗi nhiệm vụ trong `bot/activities`
tự lưu ngay chỗ biết kết quả: xong thì `mark_daily_done(<key>)` (hoặc các dấu mục tiêu `<key>_reached_N`), lỗi thật thì
`<key>_error` + một dòng History (`result.py` `save_errors`), việc theo giờ thì lưu giờ vừa làm (`<key>_tried`). Bị ngắt (Stop,
hết 120 giây, boss, bubble) không phải lỗi, không lưu gì.

Mọi nhiệm vụ nằm trong bảng [priority.py](priority.py): mỗi dòng có `key`, `priority`, `must_finish?`, `once?`, `group?` và
`run`: một hàm trơn `run(ctx, cấu hình tab)` hoặc một dict `{run, enabled, done, every}` do code của nhiệm vụ dựng sẵn (VD
`daily_job(...)`, `event_job(...)` cuối `run.py` / `common.py` của nhóm). `saves: True` = hàm tự lưu key của dòng khi xong.
Dòng không có `run` (Bubble, Join Monster War, `gift_*`, việc chưa làm) không phải nhiệm vụ của danh sách. [tasks.py](tasks.py) ghép
các dòng thành `Task`: `enabled` (đã tích ở tab cấu hình chưa), `done` (hôm nay đã xong chưa, đọc `daily_done`), `due` (chỉ việc
theo giờ: so giờ `<key>_tried` trong DB với số giờ trên tab) và `run`.

```mermaid
flowchart TD
    S[Start: tasks.build_tasks - việc đã tích, xếp theo ưu tiên] --> L{Stop?}
    L -->|Có| Z[Kết thúc]
    L -->|Không| B[Join Boss 1 lượt nếu có chọn]
    B --> R{Qua mốc reset server?}
    R -->|Có| N[Đưa lại mọi nhiệm vụ vào danh sách, trừ once đã xong]
    R -->|Không| F
    N --> F[Bỏ nhiệm vụ đã xong hôm nay]
    F --> D{Việc theo giờ nào tới giờ?}
    D -->|Có| T[Chạy việc theo giờ đó]
    D -->|Không| E{Danh sách rỗng?}
    E -->|Có| W[Nghỉ IDLE_WAIT giây] --> L
    E -->|Không| T2[Lấy nhiệm vụ đầu danh sách, chạy]
    T --> X
    T2 --> X{Xong chưa?}
    X -->|Xong| L
    X -->|Chưa| M[Chuyển xuống cuối danh sách; việc theo giờ thì chờ giờ kế tiếp] --> L
```

- **Mỗi vòng có Join Boss: 1 lượt Join Boss rồi đúng 1 nhiệm vụ**, tối đa `OTHERS_WINDOW` = 120 giây cho **từng** nhiệm vụ. Bị
  ngắt (hết 120 giây, có boss mới) thì giữ nguyên vị trí: sau Join Boss làm tiếp chính nhiệm vụ đó (chỉ nhiệm vụ chạy hết một
  lượt mà chưa xong mới xuống cuối danh sách).
- **Xong hay chưa** do `Task.done` quyết định (đọc daily_done). Nhiệm vụ không có dấu trong DB (`done` = None: Alliance Capacity,
  Black Market) coi là xong hôm nay khi đã chạy hết một lượt.
- **Sang ngày mới** (qua mốc reset server, chọn ở màn Home, mặc định 14:00) thì đưa lại mọi nhiệm vụ vào danh sách; nhiệm vụ
  `once` (Black Market) đã chạy xong thì không đưa lại, chỉ chạy lại khi Stop rồi Start.
- **Đúng giờ reset thì tắt game bật lại**: `Guards` hẹn `ctx` ngắt (`ResetDue`) đúng mốc reset kế tiếp, kể cả khi đang chạy nhiệm vụ
  `must_finish` (Bubble / Auto Times Out thì bị hoãn, reset thì không). Ngắt xong thì `am force-stop` game một lần cho mỗi mốc
  (`restart_for_reset`), rồi làm lại từ đầu việc đang dở. Vừa Start thì không đóng game.
- **Việc theo giờ** (Crazy Eggs, Alliance Donation / Help): làm xong thì lưu giờ đã làm vào DB (`daily_done`). Mỗi vòng lặp chỉ
  so giờ đó với ô chọn giờ ở tab (`Task.due`): đã qua N giờ thì làm ngay, trước các việc trong danh sách; chưa tới thì thôi.
- **Tối đa 6 lần mỗi ngày** (`MAX_ATTEMPTS`): một nhiệm vụ chạy hết một lượt mà vẫn chưa xong thì tính một lần thử; quá 6
  lần thì bỏ khỏi danh sách tới ngày mới. Bị ngắt giữa chừng (hết 120 giây, có boss) không tính là một lần thử.
- **Cả danh sách đều chưa xong** (hoặc danh sách rỗng): nghỉ `IDLE_WAIT` = 5 giây rồi xét lại, không chạy liên tục. Thread vẫn
  sống tới khi Stop.
- **Gift Claims** là bốn tail task của nhóm Daily Activities, lần lượt có
  priority `4 / 3 / 2 / 1`: Event Center, Revelry Carnival, Valuable Event,
  Super Value Return. Chúng
  chạy sau `daily_rewards`, không `must_finish`; khi có Join Boss thì bị ngắt ở
  120 giây/có boss mới, sau đó chạy lại từ các key DB chưa DONE.
- **Nhiệm vụ `must_finish`** (priority.py): đã bắt đầu thì chạy tới xong; Bubble / Auto Times Out / boss mới / 120 giây không
  ngắt (chỉ Stop); xong rồi mới tới Bubble, Auto Times Out và Join Boss. Gift
  Claims là ngoại lệ có chủ ý để xen kẽ lại Join Boss sau mỗi 120 giây.
- **Không chọn Join Boss: không có luật 120 giây** (không deadline, không ngắt bởi boss mới).
- **Không tích Bubble: không có luật Bubble** (`BubbleGuard.ensure` không làm gì, không hẹn `BubbleDue`).
- Join Boss trả về khác IDLE (dừng hẳn, ): không gọi lại Join Boss, vẫn chạy các nhiệm vụ.
- Bản đồ thế giới: worker không tự ép về thành (sau này có activity chạy ngoài thành). Chỉ `common.go_home` (activity gọi khi màn hình không
  nhận ra) bấm nút toà thành (`CityMap/toCity.png`, góc dưới phải) thay vì Back.
- Hết thể lực: Join Boss báo rảnh và đặt mốc "bây giờ + 20 phút" trên `ctx.stamina_until` — chỉ trong lượt chạy này, không lưu DB, đo bằng
  `time.monotonic()` nên đổi giờ Windows không ảnh hưởng; Stop / Start lại thì mốc mất (xem
  [stamina_wait.py](../activities/join_monster_war/stamina_wait.py)). Mỗi vòng worker hỏi mốc: chưa tới mốc thì chỉ làm nhiệm vụ
  (không gọi Join Boss, không giới hạn 120 giây, boss mới không ngắt); qua mốc thì Join Boss lại.
- Trước mỗi nhiệm vụ: `guards.call(None, ctx.check)` — lo bubble trước, rồi xét Stop / boss mới.

## 3b. Bubble (khiên): ưu tiên hơn mọi activity

Bubble và Auto Times Out nằm trong [guards.py](guards.py) (`BubbleGuard`, `RestartGuard`, bọc bởi `Guards`), tách khỏi `BotWorker`. `BotWorker` chỉ gọi `guards.call(nhãn, hàm, ...)`, `guards.hold()` / `release()` (nhiệm vụ `must_finish`) và cung cấp hook UI (`bubble_found`, `bubble_disabled`, `activity_changed`).

Bật khi tích **Bubble** ở tab Initialization (`settings["Initialization"]["bubble"]`), loại dùng lấy từ ô select (`bubble_type`: 8h / 24h / 3d / 7d, mặc định 24h). Thao tác trong game là `keep_bubble()` ở [bot/common/bubble.py](bot/common/bubble.py), làm trong một lần vào game:

1. Màn hình chính: bấm icon buff (`Bubble/1.png`) để mở City Buff. Popup `exit` được đóng và nút `click` được bấm trước.
2. City Buff: dòng Truce Agreement có thanh thời gian thì OCR (font `Timer`). Còn hơn 2 tiếng thì thoát ra, không dùng. Không có thanh hoặc còn ít hơn thì bấm icon Truce.
3. Use Item: tìm tiêu đề dòng của loại đã chọn (4 dòng xếp 8h, 24h, 3d, 7d), bấm nút cùng dòng (Use hoặc giá kim cương).
4. Popup Confirm (thay bubble đang có, dùng, mua): bấm Confirm, bình thường tối đa 2 lần.
5. Về Use Item: đọc `Remaining Time` mới, BACK 2 lần về màn hình chính. Đọc 3 lần không ra thời gian mới thì tính theo loại vừa dùng.

```mermaid
flowchart TD
    A[Trước mỗi activity / Get Server] --> B{Tích Bubble và tới lượt kiểm tra?}
    B -->|Không| R[Chạy activity]
    B -->|Có| C[Tắt tạm deadline 120s và ngắt boss]
    C --> D[Đọc thời gian bubble còn lại]
    D --> E{Còn <= 2 tiếng hoặc không có bubble?}
    E -->|Có| F[Dùng bubble loại đã chọn, đọc lại thời gian]
    E -->|Không| G
    F --> G[Khôi phục deadline / ngắt boss; hẹn lần sau]
    G --> R
    R -->|ctx.check: tới hẹn -> BubbleDue| C
```

- Hẹn lần sau: bubble còn hơn 2 tiếng thì hẹn đúng lúc còn 2 tiếng; đọc hoặc dùng không được thì 5 phút sau thử lại (`BUBBLE_RETRY`), không đọc lại trước từng activity.
- Tới hẹn, `ctx.check()` ném `BubbleDue` ở bất kỳ activity nào, kể cả Join Boss. Thứ tự ưu tiên: Stop → Bubble → thông báo boss → timeout.
- `Guards.call()` ([guards.py](guards.py)) bắt `BubbleDue`, xử lý bubble rồi gọi lại activity từ đầu (giống khi timeout). Bước bubble không bị deadline 120 giây hoặc thông báo boss cắt ngang.
- Mỗi lần biết thời gian, worker phát `bubble_found(serial, giây)`; main lưu thời điểm bubble hết vào cột `devices.bubble_until` và UI đếm ngược ở tab Initialization (ẩn khi không có bubble).
- Lần chạy sau, worker đọc `bubble_until` từ DB: còn hơn 2 tiếng thì không vào game kiểm tra, chỉ hẹn lúc còn 2 tiếng. `bubble_until` không bị chép qua Apply ALL.
- OCR thời gian (font `Timer`): dưới 1 ngày game hiện `06:55:22`, từ 1 ngày trở lên hiện `2d 23:38`.
- Không đủ kim cương (khi có ảnh `Bubble/noGems.png`): bỏ tích Bubble và không thử lại.

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

Ngắt boss chỉ được bật trong lúc chạy một nhiệm vụ của `_run_task()` (khi có Join Boss). Nó không ngắt chính Join Boss.

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

File [tests/worker/test_boss_notifications.py](../../tests/worker/test_boss_notifications.py) kiểm tra:

- Lọc đúng server, không báo lại worker nguồn, chống trùng, hết hạn và hủy đăng ký.
- Chỉ ngắt activity phụ; Stop được ưu tiên.
- Thông báo đưa worker về Join Boss, giữ activity đang dở để gọi lại và dọn deadline đúng cách.

Chạy trên Windows từ thư mục dự án:

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```

Các kiểm thử này mô phỏng điều phối trong code, không xác nhận thao tác Join thực tế trên giả lập.
