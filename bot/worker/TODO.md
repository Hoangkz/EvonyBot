# Worker — việc còn lại

Cập nhật: 2026-10-03 (chốt: thread sống khi không có Join Boss, chu kỳ Crazy Eggs). Xong mục nào thì xoá mục đó.

Mục tiêu: worker chạy theo **nhiệm vụ**, không theo activity nữa. Activity chỉ còn là nhóm trên UI (nút Select Activity,
tab cấu hình). Bộ chọn lấy thẳng nhiệm vụ: ưu tiên cao làm trước, cùng ưu tiên thì xoay vòng. Độ ưu tiên đặt ở
[priority.json](priority.json); số lớn hơn làm trước. Bubble và Join Boss là nhiệm vụ có luật riêng (mục 1).

## 1. Đã chốt (2026-10-03)

- **Bubble và Join Boss cũng là nhiệm vụ** của bộ chọn (có trong `priority.json`), nhưng có luật riêng: Bubble tới hạn khi
  còn <= 2 giờ (hoặc chưa biết) và ngắt được mọi nhiệm vụ; Join Boss chạy giữa mỗi 2 nhiệm vụ thường, rảnh thì nhường,
  có boss mới thì ngắt nhiệm vụ thường. Nhiệm vụ thường: tối đa 120 giây, xong thì quay lại Join Boss.
- **Thứ tự ưu tiên**: Bubble > Join Boss > các nhiệm vụ (theo `priority.json`). Bubble đã như vậy và phải giữ khi viết
  lại worker: lo bubble trước mọi lần chạy (`_with_bubble`, kể cả Join Boss) và `check()` ngắt mọi thứ đang chạy, kể
  cả Join Boss, khi bubble tới hạn (`BubbleDue` xét trước `BossAvailable` / `TimedOut`).
- **Khi không chọn Join Boss**: giữ thread sống, chờ các nhiệm vụ lặp lại (Crazy Eggs theo chu kỳ); sang ngày mới (qua
  mốc reset server) thì làm lại các nhiệm vụ hằng ngày. Không còn kiểu "chạy hết rồi dừng" của `_run_once`.
- **Chu kỳ Crazy Eggs**: ô chọn `0`, `1h`, `2h`, `3h`, `4h`, mặc định `2h`; `0` = không chạy. Lưu DB trước (cấu hình
  theo thiết bị), UI để sau.
- **Mỗi nhiệm vụ tối đa 120 giây khi có Join Boss** (`OTHERS_WINDOW`, thay cho khung 120 giây chung cả nhóm). **Không
  chọn Join Boss thì không có luật 120 giây; không tích Bubble thì không có luật Bubble** (người dùng chốt): boss rảnh
  thì bộ chọn lấy 1 nhiệm vụ, chạy tối đa 120 giây; **xong nhiệm vụ là quay lại Join Boss ngay**, không làm tiếp nhiệm vụ
  khác. Hết 120 giây / có boss mới / bubble tới hạn thì cũng quay lại; nhiệm vụ đang dở làm lại ở lượt sau.
  → `yield_to_boss` / `YieldToBoss` (Event dùng để nhường sau mỗi nhiệm vụ) không cần nữa, bỏ ở bước 3.
  → **Mỗi nhiệm vụ đi kèm một lượt kiểm tra boss** (người dùng chốt): Join Boss rảnh vẫn cuộn danh sách War 6 lần rồi
  mới nhường, nên nhiệm vụ phụ xong chậm hơn hiện tại, đổi lại boss được kiểm tra thường xuyên hơn. Test worker hiện
  tại (khung 120 giây chung, `test_boss_notifications`) sửa theo luật mới ở bước 1.
- **Nhận thưởng Event** (`gather_troops_claim`, `kings_path_claim`): ưu tiên đã thấp hơn mọi nhiệm vụ Event nên tự chạy
  sau; không cần tách riêng phần dùng chung.

## 2. Chuyển worker sang chạy theo nhiệm vụ (làm theo thứ tự, mỗi bước test cũ phải pass)

