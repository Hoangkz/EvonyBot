# King's Path — việc còn lại

Cập nhật: 2026-10-02. Xong mục nào thì xoá mục đó. Kịch bản tổng: [../KINGS_PATH.md](../KINGS_PATH.md).

## 1. Chạy thật

- [ ] Chạy thử cả group King's Path trên giả lập (lần đầu chạy thật).

## 2. Nhiệm vụ chưa có phần sau Go

Hiện các nhiệm vụ này bấm Go rồi dừng, **không bao giờ đánh dấu xong**, nên mỗi lượt bot lại vào King's Path và bấm Go
(mất thời gian trong 120 s dành cho activity phụ). Cần ảnh màn mở ra sau khi bấm Go và các bước tiếp theo.

- [ ] **Heal** (Day 3, Healing Heart): ảnh sau Go + cách heal (cần có lính bị thương).

Heal sau Go giống City Tax / Patrol (chờ 10 s → bấm giữa màn hình → icon trong menu công trình → màn chức năng).
**Yêu cầu: lưu được tiến độ** — đọc số đã làm ở dòng Go (OCR) mỗi lượt trước khi bấm Go, chỉ làm phần còn thiếu
(mục tiêu − đã làm); bị ngắt (120 s / boss) thì lượt sau đọc lại số mới từ game rồi làm tiếp; đủ mục tiêu → xong.
Cần ảnh cho mỗi nhiệm vụ: thành sau Go, menu sau khi bấm giữa (có icon), màn sau khi bấm icon, popup sau khi thực hiện.
- [ ] **Black Market** (Day 5): chưa có code. Cần ảnh Day 5 khi đã mở (tab Day 5, các tab phụ, dòng nhiệm vụ, màn sau Go).
- [ ] Ảnh tab **Day 5** (chưa chọn / đang chọn): hiện chỉ có Day 1–4 nên nhiệm vụ Day 5 không bấm được tab.
- [ ] Quyết định: trong lúc chờ ảnh, có nên **bỏ qua** các nhiệm vụ chưa có phần sau Go (thay vì bấm Go rồi dừng) không?

## 3. Đã code nhưng chưa thử trên giả lập

- [ ] **Wheel** — thử thật (nhất là nhịp bấm 10 Spins 1 s/lần khi bảng kết quả đang hiện).
- [ ] **City Tax** — gõ số vào popup Tax (bấm ô số → xoá 5 lần → `input text` → Enter): kiểm tra ô số đổi đúng
  (VD mỗi dòng 23 khi đã làm 20 / 110).
- [ ] **Train Troop** — doanh trại mở ở cấp cao (không thấy cấp I): bot bấm vòng trái nhất để lùi dần, **chưa có ảnh test**.
  Chụp màn Train đang ở cấp cao (VD XIII) với tài khoản có nhiều cấp mở.
- [ ] **Patrol / Donate** — cuộn danh sách tìm dòng (tối đa 3 lần) chưa thử với dòng nằm dưới màn.
- [ ] **Donate** — thử thật: popup / hiệu ứng sau mỗi lần Donate có che nút không (đang chờ 1 s mỗi lần).
- [ ] **Patrol** — thử thật (người dùng đang test). Hết lượt = nút Refresh xám (đã có ảnh, nhận theo màu).
  "Đã patrol" = >= 6 dấu tích lớn (khối xanh lá >= 20 px); lượt chỉ tính khi màn chuyển sang "đã patrol".
- [ ] **Đi giữa các nhiệm vụ** (King's Path và Gather Troops như nhau): xong một nhiệm vụ ở màn chức năng, nhiệm vụ sau
  bấm Back từng lần (`go_home`) rồi xét lại màn. Kiểm trong log: Back về thẳng event thì làm tiếp ngay; về thành thì
  thấy `... event opened` (mở lại từ Event Center, ~15–30 s mỗi nhiệm vụ — do game, không tránh được).
- [ ] **Nhận thưởng theo chấm đỏ + rương mốc Gather Troops** (event/claim.py) — thử thật cả Gather Troops và King's Path.

## 4. Rủi ro logic cần xem lại

- [ ] **OCR tiến độ**: dòng Go trên cùng bị hàng tab phụ che chữ "a / b" (nút Go ở y < ~318) → đọc ra None →
  City Tax / Donate không làm gì lượt đó. (Số lớn xuống 2 dòng ở Train Troop đã đọc được.)

## 5. Cấu hình `ui/tabs/event.json` (group King's Path)

- [ ] Train Troop: dãy `..., 50000, 10000, 200000` — có lẽ `10000` gõ nhầm của `100000`.
- [ ] Train Troop, Heal, Wheel, Black Market **không có giá trị 0** → không tắt được nhiệm vụ.
- [ ] `kings_path_black_market` có trong tab nhưng chưa có nhiệm vụ → bị bỏ qua im lặng.

## 6. Phạm vi (đã chốt 2026-10-02)

Chỉ làm các nhiệm vụ có trong group King's Path của `ui/tabs/event.json`: City Tax, Patrol, Donate,
Train Troop, Heal, Wheel, Black Market. **Không làm** các tab phụ khác: Hoarding, Mining (Day 1);
Unstoppable — đánh boss, Try Your Best (Day 2); God's Blessing — Offer (Day 3, bỏ 2026-10-02);
Accumulation, Sharp Weapons (Day 4).

City Tax: tiêu kim cương khi hết lượt miễn phí, **không cần mức trần** — chỉ cần tax 4 dòng đủ mục tiêu.
King's Path: nhận thưởng chỉ cần Claim All theo chấm đỏ, **không** đọc thanh tiến độ / nhận rương đầu màn.
Mốc rương Gather Troops (5/10/30/50/70) cố định; game đổi mốc thì sửa ở `bot/activities/event/milestones.py`.
Donate: giá mua lại lượt cao nhất 448 kim cương, giảm dần theo thời gian → **không cần mức trần**. Mua tối đa 5 lần
(lần đầu không còn lượt miễn phí: 5 × 13 = 65 ≥ 60); donate đủ (mục tiêu − số đã làm, OCR dòng Go) là dừng.

## 7. Khác

- [ ] Toàn bộ thay đổi King's Path **chưa commit**.
