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
- Gift Claims chạy cuối Daily Activities nhưng không `must_finish`: nhường Join
  Boss sau tối đa 120 giây rồi tiếp tục theo checkpoint DB.
- Danh sách rỗng, hoặc cả danh sách đều chưa xong: nghỉ 5 giây rồi xét lại tới khi Stop.

## 2. Việc còn lại

- [ ] **Chạy thật thiết kế mới** trên giả lập (`venv\Scripts\poe dev`, máy 21913): log từng nhiệm vụ (`Bắt đầu: <key>` /
  `Xong: <key>`) xen kẽ Join Boss; Crazy Eggs hẹn lại đúng giờ; Black Market chạy 1 lần. Lần chạy thật 2026-10-11 là của
  thiết kế cũ (cả activity một khối).
- [ ] **Chạy `tests/event`** (flow test Event dùng hàm `run` cũ) — chưa chạy lại sau khi sửa.
- [ ] **Ground Troop không đọc được số lượng huấn luyện** (`cannot read train count`, thấy khi chạy thật 2026-10-11):
  nhiệm vụ kết thúc mà không đánh dấu xong. Xem [gather_troops/ground_troop](../activities/event/gather_troops/ground_troop).
- [x] **Quà cuối Daily**: `gift_claims` là tail task priority 299, sau
  `daily_rewards`; mỗi event có key riêng, có ba checkpoint quét rỗng và key
  tổng theo ngày server.

## 3. Daily Activities (để sau, khi người dùng yêu cầu)

- [ ] `daily_general_enhancing` ("Cần làm thêm"): chạy thử thật `after_go`; giao diện mới (tab Cultivate Once / Quick Cultivate)
  cần ảnh nút Gold Cultivate / Cancel; ảnh `Done.png`. Chi tiết: [general_enhancing/TODO.md](../activities/daily_activities/general_enhancing/TODO.md).
- [x] Key daily_done của Daily Activities đã đổi từ nhãn ("Offering") sang `Task.key` (`daily_offering`); không migration (DB
  local, xoá được). Cột `daily_activities` (cấu hình tab) vẫn khoá theo nhãn.

## 4. Khác

- [ ] **Event không còn trong game → bỏ qua cả ngày** (người dùng tự làm sau). Event chỉ kéo dài 7 ngày (VD King's Path:
  ngày 1 làm nhiệm vụ ngày 1 … ngày 7 hết; ngày 8 tìm không thấy). Khi một nhiệm vụ Event vào tìm mà không thấy event đó:
  lưu vào DB (`daily_done`) dấu "event X không có hôm nay" (kèm ngày, VD 08/10/2026) cho **mọi nhiệm vụ của event đó** →
  hôm đó các nhiệm vụ King's Path không chạy nữa (không tìm lại từng nhiệm vụ). Sang ngày mới (qua mốc reset server) dấu
  tự hết hạn như mọi key `daily_done`, lại kiểm tra tiếp; không có thì đánh dấu lại, có thì làm bình thường.
  Liên quan: hàm xoá key của event (kể cả `<nhiệm vụ>_complete`, `event/common.py` `mark_complete`, không tự hết hạn) khi
  event kết thúc, để vòng event mới làm lại.
- [ ] Commit các thay đổi chưa commit: bảng nhiệm vụ (`priority.py`, `tasks.py`, `bot_worker.py`), Crazy Eggs
  trong Daily (ô giờ ở tab, `activated.png`, đủ 4 quả vỡ), giờ reset chọn ở màn Home, test mới / sửa.
- [ ] Crazy Eggs còn việc riêng: [crazy_eggs/TODO.md](../activities/event_center/crazy_eggs/TODO.md) (mục 4 "Tích hợp" đã
  xong — dọn).
