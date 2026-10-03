# King's Path — việc còn lại

Cập nhật: 2026-10-03. Xong mục nào thì xoá mục đó. Kịch bản tổng: [../KINGS_PATH.md](../KINGS_PATH.md).

## 1. Chạy thật

- [ ] Chạy thử cả group King's Path trên giả lập (lần đầu chạy thật).

## 2. Nhiệm vụ chưa làm

(Không còn — mọi nhiệm vụ trong group King's Path đã có code.)

## 3. Đã code nhưng chưa thử trên giả lập

- [ ] **Heal** — thử thật: thanh nhập số (bấm ô số dòng cuối → gõ → OK); Healing Speedup → Finish All;
  sau `AGAIN` đọc lại số đã heal. Hết lính bị thương (menu không có Speed Up / Heal mà có Upgrade, hoặc Hospital 0/0)
  → Back, xong hôm nay.
- [ ] **Black Market** — thử thật: 6 món cố định, bỏ món trả kim cương (nhận theo icon kim cương trên nút giá, 9 mẫu),
  mỗi món mua 1 lần (Confirm) → Instant Refresh (hết miễn phí thì bằng kim cương) → chờ 2 s, so ô vật phẩm 1 với ảnh
  trước khi refresh: khác = đã ra hàng mới, mua tiếp; giống thì chờ thêm 1 s (tối đa 10 lần) rồi bấm Refresh lại.
- [ ] **Refine Equipment** (Day 4, Sharp Weapons) — thử thật: Go → Lò rèn → Craft → tab Refine → món xanh (rồi tím)
  trái nhất; loại đang mở không có thì bấm loại bên trái (nhẫn → giày → quần → giáp → mũ; chờ 1 s, vòng giữa chưa đổi
  thì chờ thêm 1 s, quá 10 lần → Back, không lưu done); tới mũ vẫn không có → lỗi, xong hôm nay → nút Refine → màn
  "Refine Equipment": bỏ tích ô Gold / Orange, Refine → Cancel, đủ (mục tiêu − số đã làm) lần → Back 2 lần → AGAIN.
  Mọi bước chờ 2 s. Còn thiếu:
  - Chưa biết hết nguyên liệu / vàng thì game hiện gì (hiện: tiến độ không tăng sau 1 lượt → xong hôm nay).
  - Sau Cancel + Back 2 lần có về thành không.
  - Hai thiết bị chưa lưu ô `kings_path_refine` trong cấu hình tab Event → đang bị bỏ qua, cần lưu lại tab Event.
- [ ] **Wheel** — thử thật (nhất là nhịp bấm 10 Spins 1 s/lần khi bảng kết quả đang hiện).
- [ ] **City Tax** — thử thật: chọn số lần bằng "−" (tới khi ô số đứng yên 3 lần = 1) rồi "+" (số lần − 1); chờ popup
  đóng bằng nút "+" (10 lần × 1 s, quá thì Back 2 lần → AGAIN, không lưu done); hộp "spend N Gems" → Okay; băng
  "Taxing Gift" (hộp quà) → bấm (50%, 95%); hết lượt miễn phí nhận nút dòng theo hình kim cương. Còn thiếu:
  - Thu xong 4 dòng là `mark_complete` ngay, không đọc lại dòng Go — lần nhấn Tax không ăn (ảnh 1 / 3 "Free: 7" không
    đổi) vẫn bị tính là xong.
  - Flow test `test_city_tax` đã sửa theo "−" / "+" nhưng chưa chạy.
- [ ] **Donate khi không làm Patrol** (ô Patrol = 0) — thử thật: không vào King's Path, đi Liên minh → cuộn → Alliance
  Science (dùng lại ảnh của Alliance Capacity, đã có test bằng ảnh thật; popup ngoài liên minh xử lý như cũ) → donate thẻ đầu tới đủ; số lần đã
  donate hôm nay lưu daily_done `kings_path_donate_alliance_<n>`.
- [ ] **Donate** — thử thật: popup / hiệu ứng sau mỗi lần Donate có che nút không (đang chờ 1 s mỗi lần).
- [ ] **Patrol** — thử thật (người dùng đang test). Hết lượt = nút Refresh xám (đã có ảnh, nhận theo màu).
  "Đã patrol" = >= 6 dấu tích lớn (khối xanh lá >= 20 px); lượt chỉ tính khi màn chuyển sang "đã patrol".
- [ ] **Đi giữa các nhiệm vụ** (King's Path và Gather Troops như nhau): xong một nhiệm vụ ở màn chức năng, nhiệm vụ sau
  bấm Back từng lần (`go_home`) rồi xét lại màn. Kiểm trong log: Back về thẳng event thì làm tiếp ngay; về thành thì
  thấy `... event opened` (mở lại từ Event Center, ~15–30 s mỗi nhiệm vụ — do game, không tránh được).
- [ ] **Nhận thưởng theo chấm đỏ + rương mốc Gather Troops** (event/claim.py) — thử thật cả Gather Troops và King's Path.

## 4. Phạm vi (đã chốt 2026-10-02)

Chỉ làm các nhiệm vụ có trong group King's Path của `ui/tabs/event.json`: City Tax, Patrol, Donate,
Train Troop, Heal, Wheel, Refine Equipment, Black Market. **Không làm** các tab phụ khác: Hoarding, Mining (Day 1);
Unstoppable — đánh boss, Try Your Best (Day 2); God's Blessing — Offer (Day 3, bỏ 2026-10-02);
Accumulation (Day 4). Sharp Weapons (Refine Equipment) thêm 2026-10-03.

City Tax: tiêu kim cương khi hết lượt miễn phí, **không cần mức trần** — chỉ cần tax 4 dòng đủ mục tiêu.
Teamwork: Patrol làm trước Donate; sau Claim All chỉ còn ~3 dòng Go (2 Patrol + Donate) nằm gọn trên màn → không cuộn.
Black Market: hết lượt miễn phí thì Instant Refresh bằng kim cương, **không cần mức trần** (đã chốt 2026-10-02).
King's Path: nhận thưởng chỉ cần Claim All theo chấm đỏ, **không** đọc thanh tiến độ / nhận rương đầu màn.
Mốc rương Gather Troops (5/10/30/50/70) cố định; game đổi mốc thì sửa ở `bot/activities/event/milestones.py`.
Donate: giá mua lại lượt cao nhất 448 kim cương, giảm dần theo thời gian → **không cần mức trần**. Mua tối đa 5 lần
(lần đầu không còn lượt miễn phí: 5 × 13 = 65 ≥ 60); donate đủ (mục tiêu − số đã làm, OCR dòng Go) là dừng.

## 5. Khác

- [ ] Toàn bộ thay đổi King's Path **chưa commit**.
