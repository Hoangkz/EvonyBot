# Flow của Daily Activities

> Luồng mới (mở nhiệm vụ / bấm Go cho cả 2 phiên bản giao diện, sau Go giống Event): xem
> [OPEN_TASK.md](OPEN_TASK.md). Tài liệu dưới đây mô tả luồng cũ port từ C# (`common.run_task`).

Tài liệu này mô tả **code Python hiện tại** trong [run.py](run.py) (thứ tự nhiệm vụ),
[common.py](common.py) (vòng lặp chung `run_task`), các thư mục nhiệm vụ (mỗi nhiệm vụ một thư
mục giống activity Event: `constants.py` ảnh + `KEY` trong `bot/worker/priority.json`, `run.py`
handler + `TASK`), [general.py](general.py) và giao diện cấu hình tại
[daily_activities_tab.py](../../../ui/tabs/daily_activities_tab.py). Module được
chuyển từ `DailyActivities1234.cs`, nhưng một số luồng đã được sửa cho giao
diện Evony hiện tại.

Daily Activities không đọc dữ liệu trực tiếp từ game. Mỗi bước đều theo chu
trình: chụp màn hình → so khớp ảnh → thực hiện action → chụp lại và xác nhận.

## 1. Cách khởi chạy từ Evony Control App

1. Trong tab **Initialization**, chọn activity **Daily Activities**.
2. Trong tab **Daily Activities**, tích các nhiệm vụ muốn chạy.
3. Quay lại **Initialization** và bấm **Start**.
4. `BotWorker` gọi `daily_activities.run(bot, settings)`.

Số server chỉ được đọc khi chạy Join Monster War. Chạy riêng Daily Activities
không mở Settings để tìm server. Giờ reset server vẫn được dùng để quyết định
một nhiệm vụ đã hoàn thành trong ngày hay chưa; nếu chưa biết giờ reset thì
code dùng mốc 0 giờ máy làm fallback.

## 2. Cấu hình và nhiệm vụ được hỗ trợ

### General

| Cấu hình | Hành vi |
| --- | --- |
| `stamina_quantity` | UI: một ô chọn "Buy Stamina" 0, 10, 20 hoặc 30; 0 = không mua (mặc định). |
| `buy_stamina` | Tự suy ra từ UI (`stamina_quantity > 0`); giữ để tương thích cấu hình cũ. |
| `buy_all_hammers` | Checkbox "Buy Hammer": mua toàn bộ búa tìm thấy trong mục Special. |

General chạy trước danh sách nhiệm vụ Daily. Kết quả được lưu độc lập bằng
hai khóa `General: Buy Stamina` và `General: Buy All Hammers`.

### Selection Daily

Các nhiệm vụ được chạy theo đúng thứ tự sau, không theo thứ tự người dùng tích:

1. Monster Killing
2. Resource Collecting
3. Offering
4. Resource Gathering
5. Resource Tax
6. Gold Levy
7. Troop Training
8. Troop Heading (hiển thị là Troop Healing)
9. Trap Buiding (hiển thị là Trap Building)
10. Alliance Donation
11. Black Market
12. General Enhancing
13. Wheel of Fortune
14. Patrol
15. Material Composing

Các mục trong nhóm **Unavailable Daily** bị disable vì chưa có flow Python.

## 3. Điều phối tổng thể

```mermaid
flowchart TD
    A[run settings] --> B[Chạy General]
    B --> C{Có task được chọn?}
    C -->|Không| Z[Kết thúc]
    C -->|Có| D[Lặp tối đa 5 pass]
    D --> E[Duyệt TASKS theo thứ tự cố định]
    E --> F{Task đã có daily_done sau reset?}
    F -->|Có| E
    F -->|Không| G[common.run_task]
    G --> H{Xác nhận hoàn thành?}
    H -->|Có| I[mark_daily_done]
    H -->|Chưa| E
    I --> E
    E -->|Hết pass| J{Còn pass?}
    J -->|Có| D
    J -->|Không| K[Nhận Claim All và mọi rương đang mở]
    K --> L{Tất cả task đã hoàn thành?}
    L -->|Có| M[Đánh dấu Activity Rewards]
    L -->|Không| Z
    M --> Z
```

