# Crazy Eggs — việc còn lại

Cập nhật: 2026-10-03. Xong mục nào thì xoá mục đó. Flow hiện tại: [FLOW.md](FLOW.md).

## 1. Chạy thật

- [ ] Chạy thử trên giả lập, lần đầu chạy thật: màn chính → Event Center → Activities → Crazy Eggs → đập 2-3-1-4.
- [ ] Chạy thử nhánh búa vàng: quả 2 đang chờ → bấm quả 2 → Confirm → popup "Congratulations!". Xem log có
  `confirm Lucky Hammer`; ngày hôm sau (qua mốc reset server) bot dùng lại được.
- [ ] Kiểm tra điểm bấm Event Center: chữ "Event Center" + (0, -25) phải trúng icon cúp và mở màn có tab
  Limited / Activities / Competition. Offset này mới đo trên 1 ảnh, mà vị trí nút thì bị đẩy lên xuống theo số nút phía trên.
- [ ] **Animation trứng vỡ**: kiểm tra bấm (50 %, 95 %) có bỏ qua được animation không (log `egg breaking animation, tap
  to skip`, rồi hiện popup "Congratulations on activating the egg!"), và ngưỡng độ sáng 35 có đúng ở mọi khung hình
  của animation không (hiện mới đo 1 khung: 14).

## 2. Ảnh chụp

(Đủ — người dùng chốt 2026-10-02. Test vẫn dùng ảnh tổng hợp `04_eggs_ready.png?cracked_*` và `06_congratulations.png`
chụp ở lần đập khác; không cần thay.)

## 3. Rủi ro đã biết

- [ ] **Dò hụt icon búa** (chờ người dùng chọn cách xử lý): `hammer.png` (7.png, 18x14) khớp 0,95 / 0,91 / 0,88 / 0,84 trên
  quả 1 / 2 / 3 / 4 (nền sau nhãn mỗi quả khác màu), ngưỡng 0,8 → quả 4 chỉ dư 0,04. Hụt thì bot tưởng quả đang chờ, bỏ lỡ
  lượt đập đó (lần chạy sau đập lại). Không hạ ngưỡng được: màn khác (train xe công thành) đã 0,77. Đề xuất: 4 mẫu búa
  cắt từ chính từng quả (`hammer1..4.png`, ngưỡng 0,9); và/hoặc kiểm tra chéo bằng nhãn "Waiting" (vị trí quả không có
  búa lẫn "Waiting" → quét lại 1 lần).
- [ ] **Bấm nhãn "Waiting" của quả 2 để dùng búa vàng** chưa ai thử (bấm búa thì người dùng đã xác nhận đập được). Không ăn
  thì bot coi như hôm đó đã dùng búa vàng — chấp nhận được.

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
