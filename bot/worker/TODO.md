# Worker — việc còn lại

Cập nhật: 2026-10-11. Xong mục nào thì xoá mục đó. Flow hiện tại: [FLOW.md](FLOW.md).

## 1. Thiết kế hiện tại (đã chốt)

- Worker chạy theo **một danh sách nhiệm vụ**. Mọi nhiệm vụ nằm trong bảng [priority.py](priority.py) (`key`, `priority`, `run`, `policy`);
  activity (nút Select Activity, tab cấu hình) chỉ dùng để chia loại.
- Bấm Start: `tasks.build_tasks` lấy mọi nhiệm vụ đã tích, xếp theo độ ưu tiên (số lớn làm trước, < 0 không vào danh sách).
- Mỗi vòng lặp: bỏ nhiệm vụ đã xong hôm nay khỏi danh sách; việc theo giờ (Crazy Eggs, Alliance Donation / Help) làm xong thì
  lưu giờ vào DB, mỗi vòng chỉ so giờ đó, tới giờ thì làm ngay; không thì lấy nhiệm vụ đầu danh sách làm, chưa xong thì chuyển
  xuống cuối.
- Mỗi nhiệm vụ tối đa 6 lần mỗi ngày chạy hết một lượt mà vẫn chưa xong (`MAX_ATTEMPTS`); quá thì bỏ qua tới ngày mới.
- Sang ngày mới (mốc reset server) thì đưa lại mọi nhiệm vụ vào danh sách; Black Market (`once`) đã xong thì không đưa lại.
- Thứ tự ưu tiên: Bubble > Auto Times Out > Join Boss > nhiệm vụ. Có Join Boss: mỗi vòng 1 lượt Join Boss rồi 1 nhiệm vụ
  tối đa 120 giây (`OTHERS_WINDOW`); nhiệm vụ `must_finish` không bị ngắt (chỉ Stop). Không chọn Join Boss thì không có luật
  120 giây; không tích Bubble thì không có luật Bubble.
- Mọi nhiệm vụ Daily Activities đều `must_finish`: làm tới xong, không giới hạn 120 giây, không bị Bubble / Auto Times Out / boss ngắt.
- Danh sách rỗng, hoặc cả danh sách đều chưa xong: nghỉ 5 giây rồi xét lại tới khi Stop.

## 2. Việc còn lại

- [ ] **Chạy thật thiết kế mới** trên giả lập (`venv\Scripts\poe dev`, máy 21913): log từng nhiệm vụ (`Bắt đầu: <key>` /
  `Xong: <key>`) xen kẽ Join Boss; Crazy Eggs hẹn lại đúng giờ; Black Market chạy 1 lần. Lần chạy thật 2026-10-11 là của
  thiết kế cũ (cả activity một khối).
- [ ] **Chạy `tests/event`** (flow test Event dùng hàm `run` cũ) — chưa chạy lại sau khi sửa.
- [ ] **Hàm `run` cũ của Event / Daily** ([event/run.py](../activities/event/run.py),
  [daily_activities/common.py](../activities/daily_activities/common.py)): chỉ còn các flow test cũ gọi, worker không gọi.
  Khi chuyển flow test sang gọi thẳng hàm của từng nhiệm vụ thì xoá (và xoá `ACTIVITIES["Event"]`, `["Daily Activities"]`).
- [ ] **`yield_to_boss` / `YieldToBoss`**: không còn cần cho Event (mỗi nhiệm vụ là một nhiệm vụ riêng, xong là quay lại
  Join Boss). Chỉ `event_center/three_day` còn gọi; bỏ khi tách nhiệm vụ con của event 3 ngày.
- [ ] **Ground Troop không đọc được số lượng huấn luyện** (`cannot read train count`, thấy khi chạy thật 2026-10-11):
  nhiệm vụ kết thúc mà không đánh dấu xong. Xem [gather_troops/ground_troop](../activities/event/gather_troops/ground_troop).
- [ ] **Quà cuối Daily** (`gift_*`, ưu tiên -100): đang chạy bên trong nhiệm vụ `daily_rewards` (một khối dài, bị ngắt ở
  120 giây thì chạy lại từ đầu phần quét). Tách từng quà thành nhiệm vụ riêng nếu cần (nhưng ưu tiên < 0 sẽ bị loại khỏi
  danh sách — phải đổi luật hoặc ưu tiên).

## 3. Daily Activities (để sau, khi người dùng yêu cầu)

- [ ] Viết các nhiệm vụ có trong `priority.py` nhưng chưa có code: `daily_alliance_science`, `daily_alliance_research`,
  `daily_alliance_technology`, `daily_greet_champion` (khi viết thì thêm một dòng vào priority.py (hàm làm việc ở thư mục việc đó); priority.py tự lấy).
- [ ] `daily_general_enhancing`: người dùng ghi "Cần làm thêm".
- [ ] Đổi key daily_done từ nhãn ("Offering") sang dạng `daily_<tên>` + migration trong `database.py` (`KEY_RENAMES`, giống
  Gather Troops) cho `daily_done` và cột `daily_activities`. Hiện `Task.key` (key priority.py) và nhãn (key daily_done)
  tách riêng nên chưa gấp.

## 4. Khác

- [ ] **Dọn dẹp event khi hết hạn**: hàm xoá key của event (kể cả `<nhiệm vụ>_complete` của mọi nhiệm vụ Event —
  `event/common.py` `mark_complete`, không tự hết hạn) trong `daily_done` khi event kết thúc, để vòng mới làm lại.
  Người dùng tự làm sau.
- [ ] Commit các thay đổi chưa commit: bảng nhiệm vụ (`priority.py`, `tasks.py`, `bot_worker.py`), Crazy Eggs
  trong Daily (ô giờ ở tab, `activated.png`, đủ 4 quả vỡ), giờ reset chọn ở màn Home, test mới / sửa.
- [ ] Crazy Eggs còn việc riêng: [crazy_eggs/TODO.md](../activities/event_center/crazy_eggs/TODO.md) (mục 4 "Tích hợp" đã
  xong — dọn).