- [x] **Bước 1 — khung nhiệm vụ và bộ chọn** (2026-10-03): `tasks.py` (đọc `priority.json`, mỗi activity đã chọn trừ
  Join Boss = 1 nhiệm vụ nguyên khối, ưu tiên = cao nhất của nhóm), `scheduler.py` (ưu tiên cao trước, cùng ưu tiên xoay
  vòng, xong thì tới lượt lại sau mốc reset), `BotWorker._run_tasks` thay `_boss_priority` / chạy hết rồi dừng; mỗi vòng
  1 lượt Join Boss + 1 nhiệm vụ tối đa 120 s; `priority.json` thêm vào `installer/build.ps1`. Test: `tests/worker/test_scheduler.py`,
  `tests/worker/test_boss_notifications.py`. Chưa chạy thật trên giả lập.
- [x] **Bước 1b — không có Join Boss vẫn giữ thread sống** (làm cùng bước 1): hết nhiệm vụ tới lượt thì nghỉ 5 s (vẫn lo
  bubble), qua mốc reset thì làm lại; chỉ Stop mới dừng.
- [ ] **Chạy thật bước 1** trên giả lập (`venv\Scripts\poe dev`): có Join Boss + vài activity (log mỗi vòng: Join Boss rồi
  1 activity); không có Join Boss (chạy hết rồi đứng chờ, không Stopped).
- [ ] **Bước 2 — Crazy Eggs**: nhiệm vụ lặp lại theo chu kỳ, ưu tiên 999 (theo `priority.json`). Gọi
  `event_center.crazy_eggs.run`.
  - DB: cấu hình theo thiết bị `{"interval": "2h"}` (`0` / `1h` / `2h` / `3h` / `4h`, mặc định `2h`, `0` = tắt); thời
    điểm chạy xong lần trước để tính lần tới (lưu DB để tắt app mở lại vẫn đúng chu kỳ).
  - Chi tiết nhiệm vụ: [crazy_eggs/TODO.md](../activities/event_center/crazy_eggs/TODO.md).
- [ ] **Bước 3 — tách Event** thành từng nhiệm vụ con (6 Gather Troops, 7 King's Path, 2 bước nhận thưởng
  `gather_troops_claim` / `kings_path_claim` với ưu tiên thấp hơn nên tự chạy sau). Bỏ `yield_to_boss` / `YieldToBoss`
  (xong nhiệm vụ là worker tự quay lại Join Boss).

## 2b. Để sau

- [ ] **UI cho chu kỳ Crazy Eggs**: ô chọn `0` / `1h` / `2h` / `3h` / `4h` (mặc định `2h`) — tab + nút Select Activity.
- [x] **Bước 4 — Black Market**: không còn tách — chế độ Auction House đã xoá (UI + code), chỉ còn
  `black_market_market`.

## 3. Daily Activities (để sau, khi người dùng yêu cầu)

- [ ] Tách thành từng nhiệm vụ con theo `priority.json`.
- [ ] Đổi key trong code sang dạng `daily_<tên>` (VD `"Offering"` → `daily_offering`, `Activity Rewards` →
  `daily_rewards`) + migration trong `database.py` (`KEY_RENAMES`, giống Gather Troops) cho `daily_done` và cột
  `daily_activities` (tab cấu hình lưu `{tên: bật}`).
- [ ] Viết các nhiệm vụ mới có trong `priority.json` nhưng chưa có code: `daily_alliance_science`,
  `daily_alliance_research`, `daily_alliance_technology`, `daily_greet_champion`.
- [ ] `daily_general_enhancing`: người dùng ghi "Cần làm thêm".

## 4. Khác

- [ ] **Dọn dẹp event khi hết hạn**: hàm xoá key của event (kể cả `<nhiệm vụ>_complete` của mọi nhiệm vụ
  Event — `event/common.py` `mark_complete`, không tự hết hạn) trong `daily_done` khi event kết thúc, để vòng mới làm lại.
  Người dùng tự làm sau.

- [x] Đã xoá `bot/common/get_server_time.py`, `bot/ocr/read_server_time.py`, `Images/Server/serverTime.png` (2026-10-03).

- [ ] Commit các thay đổi đang chưa commit: bước 1 (`tasks.py`, `scheduler.py`, `_run_tasks`, `tests/worker/test_scheduler.py`),
  giờ reset chọn ở màn Home (`daily_reset.py`, `ServerClock`, ô "Reset Time", `database.py`), `installer/build.ps1`.
