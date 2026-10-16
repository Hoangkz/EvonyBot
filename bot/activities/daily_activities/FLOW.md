# Flow của Daily Activities

Mở nhiệm vụ / bấm Go cho cả 2 phiên bản giao diện: xem [OPEN_TASK.md](OPEN_TASK.md). Mỗi nhiệm vụ là một thư mục
(`constants.py` ảnh + `run.py` có `after_go(bot)` và `TASK`), xếp vào bảng nhiệm vụ của worker ở
[bot/worker/priority.py](../../worker/priority.py); các luật chung (`daily_job`, `hourly_job`) nằm ở
[common.py](common.py). Cấu hình ở [daily_activities_tab.py](../../../ui/tabs/daily_activities_tab.py).

Daily Activities không đọc dữ liệu trực tiếp từ game. Mỗi bước theo chu trình: chụp màn hình → so khớp ảnh → thực hiện
action → chụp lại và xác nhận.

## 1. Cách khởi chạy

Tab **Daily Activities** tích các nhiệm vụ muốn chạy; worker lấy từng việc chưa làm có ưu tiên cao nhất (xem
[../../worker/FLOW.md](../../worker/FLOW.md)). Giờ reset server quyết định một nhiệm vụ đã xong trong ngày hay chưa; chưa biết
giờ reset thì dùng mốc 0 giờ máy.

## 2. Cấu hình và nhiệm vụ được hỗ trợ

### General

| Cấu hình | Hành vi |
| --- | --- |
| `stamina_quantity` | UI: một ô chọn "Buy Stamina" 0, 10, 20 hoặc 30; 0 = không mua (mặc định). |
| `buy_stamina` | Tự suy ra từ UI (`stamina_quantity > 0`); giữ để tương thích cấu hình cũ. |
| `buy_all_hammers` | Checkbox "Buy Hammer": mua toàn bộ búa tìm thấy trong mục Special. |

General chạy trước các nhiệm vụ Daily. Kết quả lưu độc lập bằng hai khóa `General: Buy Stamina` và `General: Buy All Hammers`.

### Nhiệm vụ Daily (theo thứ tự trong `priority.py`)

Offering, Resource Tax, Gold Levy, Troop Training, Troop Healing, Trap Building, Black Market, General Enhancing, Wheel of
Fortune, Patrol, Material Composing, Research technologies, Greet Champion, Trade Carriage. Alliance Donation / Alliance
Help là việc theo giờ (ô chọn giờ, không phải ô tích), chạy sau nhận thưởng.

## 3. Một nhiệm vụ chạy thế nào (`daily_job`)

1. `open_task_or_finish`: mở bảng Activity, tìm dòng / thẻ của nhiệm vụ, bấm Go (xem [OPEN_TASK.md](OPEN_TASK.md)). Dòng
   không còn Go (Claim / tích V / thẻ Completed) → báo xong hôm nay, không làm gì thêm.
2. Bấm Go xong → `after_go(bot)` của nhiệm vụ làm phần việc trong game, rồi báo xong (`mark_task_done`) khi đạt mục tiêu.
3. `record_result` lưu "xong hôm nay" vào `daily_done` trong database; chưa xong thì không lưu, worker thử lại sau.

`daily_done` lưu timestamp; timestamp chỉ còn hiệu lực nếu nằm sau mốc reset server gần nhất. Stop, timeout và thông
báo boss được kiểm tra qua `bot.check()`.

## 4. Flow từng nhiệm vụ

Mỗi nhiệm vụ có file `FLOW.md` riêng trong thư mục của nó:

