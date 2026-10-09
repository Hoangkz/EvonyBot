# TODO — event 3 ngày

Phạm vi đã chốt: chỉ làm Alliance (donate) và Heal. Produce resources, Stamina, Alliance War
KHÔNG làm (không có ô chọn, bot không bấm Go ở các dòng đó).

- [x] Sau khi xác nhận đổi: băng "Congratulations!" (khớp ảnh Event/congratulations.png 0,999) -> Back để đóng (người dùng xác nhận).
- [x] Nút xám (hết vé hoặc hết lượt, nút giống nhau) -> bỏ qua sang quà kế (người dùng chốt). Hệ quả: vé có thể tiêu vào quà rẻ phía dưới.
- [ ] Toạ độ popup số lượng (bấm cạnh "+", nút xanh) lấy từ ảnh chụp, chưa thử trên máy thật.
- [ ] Bước nhận quà bấm mọi nút Claim (kể cả dòng nhiệm vụ khác do người dùng tự làm); chưa giới hạn chỉ Donate / Heal.
- [x] Flow test: tests/event_center/three_day/test_flow.py (nhận Claim + đổi quà, Go dòng Alliance 60, group tắt, đã xong hôm nay).
- [ ] Flow test chưa có: nhánh Heal, đổi nhiều quà liên tiếp, tab Limited chưa chọn khi vào Event Center (cần chụp thêm).
- [ ] Chạy thử trên máy thật.
- [ ] Đổi quà nhớ vị trí hàng (event.py giữ đúng thứ tự hàng của game; ROW_PITCH / DRAG_* trong constants.py): chưa đo thật xem vuốt 1 px màn = bao nhiêu px danh sách; bot tự dò thêm quanh hàng nếu lệch, nhưng cần đo để dò ít nhất. Không dùng OCR số vé.
- [ ] Donate hết kim cương (mua lại lượt): hiện chỉ đánh dấu xong hôm nay khi không đạt mục tiêu; người dùng sẽ sửa case hết kim cương chung sau.
