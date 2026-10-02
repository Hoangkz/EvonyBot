# Crazy Eggs — việc còn lại

Cập nhật: 2026-10-03. Xong mục nào thì xoá mục đó. Flow hiện tại: [FLOW.md](FLOW.md).

## 1. Chạy thật

Chạy bằng `venv\Scripts\poe test` ([tests/real_run.py](../../../../tests/real_run.py), máy 127.0.0.1:21923; `--shots` để lưu ảnh).

- [x] Điều hướng trên máy thật (127.0.0.1:21923, 2026-10-03) bằng hàm của bot: bản đồ → bấm cúp Event Center (chữ ở
  y 309, khác ảnh cũ 241, offset (0, -25) vẫn trúng) → màn "Event Center" (nhận bằng tab Competition) → tab Activities →
  cuộn → icon Crazy Eggs (ngưỡng 0,8) → màn Crazy Eggs. Chưa đập.
- [x] Chạy thật trên 21923 (2026-10-03, 49 s): màn chính → Event Center → Crazy Eggs → đập 2, 3, 1, 4 (mỗi lần BACK đóng
  popup Congratulations) → hết quả có búa → búa vàng: bấm nhãn "Waiting" quả 2 → hộp thoại → Confirm → popup → return.
  Ảnh cuối: 4 quả "Waiting", số búa vàng "0", quả 2 đếm lại từ 3:59:28.
- [ ] Ngày hôm sau (qua mốc reset server) bot dùng lại búa vàng được (cần chạy trong worker để lưu DB).
- [ ] Hết búa thường trên máy thật (hộp thoại "not enough Hammers" → Cancel).
- [ ] **Animation trứng vỡ**: kiểm tra bấm (50 %, 95 %) có bỏ qua được animation không (log `egg breaking animation, tap
  to skip`, rồi hiện popup "Congratulations on activating the egg!"), và ngưỡng độ sáng 35 có đúng ở mọi khung hình
  của animation không (hiện mới đo 1 khung: 14).
- [ ] **Phần thưởng cuối khi vỡ đủ 4 quả**: game tự nhận, màn hiện ra bỏ qua bằng bấm (50 %, 95 %) (người dùng xác nhận).
  Bot chỉ tự bấm nếu màn đó làm tối tiêu đề (độ sáng < 35, như animation); nếu là popup sáng thì bot không nhận ra —
  kiểm tra lúc đập quả cuối và chụp ảnh nếu bot không bỏ qua được.

## 2. Ảnh chụp

(Đủ — người dùng chốt 2026-10-02. Test vẫn dùng ảnh tổng hợp `04_eggs_ready.png?cracked_*` và `06_congratulations.png`
chụp ở lần đập khác; không cần thay.)

## 3. Rủi ro đã biết

- [x] **Icon búa** (giải quyết 2026-10-03): đo 60 khung trên máy thật, vùng búa không có hoạt ảnh, điểm cố định
  0,840..0,950; không có búa <= 0,699 (màn Crazy Eggs) / 0,767 (màn khác) → ngưỡng 0,77, dư ~0,07 mỗi bên. Mới đo trên
  1 máy (396x704); máy khác độ phân giải / DPI thì phải đo lại (đúng cho mọi template). Dự phòng nếu cần biên rộng hơn:
  4 mẫu búa trung vị từng quả, ngưỡng 0,9.

(Đã chốt 2026-10-02: không thấy tab / icon thì thử lại 3 lần + tắt / mở lại game + thử thêm 2 lần rồi mới bỏ hôm nay; màn
tối lạ giữ cách bấm (50 %, 95 %) tối đa 10 lần rồi BACK.)

## 4. Tích hợp (để sau, khi người dùng yêu cầu)

- [ ] Chạy kèm các activity khác: cứ mỗi 2 giờ đưa Crazy Eggs lên đầu danh sách activity phụ; Join Monster War vẫn
  ưu tiên số 1. Một lần chạy kết thúc khi đập hết trứng hoặc hết búa. Phần điều phối nằm ở `BotWorker._boss_priority`.
- [ ] Búa vàng chỉ được lưu vào DB khi chạy trong worker (`mark_daily_done` → cột `daily_done`). Khi nối vào, kiểm tra
  `crazy_eggs_lucky_hammer` có xuất hiện trong DB không.
- [ ] Bị cắt giữa chừng (hết khung 120 s / có boss mới) thì lần gọi lại chạy từ đầu và mất `state` (`before_tap`,
  `lucky_tapped`). Hiện vẫn chạy đúng, nhưng phải đi lại từ màn chính.
- [ ] `settings` chưa dùng: nếu cần tab cấu hình (bật/tắt, bật/tắt búa vàng...) thì thêm khi tích hợp.
