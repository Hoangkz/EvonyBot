# Find Boss — TODO (cần thử thực tế trên giả lập)

Code đã viết xong nhưng CHƯA chạy thật. Người dùng sẽ test rồi báo lại; mỗi mục dưới đây là một giả định / số ước lượng cần xác nhận.

## Cần kiểm chứng
- [ ] **Nút ra thế giới**: `TO_WORLD_TAP = (92, 93)` % ([constants.py](constants.py)) chỉ là ước lượng. Chụp màn thành (nút góc dưới phải), cắt template để thay cho bấm theo %.
- [ ] **Icon listboss** trên bản đồ thế giới: đã xác nhận có hiện; cần xem log đọc số boss có đúng không (`_watch_boss_count`).
- [ ] **Kiểm tra mỗi cú kéo** (`arc_sweep.WATCH_EVERY = 1`): đo thời gian thêm mỗi cú (ước 0,3–0,6 s). Nếu chậm: cho watcher dùng lại ảnh `_swipe` đã chụp, hoặc nâng lên 2–3.
- [ ] **Sau Join Boss**: camera có còn ở ô dở không (Back về thế giới); nếu hay lệch thì nhánh "về thành rồi kéo lại" chạy nhiều, cân nhắc hàm nhập toạ độ.
- [ ] **Chờ nhanh 0,3 s** (`boss_scan.POLL`): menu Share / Attack, hộp Confirm, đọc toạ độ camera có bị đọc sớm / sai không.
- [ ] **Kéo boss ra giữa rồi đọc lại** thay cho Attack: boss một phần kéo ra giữa có đọc đủ tên không; còn bao nhiêu lần phải rơi về `check_boss`.
- [ ] **Nhiều boss ở mép**: danh sách chờ theo toạ độ thế giới (`waiting`, `screen_of`) có kéo tới đủ boss không; `VISIBLE = (10, 70, 386, 620)`, `MAX_REVISIT_TRIES = 3`.
- [ ] **Kéo bù camera sau mỗi ô có boss** (`restore_camera`): `RESTORE_KM = 3`, `RESTORE_TRIES = 3`; xem log "camera lệch ô quét". Đọc X:Y hỏng (vùng X thấp?) thì dùng toạ độ dự tính (`camera_guess`).
- [ ] **Ngưỡng gộp boss** = `SAME_BOSS_KM` (4 km) theo cả tên / tầng: hai boss sát nhau có bị gộp nhầm không.
- [ ] **Nhường nhiệm vụ khác** (`YieldToTask`): việc theo giờ / City VIP 0h ngắt quét rồi quét lại từ đầu có ổn không; mỗi 5 giây xét một lần (`IDLE_RECHECK`).
- [ ] **Quét cả vòng 300 km** mất bao lâu; có cần `must_finish` / bỏ giới hạn nào khác không.

## Chưa làm
- [ ] Flow test theo chuỗi ảnh chụp thật (thành → thế giới → thấy boss → share). Hiện chỉ có test bot giả ([tests/find_boss/](../../../tests/find_boss/)).
- [ ] Hàm nhập toạ độ (nhảy thẳng tới ô đang dở / `resync` của arc_sweep) — cần ảnh màn hình nhập toạ độ.
- [ ] Watcher dùng lại ảnh chụp sẵn của `_swipe` để giảm chi phí kiểm tra mỗi cú kéo.
