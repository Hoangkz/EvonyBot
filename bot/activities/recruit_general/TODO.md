# TODO: Recruit General

## Chưa kiểm chứng trên máy thật
- [ ] Kéo ảnh tướng sang trái / phải (`SWIPE_LEFT` / `SWIPE_RIGHT`): đúng hướng, một lần kéo = một tướng, không chạm nhầm mở chi tiết tướng.
- [ ] Vòng Refresh 0,3 giây / lần và bấm ô tích theo % cố định (EPIC_BOX / HISTORIC_BOX).
- [ ] Chạy trọn `run` trên giả lập (chưa chạy lần nào), cả nhánh chưa có route (quét) và đã có route (goto).
- [ ] Đo điểm khớp ảnh Tavern (`Images/Building/civ1..7/tavern/1.png`, đã có đủ 7 civ) trên máy thật.

## Chưa làm
- [ ] Popup khác khi Refresh (hết kim cương, hết Refresh...) chưa có ảnh: hiện chỉ dừng khi rời màn / mất nút Refresh.
- [ ] Luồng MUA tướng: `_buy` mới mở màn chi tiết tướng; cần ảnh popup / màn sau khi bấm Recruit General (60.000.000 vàng) để làm tiếp.
- [x] Danh sách tướng cần mua lấy từ UI (settings["generals"]), bot đọc tên bằng OCR rồi so mờ >= 50%.
- [ ] Chưa có ảnh màn Recruit General SAU khi Cancel (tên tướng xịn hiện rõ, không bị mờ): test dùng ảnh tên tổng hợp.
- [ ] Nhánh quét route (chưa có route trong DB) chưa có flow test.
- [ ] Sau khi bấm Recruit General / Buy General Token: có popup xác nhận / màn kết quả giữa chừng không (chưa có ảnh); `_wait_list` chỉ chờ nút Refresh hiện lại.
- [ ] Sau khi mua xong `_buy` trả True và activity dừng; chưa quyết định có Refresh tiếp không.
- [ ] OCR tên tướng (`bot/ocr/read_general_name.py`, mẫu ở `Images/OCR/GeneralName/`): còn thiếu mẫu chữ `x` (VD Alexander Nevsky); chữ `q` mới có một mẫu cắt từ màn Portraits (cỡ nhỏ hơn), chưa kiểm chứng trên tên Q thật ở Tavern (Queen Boudica / Queen Jindeok / Queen Victoria / Huo Qubing). Khi OCR ra `?`, ảnh dải tên tự lưu vào `%LOCALAPPDATA%\EvonyBot\logs\generals\` để thêm mẫu (`python -m bot.ocr.add_sample GeneralName <ảnh> "<chữ|chữ|...>"`).
- [ ] Popup phần thưởng sau khi bấm Use trong popup số lượng (mở vàng): chưa thấy trên máy thật; nhánh Back dự phòng ở cuối `_use_in_popup` chỉ đóng popup số lượng bị kẹt.
