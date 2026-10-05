# Alliance Help — việc còn lại

Flow: [FLOW.md](FLOW.md). Việc chung của Daily Activities: [../TODO.md](../TODO.md).

1. ~~Ảnh `Done.png`~~: đã cắt (thẻ (283, 395) trên `tests/daily_activities/screens/32_old_grid_end_help_completed.png`,
   máy 21943): 1,00; thẻ Alliance Help chưa xong <= 0,65; thẻ Completed nhiệm vụ khác <= 0,60 (ngưỡng 0,85).
2. ~~Ảnh `Title.png`~~ (giao diện mới): không đi chụp (người dùng: không bao giờ bấm Go của nhiệm vụ này). Hệ quả: giao
   diện mới bước kiểm tra luôn `unknown` (không tìm được dòng, kể cả dòng đã tích V) → không đánh dấu xong, cứ mỗi
   N giờ lại vào Help All (không hại).
3. Ảnh màn ngay sau khi bấm Help All (có popup gì không) — hiện chỉ Back.
4. ~~`test_flow.py`~~: đã có (`tests/daily_activities/alliance_help/test_flow.py`: Help All → Completed → xong;
   "No records" → dừng, không lưu gì; Help All nhưng thẻ còn Go). Đã chạy thật trên 21913 (Help All + "No records").
