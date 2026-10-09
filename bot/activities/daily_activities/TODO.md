# Daily Activities — việc còn lại

Flow mở nhiệm vụ / bấm Go / đánh dấu xong: [OPEN_TASK.md](OPEN_TASK.md).

Bố cục giống Event: mỗi nhiệm vụ một thư mục (`constants.py` ảnh + `KEY` trong `bot/worker/priority.py`,
`run.py` handler + `TASK`); test ở `tests/daily_activities/<nhiệm vụ>/` (`test_flow.py` + `screens/`).

## Đã có

- `common.open_task(bot, titles, cards)`: từ màn chính tới lúc bấm **Go**, tự nhận ra phiên bản giao diện
  - **mới**: nút Quests góc dưới trái → tab Activity → danh sách (Claim All bấm trước) → cuộn tìm tiêu đề dòng →
    Go ngay dưới tiêu đề;
  - **cũ**: nút "•••" → bảng chức năng → Activity → lưới thẻ → lướt tìm thẻ → bấm thẻ → popup → Go.
- Sau Go hai phiên bản giống nhau, làm như Event (`event/kings_path/building.py open_building`: nhận ra công
  trình theo ảnh mẫu civ / tự học → menu → icon chức năng). Mới có **Offering** (`offering/run.py after_go`,
  tới màn Offer), **Resource Tax** (`resource_tax/run.py after_go`: Chợ → Tax → `tax_all`) và **Gold Levy** (`gold_levy/run.py
  after_go`: Thành chính → Levy → Free Levy All); cả ba đã chạy thật
  bản cũ trên 21943. Gold Levy chưa có `test_flow` (ảnh có sẵn ở
  `tests/daily_activities/gold_levy/screens/`). Resource Tax có `test_flow` phần sau Go (ảnh màn Tax chép từ
  `tests/event/kings_path/screens/`).
- Test: `tests/daily_activities/test_open_task.py` (phần chung), `offering/`, `resource_tax/`,
  `resource_collecting/`, `troop_training/` (bản mới), `troop_healing/` (bản cũ).

## TODO — phần mở nhiệm vụ / bấm Go (common.open_task, OPEN_TASK.md)

Logic đã xong; còn thiếu **ảnh** (thêm ảnh là dùng được, không phải sửa logic) và kiểm tra trên máy thật.

1. ~~**Ảnh tích V**~~ (bản mới): đã cắt `UseAllActivities/Tick.png` từ danh sách Activity máy 21913 (dòng Tax / Levy đã
   xong; tích V ở Chapter Quests 0,96 nhưng chỉ tìm ngay dưới tiêu đề dòng). Tích nằm dưới tâm tiêu đề `TICK_DY` = 33 px
   (Go / Claim 42 px). Dòng có tích V → `TASK_DONE`.
2. ~~**Ảnh tiêu đề dòng**~~ (bản mới): đã cắt `<thư mục ảnh>/Title.png` từ danh sách thật cho 14 nhiệm vụ
   (`task_titles` ưu tiên ảnh này; dòng đúng 1,00, dòng khác <= 0,78, Go cách tâm tiêu đề 43 px). Resource
   Collecting vẫn dùng `ClaimCollecting.png` (0,98). Dòng "Gather ... from outside the City" chưa gán nhiệm vụ nào.
3. **Ảnh thẻ** (bản cũ, `<thư mục ảnh>/Card.png`): đã có đủ 15 nhiệm vụ (cắt từ máy 21943, ảnh lưới
   `tests/daily_activities/screens/16..19_old_grid_*.png`; thẻ khớp 1,00, thẻ khác <= 0,51). Kiểm tra trên tài khoản
   khác (13_old_activity_grid): Gathering 0,97, Troop Healing 0,97, General Enhancing 0,97, Material Composing 0,96,
   Trap Building 0,88 (việc còn lại: [trap_building/TODO.md](trap_building/TODO.md)). Đã bấm thẻ xác nhận: găng tay = Resource
   Collecting ("Collect resources from inside the City"), bình hoá chất = Research (không phải nhiệm vụ của bot).
