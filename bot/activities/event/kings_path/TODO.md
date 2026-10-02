# King's Path — việc còn lại

Cập nhật: 2026-10-02. Tích `[x]` khi xong. Kịch bản tổng: [../KINGS_PATH.md](../KINGS_PATH.md).

## 1. Chặn chạy thật (làm trước)

- [x] **Ảnh icon King's Path trong danh sách event** → `Images/Event/KingsPath/icon.png` (2026-10-02).
- [x] Test đi từ màn chính → Event Center → danh sách event → King's Path (`test_open_from_main`).
- [ ] Chạy thử cả group King's Path trên giả lập (lần đầu chạy thật).

## 2. Nhiệm vụ chưa có phần sau Go

Hiện các nhiệm vụ này bấm Go rồi dừng, **không bao giờ đánh dấu xong**, nên mỗi lượt bot lại vào King's Path và bấm Go
(mất thời gian trong 120 s dành cho activity phụ). Cần ảnh màn mở ra sau khi bấm Go và các bước tiếp theo.

- [ ] **Patrol** (Day 2, Teamwork): ảnh sau Go + cách patrol.
- [ ] **Offer** (Day 3, God's Blessing): ảnh sau Go + cách offer.
- [ ] **Heal** (Day 3, Healing Heart): ảnh sau Go + cách heal (cần có lính bị thương).
- [ ] **Black Market** (Day 5): chưa có code. Cần ảnh Day 5 khi đã mở (tab Day 5, các tab phụ, dòng nhiệm vụ, màn sau Go).
- [ ] Ảnh tab **Day 5** (chưa chọn / đang chọn): hiện chỉ có Day 1–4 nên nhiệm vụ Day 5 không bấm được tab.
- [ ] Quyết định: trong lúc chờ ảnh, có nên **bỏ qua** các nhiệm vụ chưa có phần sau Go (thay vì bấm Go rồi dừng) không?

## 3. Đã code nhưng chưa thử trên giả lập

- [x] **Wheel** — có 100 Spins: bấm → Back → xong. Chỉ có 10 Spins: bấm liên tục tới khi game mở Purchase Chips → Back → xong hôm nay (2026-10-02).
- [ ] **Wheel** — thử thật trên giả lập (nhất là nhịp bấm 10 Spins 1 s/lần khi bảng kết quả đang hiện).
- [ ] **City Tax** — gõ số vào popup Tax (bấm ô số → xoá 5 lần → `input text` → Enter): kiểm tra ô số đổi đúng 28 / 27.
- [ ] **City Tax** — "tap giữ màn hình" đang hiểu là **bấm 1 lần** giữa màn hình; nếu là nhấn giữ thì sửa.
- [ ] **City Tax** — test dùng ảnh ghép (màn Day 1 trong ảnh toàn dòng Claim). Chụp màn City Tax còn dòng Go để thay.
- [ ] **Train Troop** — test dùng ảnh ghép dòng Go (tab Strong Troops trong ảnh toàn dòng Claim). Chụp màn còn dòng Go.
- [ ] **Train Troop** — doanh trại mở ở cấp cao (không thấy cấp I): bot bấm vòng trái nhất để lùi dần, **chưa có ảnh test**.
  Chụp màn Train đang ở cấp cao (VD XIII) với tài khoản có nhiều cấp mở.
- [ ] **Patrol / Donate** — cuộn danh sách tìm dòng (tối đa 3 lần) chưa thử với dòng nằm dưới màn.
- [ ] **Donate** — thử thật: popup / hiệu ứng sau mỗi lần Donate có che nút không (đang chờ 1 s mỗi lần).

## 4. Rủi ro logic cần xem lại

- [ ] **OCR tiến độ hỏng ở 2 trường hợp:**
  - dòng Go trên cùng bị hàng tab phụ che chữ "a / b" (nút Go ở y < ~318) → đọc ra None;
  - số lớn bị xuống 2 dòng (VD "10,000 / 10,000" ở Strong Troops, Healing Heart) → đọc ra None.

  Hậu quả: City Tax / Donate **không làm gì và lặp lại mỗi lượt** (vì không dám tiêu kim cương khi không biết số);
  Train Troop train **đủ cả mục tiêu** (có thể dư). Cần chụp dòng có số 2 dòng để sửa vùng cắt OCR.
- [ ] **"Không còn Go → xong"**: với nhiệm vụ không tìm dòng theo tiêu đề (City Tax, Train, Offer, Heal, Wheel),
  không thấy nút Go trên màn là coi như xong. Đúng nếu sau Claim All các dòng đã nhận dồn xuống dưới — **chưa xác nhận**.
  Nếu dòng Go nằm dưới màn hình thì bot đánh dấu xong nhầm.
- [x] **Donate** — mua lại lượt tối đa **4 lần** / lượt chạy (13 miễn phí + 4 × 13 = 65 ≥ 60).
- [ ] **Donate** — không kiểm tra giá kim cương mỗi lần mua (lần đầu 448, có thể tăng). Có cần mức trần không?
- [ ] **City Tax** — vượt lượt miễn phí thì tiêu kim cương, không có mức trần.
- [ ] Mỗi nhiệm vụ King's Path tự mở lại event từ màn chính (Event Center → danh sách → icon) → chậm khi bật nhiều nhiệm vụ.

## 5. Cấu hình `ui/tabs/event.json` (group King's Path)

- [ ] Train Troop: dãy `..., 50000, 10000, 200000` — có lẽ `10000` gõ nhầm của `100000`.
- [ ] Train Troop, Offer, Heal, Wheel, Black Market **không có giá trị 0** → không tắt được nhiệm vụ.
- [ ] `kings_path_black_market` có trong tab nhưng chưa có nhiệm vụ → bị bỏ qua im lặng.

## 6. Ngoài phạm vi hiện tại (ghi lại để quyết định sau)

- [ ] Các tab phụ chưa làm: Hoarding, Mining (Day 1); Unstoppable — đánh boss, Try Your Best (Day 2);
  Accumulation, Sharp Weapons (Day 4).
- [ ] Rương mốc tiến độ ở đầu màn (Progress x / 99): chưa nhận tự động (Claim All chỉ nhận dòng nhiệm vụ?).
- [ ] Toàn bộ thay đổi King's Path **chưa commit**.