- Mỗi task chỉ được lưu `daily_done` khi `common.run_task()` trả `True`.
- `daily_done` lưu timestamp trong database. Timestamp chỉ còn hiệu lực nếu
  nằm sau mốc reset server gần nhất.
- Module chạy tối đa 5 pass để có thể quay lại task chưa hoàn thành ở pass
  trước.
- Stop, timeout và thông báo boss được kiểm tra qua `bot.check()`.

## 4. State machine dùng chung cho một task

`common.run_task()` tạo danh sách template theo thứ tự ưu tiên rồi lặp liên tục.

| Action | Ý nghĩa |
| --- | --- |
| `DONE` | Thấy ảnh Finish của task; trả `True`. Không dùng cho những task có ảnh Finish dễ khớp nhầm. |
| `OPEN` | Tìm đúng hàng task và kiểm tra nút Go trong vùng 100 px của chính hàng đó. |
| `TAP` | Bấm template vừa nhận diện. |
| `BACK` | Bấm Back cho popup/ảnh thoát đã biết. |
| `SCROLL` | Cuộn danh sách Activity. Nếu vị trí không đổi nhiều lần, quay về đầu danh sách. |
| Không nhận diện | Chờ 1 giây rồi quét lại; không bấm Back mù vì có thể mở hộp Quit. |

### Kiểm tra nút Go theo đúng hàng

`common.open_task_row()` nhận góc trên trái của **nhãn task**, crop toàn bộ hàng cao
100 px rồi chỉ tìm `Go.png` trong vùng đó.

- Có Go và `open_when_available=True`: bấm Go, chờ chuyển màn hình.
- Có Go và `open_when_available=False`: trả trạng thái chưa hoàn thành nhưng
  không bấm Go.
- Không có Go: trả `ROW_COMPLETE`.
- Nhãn ở quá thấp (`y > 500`): cuộn nhẹ trước, chưa kết luận.

Việc một ảnh khác biến mất hoặc một nhiệm vụ trung gian hoàn thành **không tự
động chứng minh** task chính đã hoàn thành.

### Mở Quests → Activity

`common.open_daily_activity()` nhận diện các biến thể của nút Quests/Daily:

- `QuestButtonDaily.png`: ảnh người dùng cung cấp.
- `QuestButtonCurrent.png`: biến thể ngoài thành.
- `QuestButtonCity.png`: biến thể trong thành.

Sau đó bot bấm tab Activity và xác nhận bằng `Click_ActivitiesLight.png`. Khi
drawer tìm quái che nút Quests, bot dùng `BackToTerritoryCurrent.png` để về
thành; không dùng Android Back vì Back mở hộp Quit trên giao diện hiện tại.

## 5. Flow từng nhiệm vụ

Mỗi nhiệm vụ có file `FLOW.md` riêng trong thư mục của nó (thứ tự chạy ở [run.py](run.py)):

| Nhiệm vụ | Flow |
| --- | --- |
| Monster Killing | [monster_killing/FLOW.md](monster_killing/FLOW.md) |
| Resource Collecting | [resource_collecting/FLOW.md](resource_collecting/FLOW.md) |
| Offering | [offering/FLOW.md](offering/FLOW.md) |
| Resource Gathering | [resource_gathering/FLOW.md](resource_gathering/FLOW.md) |
| Resource Tax | [resource_tax/FLOW.md](resource_tax/FLOW.md) |
| Gold Levy | [gold_levy/FLOW.md](gold_levy/FLOW.md) |
| Troop Training | [troop_training/FLOW.md](troop_training/FLOW.md) |
| Troop Healing | [troop_healing/FLOW.md](troop_healing/FLOW.md) |
| Trap Building | [trap_building/FLOW.md](trap_building/FLOW.md) |
| Alliance Donation | [alliance_donation/FLOW.md](alliance_donation/FLOW.md) |
| Black Market | [black_market/FLOW.md](black_market/FLOW.md) |
| General Enhancing | [general_enhancing/FLOW.md](general_enhancing/FLOW.md) |
| Wheel of Fortune | [wheel_of_fortune/FLOW.md](wheel_of_fortune/FLOW.md) |
| Patrol | [patrol/FLOW.md](patrol/FLOW.md) |
| Material Composing | [material_composing/FLOW.md](material_composing/FLOW.md) |