| Nhiệm vụ | Flow |
| --- | --- |
| Offering | [offering/FLOW.md](offering/FLOW.md) |
| Resource Tax | [resource_tax/FLOW.md](resource_tax/FLOW.md) |
| Gold Levy | [gold_levy/FLOW.md](gold_levy/FLOW.md) |
| Troop Training | [troop_training/FLOW.md](troop_training/FLOW.md) |
| Troop Healing | [troop_healing/FLOW.md](troop_healing/FLOW.md) |
| Trap Building | [trap_building/FLOW.md](trap_building/FLOW.md) |
| Alliance Donation | [alliance_donation/FLOW.md](alliance_donation/FLOW.md) |
| Alliance Help | [alliance_help/FLOW.md](alliance_help/FLOW.md) |
| Black Market | [black_market/FLOW.md](black_market/FLOW.md) |
| General Enhancing | [general_enhancing/FLOW.md](general_enhancing/FLOW.md) |
| Wheel of Fortune | [wheel_of_fortune/FLOW.md](wheel_of_fortune/FLOW.md) |
| Patrol | [patrol/FLOW.md](patrol/FLOW.md) |
| Material Composing | [material_composing/FLOW.md](material_composing/FLOW.md) |
| Research technologies | [alliance_research/FLOW.md](alliance_research/FLOW.md) |

## 5. General: mua thể lực và mua búa

### Buy Stamina

1. Mở Features (`chucnang.png`).
2. Vào Items → War.
3. Tìm Stamina và bấm Buy.
4. Bấm Plus `quantity - 1` lần; số lượng mặc định là 10.
5. Bấm nút mua và chỉ khi flow trả `True` mới đánh dấu đã mua hôm nay.

### Buy All Hammers

1. Mở Features → Items → Special.
2. Tìm offer búa (`bua.png`).
3. Bấm nút Plus `HAMMER_MAX_TAPS` = 10 lần để lên số lượng tối đa (bấm vùng bên trái Plus không đáng tin, chỉ mua được 1 búa).
4. Xác nhận mua.
5. Nếu kiểm tra Special quá năm lần mà không thấy búa, trả `False`.

Mỗi flow General có giới hạn `MAX_STEPS = 100`; quá giới hạn sẽ log và dừng,
không đánh dấu hoàn thành.

## 6. Nhận thưởng Activity

Sau các pass, nếu `Activity Rewards` chưa được ghi hoàn thành:

1. Đóng popup `CongratulationsCurrent.png` bằng Back.
2. Nếu có `Claim_All.png`, bấm Claim All trước để cộng điểm Activity.
3. Tìm mọi `OpenChestCurrent.png` trong riêng hàng rương.
4. Mỗi screenshot chỉ bấm một rương, xử lý popup rồi chụp lại; không dùng lại
   tọa độ cũ vì UI thay đổi sau mỗi lần nhận.
5. Tiếp tục tới khi không còn rương đang mở.
6. Không thấy bảng Activity thì gọi `open_activity_list` (tự nhận giao diện mới "Quests" / cũ "•••"); không bấm icon Quests
   theo ảnh mẫu.
7. Chỉ ghi `Activity Rewards` vào database nếu tất cả task được chọn đã có `daily_done`.

## 7. Ảnh

- Ảnh nằm dưới `Images/DailyActivites/<folder task>/`; `Title.png` là tiêu đề dòng, `Card.png` / `Done.png` là thẻ ở giao diện cũ.
- Các nút có nhiều giao diện giữ nhiều template: `*Current.png` cho client hiện tại và ảnh cũ làm fallback.

## 8. Database và reset ngày

Các khóa hoàn thành được lưu trong trường `daily_done` của thiết bị:

```text
{
  "Offering": "2026-10-03T18:00:00",
  "General: Buy Stamina": "2026-10-03T18:15:00",
  "Activity Rewards": "2026-10-03T18:30:00"
}
```

Code không xóa bản ghi mỗi ngày. `done_today()` so timestamp với mốc reset gần nhất; bản ghi cũ tự động không còn được coi là
hoàn thành.

## 9. Kiểm thử

- [test_daily_activities.py](../../../tests/daily_activities/test_daily_activities.py): khớp UI với nhiệm vụ, nhận rương.
- [test_daily_tasks.py](../../../tests/daily_activities/test_daily_tasks.py): luật `daily_job` / `hourly_job`.
- [test_open_task.py](../../../tests/daily_activities/test_open_task.py): mở nhiệm vụ ở cả 2 giao diện.
- [test_general.py](../../../tests/daily_activities/test_general.py): mua thể lực và búa.

Unit test chỉ xác nhận quyết định của code với màn hình / mocks đã biết. Thay đổi ảnh hay giao diện cần chạy thật trên giả
lập (`tests/real_run.py`) trước khi kết luận flow đã đúng.
