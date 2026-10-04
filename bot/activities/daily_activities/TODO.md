# Daily Activities — việc còn lại

Flow mở nhiệm vụ / bấm Go / đánh dấu xong: [OPEN_TASK.md](OPEN_TASK.md).

Bố cục giống Event: mỗi nhiệm vụ một thư mục (`constants.py` ảnh + `KEY` trong `bot/worker/priority.json`,
`run.py` handler + `TASK`); test ở `tests/daily_activities/<nhiệm vụ>/` (`test_flow.py` + `screens/`).

## Đã có

- `common.open_task(bot, titles, cards)`: từ màn chính tới lúc bấm **Go**, tự nhận ra phiên bản giao diện
  - **mới**: nút Quests góc dưới trái → tab Activity → danh sách (Claim All bấm trước) → cuộn tìm tiêu đề dòng →
    Go ngay dưới tiêu đề;
  - **cũ**: nút "•••" → bảng chức năng → Activity → lưới thẻ → lướt tìm thẻ → bấm thẻ → popup → Go.
- Sau Go hai phiên bản giống nhau, làm như Event (`event/kings_path/building.py open_building`: nhận ra công
  trình theo ảnh mẫu civ / tự học → menu → icon chức năng). Mới có **Offering** (`offering/run.py after_go`,
  tới màn Offer) và **Resource Tax** (`resource_tax/run.py after_go`: Chợ → Tax → `tax_all`); cả hai đã chạy thật
  bản cũ trên 21943. Resource Tax có `test_flow` phần sau Go (ảnh màn Tax chép từ
  `tests/event/kings_path/screens/`).
- Test: `tests/daily_activities/test_open_task.py` (phần chung), `offering/`, `resource_tax/`,
  `resource_collecting/`, `troop_training/` (bản mới), `troop_healing/` (bản cũ).

## TODO — phần mở nhiệm vụ / bấm Go (common.open_task, OPEN_TASK.md)

Logic đã xong; còn thiếu **ảnh** (thêm ảnh là dùng được, không phải sửa logic) và kiểm tra trên máy thật.

1. **Ảnh tích V** (bản mới) của dòng đã nhận thưởng → `UseAllActivities/Tick.png` (`TICK_BUTTON`). Chưa có: chỉ nút
   Claim được tính là xong; dòng có tích V → `TASK_UNKNOWN` (bỏ qua, lần sau lại thử).
2. ~~**Ảnh tiêu đề dòng**~~ (bản mới): đã cắt `<thư mục ảnh>/Title.png` từ danh sách thật cho 14 nhiệm vụ
   (`task_titles` ưu tiên ảnh này; dòng đúng 1,00, dòng khác <= 0,78, Go cách tâm tiêu đề 43 px). Resource
   Collecting vẫn dùng `ClaimCollecting.png` (0,98). Dòng "Gather ... from outside the City" chưa gán nhiệm vụ nào.
3. **Ảnh thẻ** (bản cũ, `<thư mục ảnh>/Card.png`): đã có đủ 15 nhiệm vụ (cắt từ máy 21943, ảnh lưới
   `tests/daily_activities/screens/16..19_old_grid_*.png`; thẻ khớp 1,00, thẻ khác <= 0,51). Kiểm tra trên tài khoản
   khác (13_old_activity_grid): Gathering 0,97, Troop Healing 0,97, General Enhancing 0,97, Material Composing 0,96,
   **Trap Building 0,88** (sát ngưỡng 0,85 — có thể cần thêm mẫu). Đã bấm thẻ xác nhận: găng tay = Resource
   Collecting ("Collect resources from inside the City"), bình hoá chất = Research (không phải nhiệm vụ của bot).
4. **Thẻ đã 100% (bản cũ)**: icon thành hộp quà, bot nhận ra bằng chữ "100%" (`OLD_DONE_BADGE`) → bấm nhận, **chỉ
   khi chưa cuộn** (thẻ chưa nhận nằm đầu lưới; đã cuộn mà thấy "100%" là đã nhận). ~~Ảnh lưới sau khi nhận~~: đã
   có — thẻ xuống cuối lưới, icon cũ + tích xanh "Completed"; mỗi nhiệm vụ `<thư mục ảnh>/Done.png` → `TASK_DONE`.
   Đã có Done.png: Resource Collecting, Offering, Resource Tax (21943). **Còn thiếu Done.png 12 nhiệm vụ khác**
   (người dùng chụp sau khi làm xong các nhiệm vụ); flow test dùng ảnh `22..25_old_grid_*.png`.
5. **Claim All xám** (không có gì để nhận) khớp ảnh mẫu 0,86, sát ngưỡng 0,9 → nên cắt ảnh Claim All sáng chặt hơn
   hoặc kiểm tra màu, tránh bấm nhầm nút xám.
6. **Thử thật trên máy**: cuộn trượt (`LIST_SWIPE`, `LIST_END_SAME`), tốc độ hiện popup, Back khi thử lại có về đúng
   màn chính không (bản mới: Back đóng popup Quests; bản cũ: Back từ lưới).

## TODO — phần khác

7. **Nối luồng mới vào `run.py`**: hiện `run()` vẫn chạy luồng cũ port từ C# (`common.run_task`). Với nhiệm vụ đã có
   `after_go`: `common.open_task_or_finish` → `after_go`. Sau đó bỏ phần luồng C# không còn dùng (`run_task`,
   `task_targets`, `open_daily_activity` ...) và cập nhật `FLOW.md`.
8. **Ảnh sau Go từng nhiệm vụ** (người dùng gửi): menu công trình → màn chức năng → làm → xong, cho cả 15 nhiệm vụ;
    mỗi nhiệm vụ `after_go` + `test_flow.py`.
9. **Offering**: thử thật khi hôm nay đã offer vài lượt; test bản cũ khi có ảnh thẻ Offer. Offer Gems = 0 → worker
    bỏ qua nhiệm vụ (người dùng sửa ở worker). Thiếu kim cương: xem mục 12.
10. **Nhận thưởng cuối** (rương 20/50/80/110/145) cho cả hai phiên bản: `common.collect_activity_rewards` đang là
    bản C#, cần ảnh để kiểm tra.
11. **`daily_done` theo `KEY`** (giống Event) thay vì theo nhãn — cần đổi cả tab UI và chuyển dữ liệu cũ.

## TODO — làm sau (thiếu điều kiện)

12. **Thiếu kim cương / thiếu tài nguyên / thiếu tăng tốc**: để sau làm. Hiện các nhiệm vụ chưa xử lý trường hợp này
    (VD Offering không đủ kim cương, Troop Training / Trap Building / Troop Healing thiếu tài nguyên hoặc không còn
    tăng tốc, Black Market không đủ tiền). Khi làm: cần ảnh popup báo thiếu của từng loại → đóng popup, bỏ qua nhiệm
    vụ, **không** đánh dấu xong, ghi log.