## 6. General: mua thể lực và mua búa

### Buy Stamina

1. Mở Features (`chucnang.png`).
2. Vào Items → War.
3. Tìm Stamina và bấm Buy.
4. Bấm Plus `quantity - 1` lần; số lượng mặc định là 10.
5. Bấm nút mua và chỉ khi flow trả `True` mới đánh dấu đã mua hôm nay.

### Buy All Hammers

1. Mở Features → Items → Special.
2. Tìm offer búa (`bua.png`).
3. Bấm bên trái nút Plus để chọn số lượng tối đa.
4. Xác nhận mua.
5. Nếu kiểm tra Special quá năm lần mà không thấy búa, trả `False`.

Mỗi flow General có giới hạn `MAX_STEPS = 100`; quá giới hạn sẽ log và dừng,
không đánh dấu hoàn thành.

## 7. Nhận thưởng Activity

Sau các pass, nếu `Activity Rewards` chưa được ghi hoàn thành:

1. Đóng popup `CongratulationsCurrent.png` bằng Back.
2. Nếu có `Claim_All.png`, bấm Claim All trước để cộng điểm Activity.
3. Tìm mọi `OpenChestCurrent.png` trong riêng hàng rương.
4. Mỗi screenshot chỉ bấm một rương, xử lý popup rồi chụp lại; không dùng lại
   tọa độ cũ vì UI thay đổi sau mỗi lần nhận.
5. Tiếp tục tới khi không còn rương đang mở.
6. Chỉ ghi `Activity Rewards` vào database nếu tất cả task được chọn đã có
   `daily_done`.

## 8. Ảnh, vùng tìm kiếm và cache

- Ảnh nằm dưới `Images/DailyActivites/<folder task>/`.
- `find_first()` dùng cache vị trí riêng theo BotContext. Sau lần tìm thấy đầu,
  bot ưu tiên vùng nhỏ quanh vị trí cũ và vẫn có fallback toàn màn hình.
- Những ảnh nhãn hàng cần trả góc trên trái thay vì tâm để crop đúng 100 px.
- Các nút có nhiều giao diện giữ nhiều template: `*Current.png` cho client hiện
  tại và ảnh cũ làm fallback.
- Thứ tự template có ý nghĩa. Một ảnh Finish đặt trước action có thể kết thúc
  task sai nếu nó trùng với icon khác; Resource Collecting đã loại bỏ Finish vì
  lý do này.

## 9. Database và reset ngày

Các khóa hoàn thành được lưu trong trường `daily_done` của thiết bị:

```text
{
  "Monster Killing": "2026-10-03T18:00:00",
  "Resource Collecting": "2026-10-03T18:10:00",
  "General: Buy Stamina": "2026-10-03T18:15:00",
  "Activity Rewards": "2026-10-03T18:30:00"
}
```

Code không xóa bản ghi mỗi ngày. `done_today()` so timestamp với mốc reset gần
nhất; bản ghi cũ tự động không còn được coi là hoàn thành.

## 10. Kiểm thử và giới hạn xác nhận

Các test chính:

- [test_daily_activities.py](../../../tests/daily_activities/test_daily_activities.py): state
  machine, kiểm tra hàng/Go, Monster 2+3, Resource Collecting và nhận rương.
- [test_general.py](../../../tests/daily_activities/test_general.py): mua thể lực và
  búa.

Chạy unit test:

```powershell
.\venv\Scripts\python.exe -m unittest tests.daily_activities.test_daily_activities tests.daily_activities.test_general
```

Unit test xác nhận quyết định của code với màn hình/mocks đã biết; nó không tự
chứng minh toàn bộ luồng thật trên mọi tài khoản hoặc mọi phiên bản Evony. Với
thay đổi ảnh hay giao diện, cần chạy thật trên giả lập (`tests/real_run.py`, `poe test`)
trước khi kết luận flow đã đúng hoàn toàn.