4. **Thẻ đã 100% (bản cũ)**: icon thành hộp quà, bot nhận ra bằng chữ "100%" (`OLD_DONE_BADGE`) → bấm nhận, **chỉ
   khi chưa cuộn** (thẻ chưa nhận nằm đầu lưới; đã cuộn mà thấy "100%" là đã nhận). ~~Ảnh lưới sau khi nhận~~: đã
   có — thẻ xuống cuối lưới, icon cũ + tích xanh "Completed"; mỗi nhiệm vụ `<thư mục ảnh>/Done.png` → `TASK_DONE`.
   Đã có Done.png: Resource Collecting, Offering, Resource Tax, Gold Levy, Troop Training, Troop Healing, Trap Building, Alliance Help, Alliance Donation, Black Market (21943). Nhiệm vụ còn thiếu Done.png
   ghi trong TODO.md của nhiệm vụ đó; flow test dùng ảnh `22..30_old_grid_*.png` (26: popup Congratulations sau khi nhận → Back).
5. ~~**Claim All xám**~~: `_active_claim_all` xét thêm độ bão hoà màu trong khung nút (sáng ~205, xám ~14, ngưỡng
   `CLAIM_ALL_MIN_SATURATION` = 100) → nút xám không bấm. Test: `black_market/test_flow`
   (`screens/05_activity_claim_all_gray.png`, 21913).
6. **Thử thật trên máy**: cuộn trượt (`LIST_SWIPE`, `LIST_END_SAME`), tốc độ hiện popup, Back khi thử lại có về đúng
   màn chính không (bản mới: Back đóng popup Quests; bản cũ: Back từ lưới).

## TODO — phần khác

7. **Nối luồng mới vào `run.py`**: hiện `run()` vẫn chạy luồng cũ port từ C# (`common.run_task`). Với nhiệm vụ đã có
   `after_go`: `common.open_task_or_finish` → `after_go`. Sau đó bỏ phần luồng C# không còn dùng (`run_task`,
   `task_targets`, `open_daily_activity` ...) và cập nhật `FLOW.md`.
8. **Ảnh sau Go / `after_go` / `test_flow.py`** của từng nhiệm vụ: ghi trong TODO.md của nhiệm vụ (bảng cuối file).
9. **Nhận thưởng cuối** (rương 20/50/80/110/145) cho cả hai phiên bản: `common.collect_activity_rewards` đang là
    bản C#, cần ảnh để kiểm tra.
10. **`daily_done` theo `KEY`** (giống Event) thay vì theo nhãn — cần đổi cả tab UI và chuyển dữ liệu cũ.

## TODO — làm sau (thiếu điều kiện)

11. **Thiếu kim cương / thiếu tài nguyên / thiếu tăng tốc** (quy tắc chung): cần ảnh popup báo thiếu của từng loại →
    đóng popup, bỏ qua nhiệm vụ, **không** đánh dấu xong, ghi log. Nhiệm vụ nào bị ảnh hưởng ghi trong TODO.md của nó.

## TODO từng nhiệm vụ

Việc riêng của nhiệm vụ nào ghi trong `<thư mục nhiệm vụ>/TODO.md`; file này chỉ giữ việc chung.

| Nhiệm vụ | TODO | Số việc |
| --- | --- | --- |
| Monster Killing | [monster_killing/TODO.md](monster_killing/TODO.md) | 3 |
| Resource Collecting | [resource_collecting/TODO.md](resource_collecting/TODO.md) | 1 |
| Offering | [offering/TODO.md](offering/TODO.md) | 3 |
| Resource Gathering | [resource_gathering/TODO.md](resource_gathering/TODO.md) | 2 |
| Resource Tax | [resource_tax/TODO.md](resource_tax/TODO.md) | 3 |
| Gold Levy | [gold_levy/TODO.md](gold_levy/TODO.md) | 4 |
| Troop Training | [troop_training/TODO.md](troop_training/TODO.md) | 3 |
| Troop Healing | [troop_healing/TODO.md](troop_healing/TODO.md) | 3 |
| Trap Building | [trap_building/TODO.md](trap_building/TODO.md) | 5 |
| Alliance Donation | [alliance_donation/TODO.md](alliance_donation/TODO.md) | 3 |
| Black Market | [black_market/TODO.md](black_market/TODO.md) | 4 |
| General Enhancing | [general_enhancing/TODO.md](general_enhancing/TODO.md) | 3 |
| Wheel of Fortune | [wheel_of_fortune/TODO.md](wheel_of_fortune/TODO.md) | 3 |
| Patrol | [patrol/TODO.md](patrol/TODO.md) | 3 |
| Material Composing | [material_composing/TODO.md](material_composing/TODO.md) | 3 |
