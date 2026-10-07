# Event 3 ngày (Event Center > Limited)

Ví dụ: "Precious Vegetation". Cấu hình ở tab Event, group "3-Day Event": ô tích ở tiêu đề group
(active), Alliance (0/10/30/60, mặc định 60), Heal (0/5000/10000/30000, mặc định 30000), danh sách
quà ưu tiên (Up/Down hoặc kéo thả). Chạy cuối activity Event ([../../event/run.py](../../event/run.py)).

1. Màn chính -> Event Center -> tab Limited -> cuộn tìm icon (mọi ảnh trong `Images/EventCenter/ThreeDay/Icons/`;
   event mới = thả thêm ảnh icon vào đó).
2. Tab nhiệm vụ (vừa vào là ở đầu danh sách): cuộn xuống tìm chữ chung "Donate to the Alliance" / "Heal" của các
   nhiệm vụ bật. LUÔN kiểm cả 2 nhiệm vụ, không dựa vào dấu "đã xong" (daily_done) tự lưu (donate xong tự đánh
   dấu nhưng vào danh sách vẫn kiểm). Nhiệm vụ chỉ được coi là xong khi thấy một trong 3 trường hợp:
   1. có Go và OCR lại số đã làm >= mục tiêu (3 mốc dùng chung bộ đếm);
   2. thấy đủ 3 dòng đều Claimed;
   3. thấy đủ 3 dòng đều Claim (bấm nhận từng dòng -> thành Claimed).
   Gặp Claim thì bấm nhận quà. Có Go mà chưa đủ -> Go, donate / heal, quét lại từ đầu và OCR lại (tối đa 3 lần
   Go mỗi nhiệm vụ, quá thì ghi không đạt, xong hôm nay). Không kết luận được nhiệm vụ nào -> Back rồi làm lại, 3
   lần, vẫn không -> ghi lỗi, đánh dấu xong hôm nay, sang đổi quà.
3. Xong cả 2 nhiệm vụ (quà đã nhận ngay lúc quét): sang tab Redeem luôn, không cuộn lại danh sách nhiệm vụ, rồi đổi quà theo thứ tự ưu tiên (nút xám thì bỏ qua; 5 quà xám liên tiếp thì dừng).
4. Xong hết -> daily_done `three_day_done` (đã xong hôm nay, tới lần reset server). Hết event (không thấy
   icon / tab) cũng lưu để không tìm lại cả ngày.
