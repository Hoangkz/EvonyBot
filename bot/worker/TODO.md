# Worker — việc còn lại

Cập nhật: 2026-10-11. Xong mục nào thì xoá mục đó. Flow hiện tại: [FLOW.md](FLOW.md).

## 1. Thiết kế hiện tại (đã chốt)

- Worker chạy theo **nhiệm vụ**, không theo activity. Activity (nút Select Activity, tab cấu hình) chỉ dùng để chia loại.
- Bấm Start: `build_tasks` ([tasks.py](tasks.py)) lấy mọi nhiệm vụ trong bảng [registry.py](registry.py) có
  nhóm được chọn và đã được tích (khai báo ở worker: daily/, event/, event_center/, standalone.py; registry.py chỉ gom lại), gắn độ ưu tiên của chính nhiệm vụ ([priority.py](priority.py), số lớn làm trước, < 0
  không vào danh sách). Mỗi nhiệm vụ có hàm `run` riêng; worker gọi thẳng (`BotWorker._run_one`), không qua `run` của
  activity.
- Mỗi lần chọn 1 nhiệm vụ ưu tiên cao nhất (cùng ưu tiên thì xoay vòng). Xong nhiệm vụ thì đánh dấu xong hôm nay, tới mốc
  reset server mới tới lượt lại.
- Ngoại lệ: Black Market chạy 1 lần (`once`, chỉ chạy lại khi Start lại); Crazy Eggs hẹn đập lại mỗi N giờ tới khi đủ 4
  quả vỡ (`repeat`, giữ ưu tiên 999); nhiệm vụ Daily chưa xong hẹn thử lại 300 giây, tối đa 5 lần mỗi ngày; Alliance
  Donation / Help theo giờ (ô 0 / 1h .. 4h) hẹn lại qua `ctx.again_after`.
- Thứ tự ưu tiên: Bubble > Auto Times Out > Join Boss > nhiệm vụ. Có Join Boss: mỗi vòng 1 lượt Join Boss rồi 1 nhiệm vụ
  tối đa 120 giây (`OTHERS_WINDOW`), xong nhiệm vụ là quay lại Join Boss ngay; nhiệm vụ `must_finish` không bị ngắt (chỉ
  Stop). Không chọn Join Boss thì không có luật 120 giây; không tích Bubble thì không có luật Bubble.
- Không còn nhiệm vụ tới lượt: thread vẫn sống, nghỉ 5 giây rồi xét lại tới khi Stop.

## 2. Việc còn lại

- [ ] **Chạy thật thiết kế mới** trên giả lập (`venv\Scripts\poe dev`, máy 21913): log từng nhiệm vụ (`Bắt đầu: <key>` /
  `Xong: <key>`) xen kẽ Join Boss; Crazy Eggs hẹn lại đúng giờ; Black Market chạy 1 lần. Lần chạy thật 2026-10-11 là của
  thiết kế cũ (cả activity một khối).
- [ ] **Chạy `tests/event`** (flow test Event dùng hàm `run` cũ) — chưa chạy lại sau khi sửa.
- [ ] **Hàm `run` cũ của Event / Daily** ([event/run.py](../activities/event/run.py),
  [daily_activities/run.py](../activities/daily_activities/run.py)): chỉ còn các flow test cũ gọi, worker không gọi.
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
  `daily_alliance_technology`, `daily_greet_champion` (khi viết thì thêm vào TASKS ở run.py và key vào priority.py; worker/daily/tasks.py tự lấy).
- [ ] `daily_general_enhancing`: người dùng ghi "Cần làm thêm".
- [ ] Đổi key daily_done từ nhãn ("Offering") sang dạng `daily_<tên>` + migration trong `database.py` (`KEY_RENAMES`, giống
  Gather Troops) cho `daily_done` và cột `daily_activities`. Hiện `Task.key` (key priority.py) và nhãn (key daily_done)
  tách riêng nên chưa gấp.

## 4. Khác

- [ ] **Dọn dẹp event khi hết hạn**: hàm xoá key của event (kể cả `<nhiệm vụ>_complete` của mọi nhiệm vụ Event —
  `event/common.py` `mark_complete`, không tự hết hạn) trong `daily_done` khi event kết thúc, để vòng mới làm lại.
  Người dùng tự làm sau.
- [ ] Commit các thay đổi chưa commit: bảng nhiệm vụ (`registry.py`, `tasks.py`, `scheduler.py`, `bot_worker.py`), Crazy Eggs
  trong Daily (ô giờ ở tab, `activated.png`, đủ 4 quả vỡ), giờ reset chọn ở màn Home, test mới / sửa.
- [ ] Crazy Eggs còn việc riêng: [crazy_eggs/TODO.md](../activities/event_center/crazy_eggs/TODO.md) (mục 4 "Tích hợp" đã
  xong — dọn).
